"""Minimal PE32+ reader/writer helpers for the Finals.id companion exe."""
import struct

IMAGE_BASE_DEFAULT = 0x140000000


class PE:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = bytearray(f.read())
        d = self.data
        self.e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[self.e_lfanew:self.e_lfanew + 4] == b"PE\0\0"
        self.file_header_off = self.e_lfanew + 4
        (self.machine, self.nsec, self.timestamp, self.symptr, self.nsym,
         self.optsize, self.chars) = struct.unpack_from("<HHIIIHH", d, self.file_header_off)
        self.opt_off = self.file_header_off + 20
        assert struct.unpack_from("<H", d, self.opt_off)[0] == 0x20B
        self.image_base = struct.unpack_from("<Q", d, self.opt_off + 24)[0]
        self.section_align = struct.unpack_from("<I", d, self.opt_off + 32)[0]
        self.file_align = struct.unpack_from("<I", d, self.opt_off + 36)[0]
        self.size_image = struct.unpack_from("<I", d, self.opt_off + 56)[0]
        self.size_headers = struct.unpack_from("<I", d, self.opt_off + 60)[0]
        self.checksum_off = self.opt_off + 64
        self.checksum = struct.unpack_from("<I", d, self.checksum_off)[0]
        self.ndirs = struct.unpack_from("<I", d, self.opt_off + 108)[0]
        self.dirs = []
        for i in range(min(self.ndirs, 16)):
            rva, size = struct.unpack_from("<II", d, self.opt_off + 112 + i * 8)
            self.dirs.append((rva, size))
        self.sections = []
        off = self.opt_off + self.optsize
        for i in range(self.nsec):
            name = d[off:off + 8].rstrip(b"\0").decode("ascii", "replace")
            vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", d, off + 8)
            ch = struct.unpack_from("<I", d, off + 36)[0]
            self.sections.append(dict(i=i, header_off=off, name=name, vsize=vsize,
                                      vaddr=vaddr, rsize=rsize, raddr=raddr, ch=ch))
            off += 40
        self.section_headers_end = off

    # --- address translation ---
    def rva2off(self, rva):
        for s in self.sections:
            span = max(s["vsize"], s["rsize"])
            if s["vaddr"] <= rva < s["vaddr"] + span:
                return s["raddr"] + (rva - s["vaddr"])
        return None

    def va2off(self, va):
        return self.rva2off(va - self.image_base)

    def off2va(self, off):
        for s in self.sections:
            if s["raddr"] <= off < s["raddr"] + s["rsize"]:
                return self.image_base + s["vaddr"] + (off - s["raddr"])
        return None

    def read_va(self, va, n):
        off = self.va2off(va)
        if off is None:
            return None
        return bytes(self.data[off:off + n])

    # --- assets table ---
    def find_asset_table(self, min_run=50):
        """Scan .rdata for the (key_ptr,key_len,val_ptr,val_len) struct array."""
        candidates = []
        for s in self.sections:
            if s["name"] not in (".rdata", ".data"):
                continue
            start, end = s["raddr"], s["raddr"] + s["rsize"]
            off = start
            while off + 32 <= end:
                kp, kl, vp, vl = struct.unpack_from("<QQQQ", self.data, off)
                if 2 < kl < 300 and 0 < vl < 0x8000000:
                    ko = self.va2off(kp)
                    vo = self.va2off(vp)
                    if ko is not None and vo is not None and ko + kl <= len(self.data):
                        key = bytes(self.data[ko:ko + kl])
                        if key[:1] == b"/" and all(32 <= c < 127 for c in key):
                            candidates.append((off, key, kl, vp, vl))
                off += 8
        # keep the longest run of entries spaced exactly 32 bytes apart
        best, run = [], []
        for c in candidates:
            if run and c[0] == run[-1][0] + 32:
                run.append(c)
            else:
                run = [c]
            if len(run) > len(best):
                best = list(run)
        return best if len(best) >= min_run else None

    def reloc_entries(self):
        rva, size = self.dirs[5]
        off = self.rva2off(rva)
        out = []
        pos = off
        end = off + size
        while pos + 8 <= end:
            page, bsize = struct.unpack_from("<II", self.data, pos)
            if page == 0 or bsize < 8:
                break
            n = (bsize - 8) // 2
            for i in range(n):
                w = struct.unpack_from("<H", self.data, pos + 8 + i * 2)[0]
                out.append((page + (w & 0xFFF), w >> 12))
            pos += bsize
        return out

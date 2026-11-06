"""Finals.id Companion App 汉化补丁工具（静态 PE 补丁）。

用法:
  python patch.py build   [--exe PATH] [--out PATH] [--dict PATH]
  python patch.py install [--exe PATH] [--dict PATH]      # 备份 .bak 后直接替换
  python patch.py restore [--exe PATH]
  python patch.py verify  [--exe PATH]

原理: 取出现代浏览器前端主 bundle(assets/index-*.js, Brotli 压缩)，
末尾追加中文化运行时(字典 + MutationObserver)，重新 Brotli 压缩后
写入 PE 新段 .zhtr，并把资源表中该条目的 val_ptr/val_len 指向新段。
资源表条目原本就带 DIR64 重定位，指针值会被加载器自动重定位。
"""
import argparse
import json
import os
import re
import struct
import sys
import time

import brotli

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fzpe import PE

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_EXE = r"E:\Finals.id Companion App\finals-companion.exe"
DEFAULT_DICT = os.path.join(ROOT, "translations.json")
RUNTIME_JS = os.path.join(HERE, "runtime.js")
MARKER = "__FINALS_ZH_RT__"
TOKEN = "__FINALS_ZH_DICT__"
JS_KEY = "/assets/index-D-vp0nj_.js"
SECTION_NAME = b".zhtr"


def align(v, a):
    return (v + a - 1) // a * a


def load_dict(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        items = json.load(f)
    out = {}
    for it in items:
        en = it.get("en") or ""
        zh = it.get("zh") or ""
        if not en or not zh:
            continue
        if en not in out:
            out[en] = zh
    return out


def build_runtime(dic):
    src = open(RUNTIME_JS, "r", encoding="utf-8").read()
    js = json.dumps(dic, ensure_ascii=False, indent=0)
    js = js.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    if TOKEN not in src:
        raise SystemExit("runtime.js 缺少占位符 " + TOKEN)
    return src.replace(TOKEN, js)


def find_js_entry(pe, table):
    # 1) 老版本固定文件名
    for e in table:
        if e[1].decode("utf-8", "replace") == JS_KEY:
            return e
    # 2) 从 /index.html 里读 <script src="...js">，自动适配更新后的哈希文件名
    for off, key, kl, vp, vl in table:
        if key == b"/index.html":
            try:
                html = brotli.decompress(pe.read_va(vp, vl)).decode("utf-8", "replace")
            except Exception:
                break
            m = re.search(r'src="([^"]+\.js)"', html)
            if m:
                target = m.group(1).encode("utf-8")
                for e in table:
                    if e[1] == target:
                        print("  按 index.html 自动识别前端 bundle: %s" % m.group(1))
                        return e
            break
    # 3) 兜底：取最大的 .js
    cands = [e for e in table if e[1].endswith(b".js")]
    cands.sort(key=lambda e: e[4], reverse=True)
    if cands:
        print("  警告: 未找到明确的 index bundle，改用最大的 js: %s" % cands[0][1].decode())
        return cands[0]
    raise SystemExit("找不到主 JS bundle，现有 js: %r" % [c[1] for c in table if c[1].endswith(b".js")])


def pe_checksum(data, checksum_off):
    d = bytearray(data)
    d[checksum_off:checksum_off + 4] = b"\0\0\0\0"
    total = 0
    n = len(d)
    if n % 2:
        total += d[-1]
        n -= 1
    for i in range(0, n, 2):
        total += d[i] | (d[i + 1] << 8)
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (total + len(data)) & 0xFFFFFFFF


def build(orig_exe, out_exe, dict_path, quality=11):
    t_start = time.time()
    pe = PE(orig_exe)
    print("原始文件: %s (%d 字节)" % (orig_exe, len(pe.data)))
    print("ImageBase %#x  SectionAlign %#x  FileAlign %#x  SizeOfImage %#x"
          % (pe.image_base, pe.section_align, pe.file_align, pe.size_image))

    table = pe.find_asset_table()
    if not table:
        raise SystemExit("资源表解析失败")
    print("资源表: %d 条, 起始文件偏移 %#x" % (len(table), table[0][0]))

    off, key, klen, vptr, vlen = find_js_entry(pe, table)
    key_s = key.decode()
    print("目标资源: %s  val_ptr=%#x  val_len=%d" % (key_s, vptr, vlen))

    orig_js = brotli.decompress(pe.read_va(vptr, vlen))
    print("解压原始 bundle: %d 字节, sha1=%s"
          % (len(orig_js), __import__("hashlib").sha1(orig_js).hexdigest()[:12]))

    dic = load_dict(dict_path)
    runtime = build_runtime(dic)
    print("字典: %d 条, 运行时 %d 字节" % (len(dic), len(runtime.encode('utf-8'))))

    new_js = orig_js + b"\n;\n" + runtime.encode("utf-8")
    t0 = time.time()
    js_payload = brotli.compress(new_js, quality=quality, lgwin=22, mode=brotli.MODE_TEXT)
    print("压缩: %d -> %d 字节 (%.1fs)" % (len(new_js), len(js_payload), time.time() - t0))
    if len(js_payload) > 0x8000000:
        raise SystemExit("压缩结果过大")

    blobs = [(off, js_payload)]

    htm_entry = None
    for e in table:
        if e[1].decode("utf-8", "replace") == "/index.html":
            htm_entry = e
            break
    if htm_entry is not None:
        hoff, hkey, hklen, hvptr, hvlen = htm_entry
        orig_html = brotli.decompress(pe.read_va(hvptr, hvlen))
        new_html = re.sub(rb"<title>.*?</title>",
                          "<title>Finals.id 伙伴应用</title>".encode("utf-8"),
                          orig_html, count=1, flags=re.S)
        new_html = new_html.replace(b'<html lang="en"', b'<html lang="zh-CN"')
        if new_html != orig_html:
            hp = brotli.compress(new_html, quality=quality, lgwin=22, mode=brotli.MODE_TEXT)
            blobs.append((hoff, hp))
            print("index.html 标题替换 -> %d 字节" % len(hp))

    blob = b""
    placements = []
    for (ent_off, payload) in blobs:
        placements.append((ent_off, len(blob), payload))
        blob += payload

    sec_align, file_align = pe.section_align, pe.file_align
    new_va = align(pe.size_image, sec_align)
    raw_off = align(len(pe.data), file_align)
    vsize = len(blob)
    rsize = align(vsize, file_align)

    data = bytearray(pe.data)
    if raw_off > len(data):
        data += b"\0" * (raw_off - len(data))
    data += blob
    data += b"\0" * (rsize - vsize)

    hdr_off = pe.section_headers_end
    if hdr_off + 40 > pe.size_headers:
        raise SystemExit("PE 头部没有空间放新段头")
    sec_hdr = struct.pack("<8sIIIIIIHHI", SECTION_NAME, vsize, new_va,
                          rsize, raw_off, 0, 0, 0, 0, 0x40000040)
    data[hdr_off:hdr_off + 40] = sec_hdr

    struct.pack_into("<H", data, pe.file_header_off + 2, pe.nsec + 1)
    struct.pack_into("<I", data, pe.opt_off + 56, align(new_va + vsize, sec_align))
    struct.pack_into("<I", data, pe.opt_off + 8,
                     struct.unpack_from("<I", data, pe.opt_off + 8)[0] + rsize)

    for (ent_off, blob_off, payload) in placements:
        struct.pack_into("<Q", data, ent_off + 16, pe.image_base + new_va + blob_off)
        struct.pack_into("<Q", data, ent_off + 24, len(payload))

    struct.pack_into("<I", data, pe.checksum_off,
                     pe_checksum(data, pe.checksum_off))

    with open(out_exe, "wb") as f:
        f.write(data)
    print("已写入: %s (%d 字节, 新段 .zhtr VA=%#x, 总耗时 %.1fs)"
          % (out_exe, len(data), new_va, time.time() - t_start))
    return out_exe


def verify(exe):
    pe = PE(exe)
    table = pe.find_asset_table()
    print("段数:", len(pe.sections), " SizeOfImage:", hex(pe.size_image))
    for s in pe.sections:
        print("  %-8s VA %#010x vsize %#x raw %#010x rsize %#x"
              % (s["name"], s["vaddr"], s["vsize"], s["raddr"], s["rsize"]))
    off, key, klen, vptr, vlen = find_js_entry(pe, table)
    print("资源:", key.decode(), "val_ptr=%#x val_len=%d" % (vptr, vlen))
    js = brotli.decompress(pe.read_va(vptr, vlen))
    print("解压成功:", len(js), "字节, 含汉化运行时:", MARKER.encode() in js)
    # 段边界检查
    for s in pe.sections:
        assert s["raddr"] + s["rsize"] <= len(pe.data), "段 %s 越过文件尾" % s["name"]
    print("校验通过")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "install", "restore", "verify"])
    ap.add_argument("--exe", default=DEFAULT_EXE)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dict", default=DEFAULT_DICT)
    ap.add_argument("--quality", type=int, default=11)
    a = ap.parse_args()

    exe = os.path.abspath(a.exe)
    if not os.path.exists(exe):
        raise SystemExit("exe 不存在: " + exe)

    if a.cmd == "build":
        out = a.out or os.path.join(os.path.dirname(exe), "finals-companion.zh.exe")
        build(exe, out, a.dict, a.quality)
        verify(out)
    elif a.cmd == "install":
        tmp = exe + ".zh.tmp"
        build(exe, tmp, a.dict, a.quality)
        verify(tmp)
        bak = exe + ".bak"
        if not os.path.exists(bak):
            os.replace(exe, bak)
            print("原文件已备份:", bak)
        else:
            print("备份已存在，保留:", bak)
        os.replace(tmp, exe)
        print("安装完成:", exe)
    elif a.cmd == "restore":
        bak = exe + ".bak"
        if not os.path.exists(bak):
            raise SystemExit("没有备份文件: " + bak)
        os.replace(bak, exe)
        print("已从备份恢复:", exe)
    elif a.cmd == "verify":
        verify(exe)


if __name__ == "__main__":
    main()

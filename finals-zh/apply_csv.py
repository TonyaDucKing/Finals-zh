"""把 translations.csv 里改过的「中文翻译」写回 translations.json，并重建 translations.html。"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV = HERE / "translations.csv"
JSONP = HERE / "translations.json"
HTML = HERE / "translations.html"


def write_html(rows, header):
    idx_id = header.index("序号")
    idx_en = header.index("English")
    idx_zh = header.index("中文翻译")
    idx_ctx = header.index("上下文（代码片段）") if "上下文（代码片段）" in header else -1
    idx_note = header.index("备注") if "备注" in header else -1
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    trs = []
    for r in rows:
        ctx = r[idx_ctx] if idx_ctx >= 0 else ""
        note = r[idx_note] if idx_note >= 0 else ""
        trs.append(
            "<tr><td class=id>%s</td><td class=en>%s</td><td class=zh>%s</td><td class=ctx>%s</td><td class=note>%s</td></tr>"
            % (esc(r[idx_id]), esc(r[idx_en]), esc(r[idx_zh]), esc(ctx[:70]), esc(note))
        )
    html = """<!doctype html><meta charset=utf-8><title>Finals.id 中文词表</title>
<style>
body{background:#0e1311;color:#dfe7e3;font:14px/1.5 "Segoe UI",system-ui,sans-serif;margin:0}
header{position:sticky;top:0;background:#101715;padding:14px 20px;border-bottom:1px solid #23302b;z-index:9}
h1{font-size:17px;margin:0 0 8px}
input{width:min(520px,90vw);padding:7px 10px;border-radius:6px;border:1px solid #2c3b35;background:#0b100e;color:inherit}
#count{color:#7f938b;margin-left:10px}
table{border-collapse:collapse;width:100%}
td{border-bottom:1px solid #1b2522;padding:6px 10px;vertical-align:top}
th{position:sticky;top:62px;background:#101715;text-align:left;padding:6px 10px;color:#8aa198}
.id{color:#5d7069;width:52px;text-align:right}
.en{color:#9fb3ab;width:34%}
.zh{width:30%}
.ctx{color:#5f736b;font-family:Consolas,monospace;font-size:12px}
.note{color:#4e8f74;width:80px}
tr.hide{display:none}
</style>
<header><h1>Finals.id 伙伴应用 · 中文词表</h1>
<input id=q placeholder="搜索英文或中文…"><span id=count></span></header>
<table id=t><thead><tr><th>#</th><th>English</th><th>中文</th><th>上下文</th><th>备注</th></tr></thead><tbody>
""" + "\n".join(trs) + """
</tbody></table>
<script>
var q=document.getElementById('q'),rows=[].slice.call(document.querySelectorAll('#t tbody tr')),c=document.getElementById('count');
function f(){var v=q.value.toLowerCase();var n=0;rows.forEach(function(r){var hit=!v||r.textContent.toLowerCase().indexOf(v)>=0;r.className=hit?'':'hide';if(hit)n++});c.textContent=n+' / '+rows.length}
q.addEventListener('input',f);f();
</script>"""
    HTML.write_text(html, encoding="utf-8")


def main():
    if not CSV.exists():
        raise SystemExit("找不到 translations.csv")
    with open(CSV, encoding="utf-8-sig", newline="") as fh:
        rd = list(csv.reader(fh))
    header, data = rd[0], rd[1:]
    i_id = header.index("序号")
    i_zh = header.index("中文翻译")

    trs = json.loads(JSONP.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in trs}
    changed = 0
    for row in data:
        if not row or not row[i_id].strip():
            continue
        try:
            rid = int(row[i_id])
        except ValueError:
            continue
        zh = row[i_zh]
        r = by_id.get(rid)
        if r is not None and zh and r["zh"] != zh:
            r["zh"] = zh
            changed += 1

    JSONP.write_text(json.dumps(trs, ensure_ascii=False, indent=1), encoding="utf-8")
    write_html(data, header)
    print("已写回译文:", changed, "处；词库共", len(trs), "条")


if __name__ == "__main__":
    main()

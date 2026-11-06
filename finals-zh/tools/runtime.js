/* Finals.id Companion App 中文化运行时（由 patch.py 注入到主 bundle 末尾） */
(function () {
  "use strict";
  if (window.__FINALS_ZH_RT__) return;
  window.__FINALS_ZH_RT__ = 1;

  var RAW = __FINALS_ZH_DICT__;
  var MAP = Object.create(null);
  var CMP = Object.create(null);
  var RE_WS = /[\s\u00a0]+/g;
  var RE_HAN = /[\u3400-\u9fff\uf900-\ufaff]/;
  var RE_CMP = /^[A-Za-z0-9%\/+\-.,:!?()&]+$/;
  var MAXLEN = 2000;

  function norm(s) {
    return s.replace(RE_WS, " ").trim();
  }

  for (var k in RAW) {
    var nk = norm(k);
    if (!nk) continue;
    if (MAP[nk] === undefined) MAP[nk] = RAW[k];
    var ck = nk.replace(/\s+/g, "");
    if (ck !== nk && ck.length >= 2 && ck.length <= 40 && RE_CMP.test(ck) && CMP[ck] === undefined) {
      CMP[ck] = RAW[k];
    }
  }

  var PREFIX = [
    ["Open now until ", "现已开放至 "],
    ["Now until ", "现在至 "],
    ["Now until", "现在至 "],
    ["Yesterday ", "昨天 "],
    ["Today ", "今天 "],
    ["Tomorrow ", "明天 "]
  ];
  // 主题编辑器里的 Light 是「明亮」主题，与职业 Light（轻型）同词不同义
  var THEME_MAP = { Light: "明亮", Dark: "深色", Emerald: "翡翠", Amethyst: "紫水晶", Graphite: "石墨" };
  var THEME_SEL = ".theme-modal,[class*='preset-swatch']";
  var RE_ORDINAL = /^(\d+)(st|nd|rd|th)$/;
  var MONTHS = { jan: "1月", feb: "2月", mar: "3月", apr: "4月", may: "5月", jun: "6月", jul: "7月", aug: "8月", sep: "9月", oct: "10月", nov: "11月", dec: "12月" };
  var PATTERNS = [
    [/^unknown \(one of (\d+) maps?\)\.?$/i, function (m) { return "未知（" + m[1] + " 张地图之一）"; }],
    [/^likely (.+?) \((\d+)%\)\.?$/i, function (m) { return "可能是 " + m[1] + "（" + m[2] + "%）"; }],
    [/^possible maps: (.+)$/i, function (m) { return "可能地图：" + m[1]; }],
    [/^club tag (.+)$/i, function (m) { return "俱乐部标签 " + m[1]; }],
    [/^(.+?) left\.$/i, function (m) { return "剩余 " + m[1] + "。"; }],
    [/^(\d+)h (\d+)m$/, function (m) { return m[1] + " 小时 " + m[2] + " 分"; }],
    [/^(\d+)d (\d+)h$/, function (m) { return m[1] + " 天 " + m[2] + " 小时"; }],
    [/^([A-Za-z]{3,9}) (\d{1,2})$/, function (m) {
      var mk = MONTHS[m[1].toLowerCase().slice(0, 3)];
      return mk ? mk + m[2] + "日" : m[0];
    }]
  ];

  var CI = Object.create(null);
  var CICNT = Object.create(null);
  for (var k2 in RAW) {
    var nk2 = norm(k2);
    if (!nk2) continue;
    var lk2 = nk2.toLowerCase();
    CICNT[lk2] = (CICNT[lk2] || 0) + 1;
    if (CI[lk2] === undefined) CI[lk2] = RAW[k2];
  }

  function basic(n) {
    var zh = MAP[n];
    if (zh !== undefined) return zh;
    for (var p = 0; p < PREFIX.length; p++) {
      var pe = PREFIX[p][0];
      if (n.length > pe.length && n.indexOf(pe) === 0) return PREFIX[p][1] + n.slice(pe.length);
    }
    var mo = RE_ORDINAL.exec(n);
    if (mo) return "第 " + mo[1];
    if (n.length <= 40) {
      var c = n.replace(/\s+/g, "");
      if (c !== n && RE_CMP.test(c)) {
        zh = CMP[c];
        if (zh !== undefined) return zh;
      }
    }
    if (n.length <= 80) {
      var lk = n.toLowerCase();
      if (CICNT[lk] === 1 && CI[lk] !== undefined && CI[lk] !== n) return CI[lk];
    }
    for (var q = 0; q < PATTERNS.length; q++) {
      if (n.indexOf(". ") >= 0) break;
      var mm = PATTERNS[q][0].exec(n);
      if (mm) return PATTERNS[q][1](mm);
    }
    return undefined;
  }

  function seg(n) {
    if (n.length < 24 || n.indexOf(". ") < 0) return undefined;
    var parts = [];
    var i0 = 0;
    while (i0 < n.length) {
      var j = n.indexOf(". ", i0);
      if (j < 0) { parts.push(n.slice(i0)); break; }
      parts.push(n.slice(i0, j + 1));
      i0 = j + 2;
    }
    var any = false;
    var out = "";
    for (var k3 = 0; k3 < parts.length; k3++) {
      var raw = parts[k3].trim();
      if (!raw) continue;
      var z = basic(raw);
      if (z !== undefined && z !== raw) { out += z; any = true; }
      else out += raw;
    }
    return any ? out : undefined;
  }

  function lookup(s) {
    if (!s || s.length > MAXLEN) return null;
    var n = norm(s);
    if (!n || RE_HAN.test(n)) return null;
    var zh = basic(n);
    if (zh === undefined) zh = seg(n);
    if (zh === undefined || zh === n) return null;
    return zh;
  }

  function trText(node) {
    var t = node.nodeValue;
    if (!t) return;
    if (node.parentElement && guarded(node.parentElement)) return;
    var zh;
    if (node.parentElement && inTheme(node.parentElement)) {
      var tn = norm(t);
      if (THEME_MAP[tn]) zh = THEME_MAP[tn];
    }
    if (zh == null) zh = lookup(t);
    if (zh == null) return;
    var m = /^(\s*)([\s\S]*?)(\s*)$/.exec(t);
    node.nodeValue = (m[1] || "") + zh + (m[3] || "");
  }

  var ATTRS = ["placeholder", "title", "aria-label", "data-tip", "data-label", "alt"];
  var GUARD_SEL = "[class*='player-name'],[class*='club-name'],[class*='club-tag'],[class*='roster-member'],[class*='fo-avatar'],[class*='self-name'],[class*='weapon-name'],[class*='wtab-name'],[class*='kit-name']";

  function guarded(el) {
    try {
      return !!(el && el.closest && el.closest(GUARD_SEL));
    } catch (e) {
      return false;
    }
  }

  function inTheme(el) {
    try {
      return !!(el && el.closest && el.closest(THEME_SEL));
    } catch (e) {
      return false;
    }
  }

  function trAttrs(el) {
    if (!el.getAttribute) return;
    if (guarded(el)) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i];
      var v = el.getAttribute(a);
      if (!v) continue;
      var zh = lookup(v);
      if (zh != null) el.setAttribute(a, zh);
    }
    var tag = el.tagName;
    if (tag === "INPUT") {
      var t = el.getAttribute("type");
      if (t && t !== "button" && t !== "submit" && t !== "reset") return;
    } else if (tag !== "BUTTON" && tag !== "OPTION") {
      return;
    }
    var val = el.getAttribute("value");
    if (val) {
      var zv = lookup(val);
      if (zv != null) el.setAttribute("value", zv);
    }
  }

  function walk(root) {
    if (!root) return;
    var type = root.nodeType;
    if (type === 3) { trText(root); return; }
    if (type !== 1 && type !== 9 && type !== 11) return;
    if (type === 1) trAttrs(root);
    var tw = document.createTreeWalker(root, 1 | 4, null);
    var n;
    while ((n = tw.nextNode())) {
      if (n.nodeType === 3) trText(n);
      else trAttrs(n);
    }
  }

  var mo = new MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      var m = muts[i];
      if (m.type === "characterData") {
        trText(m.target);
      } else if (m.type === "childList") {
        for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
      } else if (m.type === "attributes") {
        trAttrs(m.target);
      }
    }
  });

  function start() {
    walk(document.documentElement);
    mo.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRS.concat(["value"])
    });
    var delays = [300, 1000, 2500, 5000, 9000];
    for (var i = 0; i < delays.length; i++) {
      (function (ms) {
        setTimeout(function () { walk(document.documentElement); }, ms);
      })(delays[i]);
    }
  }

  if (document.documentElement) {
    start();
  } else {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  }
})();

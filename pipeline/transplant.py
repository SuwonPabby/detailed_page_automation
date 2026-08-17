#!/usr/bin/env python3
"""transplant.py — 템플릿 파일의 변형(variant) 서브트리를 REST로 읽어
작업 파일에서 재구축할 수 있는 압축 스펙(JSON)으로 컴파일한다.

Figma API는 파일 간 노드 복사가 불가하므로, 스펙 → use_figma 빌더 JS로 재구축한다.
- 위치는 절대좌표(부모 상대)로 보존. auto-layout은 재현하지 않는다(1:1 재구축이 목적).
- IMAGE fill은 브랜드 그라디언트 placeholder로 치환 (해시는 파일 경계를 못 넘음)
- VECTOR/POLYGON 등은 bbox+첫 SOLID fill 사각형으로 근사 (name 앞에 vec~)
- 색상 리맵: --remap 'old=new,...' hex 매핑

사용:
  python3 pipeline/transplant.py <variantNodeId> [--remap '#FF0000=#123D26,...'] [--texts]
출력: /tmp/claude-501/spec-<id>.json (+ --texts면 텍스트 목록 stdout)
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

# 템플릿 파일은 사람 관할 config에서 — 하드코딩 금지 (config/templates.json)
import json as _json
TPL_KEY = _json.load(open(Path(__file__).resolve().parent.parent / "config" / "templates.json"))["file_key"]
ENV = Path.home() / "projects/detailed_page_automation/.env"


def token():
    for line in ENV.read_text().splitlines():
        m = re.match(r"\s*FIGMA_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
        if m:
            return m.group(1)
    sys.exit("no token")


def hexc(c):
    return "#%02X%02X%02X" % (round(c["r"] * 255), round(c["g"] * 255), round(c["b"] * 255))


def compress(node, origin, remap):
    bb = node.get("absoluteBoundingBox") or {}
    t = node.get("type")
    out = {
        "t": t, "n": node.get("name", "")[:20],
        "x": round(bb.get("x", 0) - origin[0], 1), "y": round(bb.get("y", 0) - origin[1], 1),
        "w": round(bb.get("width", 0), 1), "h": round(bb.get("height", 0), 1),
    }
    if node.get("opacity", 1) != 1:
        out["o"] = round(node["opacity"], 3)
    if node.get("visible") is False:
        return None
    # fills
    fills = []
    for f in node.get("fills") or []:
        if f.get("visible") is False:
            continue
        if f["type"] == "SOLID":
            h = hexc(f["color"])
            fills.append({"s": remap.get(h, h), "o": round(f.get("opacity", 1), 3)})
        elif f["type"].startswith("GRADIENT"):
            stops = [{"p": round(s["position"], 3),
                      "c": remap.get(hexc(s["color"]), hexc(s["color"])),
                      "a": round(s["color"].get("a", 1), 3)} for s in f.get("gradientStops", [])]
            fills.append({"g": stops})
        elif f["type"] == "IMAGE":
            fills.append({"img": 1})
    if fills:
        out["f"] = fills
    # strokes
    for s in node.get("strokes") or []:
        if s.get("type") == "SOLID" and s.get("visible", True):
            h = hexc(s["color"])
            out["st"] = {"c": remap.get(h, h), "w": node.get("strokeWeight", 1)}
            break
    if node.get("cornerRadius"):
        out["r"] = node["cornerRadius"]
    if node.get("rectangleCornerRadii"):
        out["rr"] = node["rectangleCornerRadii"]
    if t == "TEXT":
        st = node.get("style", {})
        out["ch"] = node.get("characters", "")
        out["fs"] = st.get("fontSize", 16)
        out["fw"] = st.get("fontWeight", 400)
        out["ta"] = st.get("textAlignHorizontal", "LEFT")
        if st.get("lineHeightPx"):
            out["lh"] = round(st["lineHeightPx"], 1)
        if st.get("letterSpacing"):
            out["ls"] = round(st["letterSpacing"], 2)
    # 자식 (TEXT는 자식 무시)
    if t != "TEXT":
        kids = []
        for c in node.get("children") or []:
            k = compress(c, origin, remap)
            if k:
                kids.append(k)
        if kids:
            out["k"] = kids
    return out


def main():
    nid = sys.argv[1]
    remap = {}
    if "--remap" in sys.argv:
        for pair in sys.argv[sys.argv.index("--remap") + 1].split(","):
            a, b = pair.split("=")
            remap[a.upper()] = b.upper()
    req = urllib.request.Request(
        f"https://api.figma.com/v1/files/{TPL_KEY}/nodes?ids={nid}",
        headers={"X-Figma-Token": token()})
    d = json.load(urllib.request.urlopen(req))
    doc = d["nodes"][nid]["document"]
    bb = doc["absoluteBoundingBox"]
    spec = compress(doc, (bb["x"], bb["y"]), remap)
    out = Path(f"/tmp/claude-501/spec-{nid.replace(':', '_')}.json")
    out.write_text(json.dumps(spec, ensure_ascii=False, separators=(",", ":")))
    print(f"{out} ({out.stat().st_size} bytes)")
    if "--texts" in sys.argv:
        def walk(n, d=0):
            if n["t"] == "TEXT":
                print(f"  T fs={n['fs']} fw={n['fw']} {n['ch'][:60]!r}")
            for c in n.get("k", []):
                walk(c, d + 1)
        walk(spec)


if __name__ == "__main__":
    main()

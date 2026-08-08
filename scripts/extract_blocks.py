#!/usr/bin/env python3
"""raw 노드 JSON → 블록 레코드(data/blocks.json)의 구조 필드를 산출한다.

- 구조 필드(스크립트 담당): bg, texts, max_font, images, bbox, seq ...
- 라벨 필드(Claude 담당): scene_type, layout, notes — 재실행 시 기존 값을 보존(merge by block_id).

사용법:
    python3 scripts/extract_blocks.py <product> [<product> ...]
    python3 scripts/extract_blocks.py --stats            # blocks.json 요약 통계
"""

import json
import sys
from pathlib import Path

from fetch_figma import PRODUCTS, REPO, RAW

BLOCKS_PATH = REPO / "data" / "blocks.json"


# ---------- 색상 유틸 ----------

def to_hex(c: dict) -> str:
    return "#%02X%02X%02X" % (round(c["r"] * 255), round(c["g"] * 255), round(c["b"] * 255))


def luminance(c: dict) -> float:
    """상대 휘도 (sRGB → WCAG)."""
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(c["r"]) + 0.7152 * lin(c["g"]) + 0.0722 * lin(c["b"])


def lum_class(lum: float) -> str:
    """배경 명도 3분류: L(밝음)/M(중간)/D(어두움) — design-principles A항 정량화."""
    if lum >= 0.55:
        return "L"
    if lum >= 0.18:
        return "M"
    return "D"


def solid_fill(node: dict):
    for f in node.get("fills", []) or []:
        if f.get("type") == "SOLID" and f.get("visible", True):
            return f["color"]
    return None


# ---------- 블록 분석 ----------

def area(bb: dict) -> float:
    return (bb.get("width") or 0) * (bb.get("height") or 0)


def block_bg(block: dict):
    """블록 배경색: 블록 자신의 SOLID fill → 없으면 블록 면적 60% 이상을 덮는
    최상위 자식 사각형/프레임의 fill → 그것도 없으면 흰색으로 간주(캔버스 노출)."""
    c = solid_fill(block)
    if c is not None:
        return c, "self"
    bb = block.get("absoluteBoundingBox") or {}
    for child in block.get("children", []) or []:
        cb = child.get("absoluteBoundingBox") or {}
        if area(bb) and area(cb) / area(bb) >= 0.6:
            cc = solid_fill(child)
            if cc is not None:
                return cc, f"child:{child['id']}"
    return {"r": 1, "g": 1, "b": 1}, "default-white"


def walk(node, fn, depth=0):
    fn(node, depth)
    for c in node.get("children", []) or []:
        walk(c, fn, depth + 1)


def analyze_block(block: dict, product_key: str, seq: int, frame_id: str, variant=None) -> dict:
    bb = block.get("absoluteBoundingBox") or {}
    bg_color, bg_src = block_bg(block)
    lum = luminance(bg_color)

    texts, image_nodes = [], []

    def visit(n, _d):
        if n.get("visible") is False:
            return
        if n["type"] == "TEXT" and n.get("characters", "").strip():
            s = n.get("style", {})
            c = solid_fill(n)
            texts.append({
                "id": n["id"],
                "chars": n["characters"][:120],
                "size": s.get("fontSize"),
                "family": s.get("fontFamily"),
                "weight": s.get("fontWeight"),
                "color": to_hex(c) if c else None,
            })
        for f in n.get("fills", []) or []:
            if f.get("type") == "IMAGE" and f.get("visible", True):
                nb = n.get("absoluteBoundingBox") or {}
                image_nodes.append({"id": n["id"], "area": area(nb)})
                break

    walk(block, visit)

    sizes = [t["size"] for t in texts if t["size"]]
    block_area = area(bb)
    img_area = sum(i["area"] for i in image_nodes)
    coverage = round(min(img_area / block_area, 1.0), 2) if block_area else 0

    rec = {
        "block_id": block["id"],
        "product": product_key,
        "label": PRODUCTS[product_key]["label"],
        "quality": "good" if PRODUCTS[product_key]["page"] == "good" else "bad",
        "seq": seq,
        "parent_frame": frame_id,
        "name": block.get("name", ""),
        "y": round(bb.get("y", 0)),
        "height": round(bb.get("height", 0)),
        "bg": {"hex": to_hex(bg_color), "lum": round(lum, 3), "class": lum_class(lum), "src": bg_src},
        "texts": texts,
        "max_font": max(sizes) if sizes else None,
        "char_total": sum(len(t["chars"]) for t in texts),
        "images": {"count": len(image_nodes), "coverage": coverage},
        # Claude 라벨링 필드 (merge 시 보존)
        "scene_type": None,
        "layout": None,
        "notes": None,
    }
    if variant:
        rec["variant"] = variant
    return rec


def extract(product: str) -> list[dict]:
    raw = json.loads((RAW / f"{product}.json").read_text())
    frames = raw["frames"]

    # 클렌즈 주스: 병렬 시안 2개 → x 좌표로 variant 분리
    variants = {}
    if product == "cleanse-juice":
        xs = sorted({round(f["absoluteBoundingBox"]["x"]) for f in frames})
        for f in frames:
            variants[f["id"]] = "A" if round(f["absoluteBoundingBox"]["x"]) == xs[0] else "B"

    records, seq_by_variant = [], {}
    for f in frames:  # frames는 이미 y→x 정렬(fetch_figma.frames_of)
        v = variants.get(f["id"])
        blocks = sorted(
            (raw["nodes"][b["id"]]["document"] for b in f.get("children", []) if b["id"] in raw["nodes"]),
            key=lambda b: (b.get("absoluteBoundingBox") or {}).get("y", 0),
        )
        for b in blocks:
            seq_by_variant[v] = seq_by_variant.get(v, 0) + 1
            records.append(analyze_block(b, product, seq_by_variant[v], f["id"], variant=v))
    return records


def merge_save(new_records: list[dict]):
    """기존 blocks.json과 병합. 라벨 필드(scene_type/layout/notes)는 기존 값 보존."""
    existing = {}
    if BLOCKS_PATH.exists():
        existing = {r["block_id"]: r for r in json.loads(BLOCKS_PATH.read_text())}
    for r in new_records:
        old = existing.get(r["block_id"])
        if old:
            for k in ("scene_type", "layout", "notes", "bg_override"):
                if old.get(k) is not None:
                    r[k] = old[k]
        existing[r["block_id"]] = r
    merged = sorted(existing.values(), key=lambda r: (r["quality"], r["product"], r.get("variant") or "", r["seq"]))
    BLOCKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOCKS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
    return merged


def stats():
    blocks = json.loads(BLOCKS_PATH.read_text())
    by = {}
    for b in blocks:
        by.setdefault(b["product"], []).append(b)
    for p, bs in by.items():
        seq = "-".join(b["bg"]["class"] for b in bs if not b.get("variant") or b["variant"] == "B")
        fonts = [b["max_font"] for b in bs if b["max_font"]]
        labeled = sum(1 for b in bs if b["scene_type"])
        print(f"{p:<14} blocks={len(bs):<4} labeled={labeled:<4} bg={seq}")
        if fonts:
            print(f"{'':<14} max_font min/med/max = {min(fonts):.0f}/{sorted(fonts)[len(fonts)//2]:.0f}/{max(fonts):.0f}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--stats":
        stats()
        return
    all_new = []
    for product in sys.argv[1:]:
        if product not in PRODUCTS:
            sys.exit(f"unknown product: {product}")
        recs = extract(product)
        print(f"{product}: {len(recs)} blocks extracted", file=sys.stderr)
        all_new += recs
    merged = merge_save(all_new)
    print(f"blocks.json: {len(merged)} total records", file=sys.stderr)


if __name__ == "__main__":
    main()

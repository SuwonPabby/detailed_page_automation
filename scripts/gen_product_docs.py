#!/usr/bin/env python3
"""blocks.json → docs/analysis/products/*.md 제품별 블록 표 생성."""

import json
from pathlib import Path

from fetch_figma import PRODUCTS, REPO

OUT = REPO / "docs" / "analysis" / "products"
ORDER = ["glowshot", "kkuljam", "goosemeal", "olivit", "cleanse-juice",
         "iljin-wire", "milbat", "cleanse", "fileconv",
         "sangha-soup", "block-soup", "tomato", "section4", "potato"]


def main():
    blocks = json.loads((REPO / "data" / "blocks.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for i, prod in enumerate(ORDER, 1):
        bs = [b for b in blocks if b["product"] == prod]
        if not bs:
            continue
        meta = PRODUCTS[prod]
        lines = [
            f"# {i:02d}-{prod} — {meta['label']} ({'Good' if meta['page'] == 'good' else 'Bad'})",
            "",
            f"> 자동 생성: `python3 scripts/gen_product_docs.py`. 원천은 `data/blocks.json`.",
            f"> 스크린샷: `get_screenshot(fileKey=\"jjgud5OkeXKA4weyP3FEND\", nodeId=<블록ID>)`",
            "",
            "| seq | 블록 ID | scene | layout | bg | h | max_font | 노트 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for b in bs:
            bg = b.get("bg_override") or b["bg"]["class"]
            var = f"[{b['variant']}] " if b.get("variant") else ""
            notes = (b.get("notes") or "").replace("|", "·")[:90]
            lines.append(
                f"| {var}{b['seq']} | `{b['block_id']}` | {b['scene_type'] or '—'} | "
                f"{b['layout'] or '—'} | {bg} | {b['height']} | {b['max_font'] or '—'} | {notes} |"
            )
        (OUT / f"{i:02d}-{prod}.md").write_text("\n".join(lines) + "\n")
        print(f"{i:02d}-{prod}.md ({len(bs)} blocks)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Claude가 스크린샷을 보고 판정한 라벨을 blocks.json에 적용한다.

라벨 원천은 data/labels/<product>.json — Claude가 세션 중 작성.
형식: { "<block_id>": {"scene_type": ..., "layout": ..., "notes": ..., "bg_override": ...}, ... }

bg_override: 이미지 배경 블록은 SOLID fill 기반 bg.class가 실제와 다를 수 있어
스크린샷 판정으로 덮어쓴다 (예: "D", "M", "D+L", "L→M").

사용법: python3 scripts/apply_labels.py <product> [...]
"""

import json
import sys
from pathlib import Path

from fetch_figma import REPO

BLOCKS_PATH = REPO / "data" / "blocks.json"
LABELS_DIR = REPO / "data" / "labels"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    blocks = {b["block_id"]: b for b in json.loads(BLOCKS_PATH.read_text())}
    applied = 0
    for product in sys.argv[1:]:
        labels = json.loads((LABELS_DIR / f"{product}.json").read_text())
        for block_id, label in labels.items():
            if block_id not in blocks:
                print(f"  경고: {block_id} 없음 (product={product})", file=sys.stderr)
                continue
            for k, v in label.items():
                blocks[block_id][k] = v
            applied += 1
    out = sorted(blocks.values(), key=lambda r: (r["quality"], r["product"], r.get("variant") or "", r["seq"]))
    BLOCKS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    unlabeled = [b["block_id"] for b in out if b["scene_type"] is None]
    print(f"applied={applied}, total={len(out)}, unlabeled={len(unlabeled)}")


if __name__ == "__main__":
    main()

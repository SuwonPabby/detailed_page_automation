#!/usr/bin/env python3
"""Full_design(읽기 전용 레퍼런스)에서 분석용 원본 데이터를 배치로 가져와 캐시한다.

- 읽기 전용: GET 요청만 사용한다. rules.md §1의 쓰기 경계를 절대 넘지 않는다.
- 캐시 우선: data/raw/ 에 이미 있으면 API를 다시 부르지 않는다.
- 토큰: main worktree의 .env를 정규식으로 파싱한다 (source 금지 — rules.md §2).

사용법:
    python3 scripts/fetch_figma.py sections            # 전 SECTION 구조 스캔 (depth=2)
    python3 scripts/fetch_figma.py blocks <product>    # 제품의 블록 서브트리 배치 취득
    python3 scripts/fetch_figma.py shots <product>     # 제품 스크린샷 URL 발급 + 다운로드
    python3 scripts/fetch_figma.py all <product>       # blocks + shots
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

FILE_KEY = "jjgud5OkeXKA4weyP3FEND"
ENV_PATH = Path.home() / "projects/detailed_page_automation/.env"
REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "data" / "raw"
SHOTS = RAW / "shots"

# figma-spaces.md 인벤토리 기준. section: 제품 SECTION 노드 ID.
# frames: 분석 대상 860px 프레임 (스크린샷 단위). blocks_expected: 교차 검증용.
PRODUCTS = {
    # Good
    "glowshot":   {"page": "good", "section": "1:2",     "label": "글로우샷"},
    "kkuljam":    {"page": "good", "section": "1:539",   "label": "꿀잠모드"},
    "goosemeal":  {"page": "good", "section": "1:1305",  "label": "구스밀"},
    "olivit":     {"page": "good", "section": "1:21812", "label": "올리빗"},
    "cleanse-juice": {"page": "good", "section": "1:57168", "label": "클렌즈 주스"},
    "iljin-wire": {"page": "good", "section": "1:82346", "label": "일진와이어"},
    "milbat":     {"page": "good", "section": "1:82814", "label": "밀밭명가"},
    "cleanse":    {"page": "good", "section": "1:84516", "label": "클렌즈"},
    "fileconv":   {"page": "good", "section": "1:84542", "label": "파일변환"},
    # Bad
    "sangha-soup": {"page": "bad", "section": "1:84811", "label": "상하키친 스프"},
    "block-soup":  {"page": "bad", "section": "1:84822", "label": "간편블럭국"},
    "tomato":      {"page": "bad", "section": "1:85419", "label": "토마토"},
    "section4":    {"page": "bad", "section": "1:85854", "label": "Section 4"},
    "potato":      {"page": "bad", "section": "10:86226", "label": "감자"},
}

BATCH = 15  # /nodes ids 배치 크기


def token() -> str:
    for line in ENV_PATH.read_text().splitlines():
        m = re.match(r"\s*FIGMA_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
        if m:
            return m.group(1)
    sys.exit(f"FIGMA_API_KEY not found in {ENV_PATH}")


def api(path: str, params: dict | None = None) -> dict:
    qs = ("?" + urllib.parse.urlencode(params)) if params else ""
    url = f"https://api.figma.com/v1{path}{qs}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token()})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:  # rate limit → 대기 후 재시도
                wait = int(e.headers.get("Retry-After", 30))
                print(f"  429 rate-limited, {wait}s 대기...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def cached(path: Path, fetch):
    """캐시가 있으면 읽고, 없으면 fetch() 결과를 저장 후 반환."""
    if path.exists():
        return json.loads(path.read_text())
    data = fetch()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False))
    print(f"  cached → {path.relative_to(REPO)}", file=sys.stderr)
    return data


def fetch_sections() -> dict:
    """전 SECTION을 depth=2로 스캔: 860프레임 목록 + 각 프레임의 자식 블록 ID/bbox."""
    ids = ",".join(p["section"] for p in PRODUCTS.values())
    return cached(
        RAW / "sections-depth2.json",
        lambda: api(f"/files/{FILE_KEY}/nodes", {"ids": ids, "depth": 2}),
    )


def frames_of(product: str, sections: dict) -> list[dict]:
    """SECTION에서 분석 단위인 860±2px 프레임을 y→x 순서로 반환."""
    sec = sections["nodes"][PRODUCTS[product]["section"]]["document"]
    frames = [
        c for c in sec.get("children", [])
        if c.get("absoluteBoundingBox")
        and abs(c["absoluteBoundingBox"]["width"] - 861) <= 3  # 858~864 허용
    ]
    frames.sort(key=lambda f: (f["absoluteBoundingBox"]["y"], f["absoluteBoundingBox"]["x"]))
    return frames


def fetch_blocks(product: str) -> dict:
    """제품의 모든 블록 서브트리를 배치로 취득해 raw/<product>.json에 캐시."""
    out_path = RAW / f"{product}.json"
    if out_path.exists():
        print(f"  cache hit: {out_path.relative_to(REPO)}", file=sys.stderr)
        return json.loads(out_path.read_text())

    sections = fetch_sections()
    frames = frames_of(product, sections)
    block_ids = [b["id"] for f in frames for b in f.get("children", [])]
    print(f"  {product}: frames={len(frames)} blocks={len(block_ids)}", file=sys.stderr)

    nodes: dict = {}
    for i in range(0, len(block_ids), BATCH):
        chunk = block_ids[i : i + BATCH]
        resp = api(f"/files/{FILE_KEY}/nodes", {"ids": ",".join(chunk)})
        nodes.update(resp["nodes"])
        print(f"  batch {i // BATCH + 1}: {len(chunk)} blocks", file=sys.stderr)

    data = {"product": product, "frames": frames, "nodes": nodes}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False))
    return data


def fetch_shots(product: str, per_block_over: int = 6000) -> list[Path]:
    """스크린샷: 기본은 프레임 단위 1장. 프레임이 너무 길면(>per_block_over px) 블록 개별."""
    sections = fetch_sections()
    frames = frames_of(product, sections)

    targets: list[str] = []
    for f in frames:
        h = f["absoluteBoundingBox"]["height"]
        if h > per_block_over:
            targets += [b["id"] for b in f.get("children", [])]
        else:
            targets.append(f["id"])

    meta_path = SHOTS / f"{product}-urls.json"
    urls = cached(
        meta_path,
        lambda: api(f"/images/{FILE_KEY}", {"ids": ",".join(targets), "scale": 0.35, "format": "png"}),
    )["images"]

    paths = []
    SHOTS.mkdir(parents=True, exist_ok=True)
    for node_id, url in urls.items():
        if not url:
            print(f"  render 실패: {node_id}", file=sys.stderr)
            continue
        dest = SHOTS / f"{product}-{node_id.replace(':', '_')}.png"
        if not dest.exists():
            urllib.request.urlretrieve(url, dest)  # S3 직행 — rate limit 무관
        paths.append(dest)
    print(f"  {product}: {len(paths)} shots", file=sys.stderr)
    return paths


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "sections":
        s = fetch_sections()
        for key, p in PRODUCTS.items():
            frames = frames_of(key, s)
            n = sum(len(f.get("children", [])) for f in frames)
            print(f"{key:<14} frames={len(frames):<3} blocks={n}")
    elif cmd in ("blocks", "shots", "all"):
        product = sys.argv[2]
        if product not in PRODUCTS:
            sys.exit(f"unknown product: {product} (choices: {', '.join(PRODUCTS)})")
        if cmd in ("blocks", "all"):
            fetch_blocks(product)
        if cmd in ("shots", "all"):
            fetch_shots(product)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

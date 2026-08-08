#!/usr/bin/env python3
"""qa_check.py — 상세페이지 산출물의 결정론적 공리 검사

설계 근거: VLM-as-judge는 척추가 될 수 없다. Nielsen 휴리스틱 평가에서
GPT-4o 재현율은 21.2%(arXiv 2506.16345)에 그친다. 반면 craft-axioms의
상당수는 Figma 노드 트리에서 **정확히** 계산된다 — DOM보다 정확하다.

따라서 판정 구조는:
  ① 이 스크립트(결정론적)  → 수치로 판정 가능한 공리
  ② detail-page-reviewer   → 주관적 잔여물 (구성·질감·컨셉 일치)
  ③ compliance 블랙리스트  → 법적 게이트

사용:
  python3 pipeline/qa_check.py <fileKey> <rootNodeId>
  python3 pipeline/qa_check.py e4Nto2oOgqwbCcrI6Y4Btb 11:3 --json
"""
import argparse
import json
import os
import re
import statistics
import sys
import urllib.request

ENV = os.path.expanduser("~/projects/detailed_page_automation/.env")
API = "https://api.figma.com/v1"

# ── 임계값 (docs/analysis/craft-axioms.md · design-tokens.md 실측 기반) ──
HEADLINE_MIN = 64      # A-1  블록 헤드라인 하한 @860
BODY_FLOOR = 24        # A-3  본문 하드 하한 (모바일 환산 11 CSS px)
BODY_TARGET = 32       # A-3  본문 권장 하한 (모바일 환산 14.6 CSS px)
FOOTNOTE_MIN = 20      # A-4  각주 하한
HIER_MIN = 2.0         # A-2  위계비 (Good med 2.17 / Bad med 1.76)
LIGHT_RUN_MAX = 5      # B-2  동일 명도 연속 상한
DARK_MIN, DARK_MAX = 2, 6   # B-3
FONT_FAMILY_MAX = 3    # A-5  3% 이상 점유 패밀리 수
TEXT_DENSITY_MAX = 115 # C-5  자 / 1000px 블록 높이
BLOCK_MIN, BLOCK_MAX = 6, 23  # C-3
MOBILE_SCALE = 393 / 860      # iPhone 15 뷰포트 환산


def token():
    with open(ENV) as f:
        for line in f:
            m = re.match(r"\s*FIGMA_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                return m.group(1)
    sys.exit("FIGMA_API_KEY not found in " + ENV)


def api(path, tok):
    req = urllib.request.Request(API + path, headers={"X-Figma-Token": tok})
    return json.load(urllib.request.urlopen(req))


def lum(c):
    """WCAG relative luminance. c = {r,g,b} 0-1"""
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c["r"]) + 0.7152 * ch(c["g"]) + 0.0722 * ch(c["b"])


def lum_class(l):
    return "L" if l >= 0.55 else ("M" if l >= 0.18 else "D")


def solid_of(node):
    """노드의 대표 배경 명도. GRADIENT는 정지점 평균."""
    for f in node.get("fills") or []:
        if not f.get("visible", True):
            continue
        if f["type"] == "SOLID":
            return lum(f["color"])
        if f["type"].startswith("GRADIENT"):
            stops = f.get("gradientStops") or []
            if stops:
                return statistics.mean(lum(s["color"]) for s in stops)
    return None


def contrast(l1, l2):
    a, b = max(l1, l2), min(l1, l2)
    return (a + 0.05) / (b + 0.05)


def walk(node, out=None, depth=0, chain=()):
    """(node, depth, ancestor_chain) — chain은 루트→부모 순."""
    out = [] if out is None else out
    out.append((node, depth, chain))
    for c in node.get("children") or []:
        walk(c, out, depth + 1, chain + (node,))
    return out


def scrim_lum(parent):
    """형제 스크림 사각형의 유효 명도.

    스크림은 텍스트의 *조상*이 아니라 *형제*다(같은 스테이지 프레임 안에
    이미지→스크림→텍스트 순으로 쌓임). 조상만 훑으면 '스크림 위 흰 글씨'를
    전부 오탐한다 — 실제로 v2 1라운드에서 타일 라벨 5개를 오판했다.
    """
    best = None
    for c in parent.get("children") or []:
        if c["type"] != "RECTANGLE":
            continue
        for f in c.get("fills") or []:
            if not f.get("visible", True):
                continue
            if f["type"].startswith("GRADIENT"):
                stops = f.get("gradientStops") or []
                if not stops:
                    continue
                # 불투명도 가중 — 진한 쪽이 텍스트가 얹히는 영역
                w = max(stops, key=lambda s: s["color"].get("a", 1))
                best = lum(w["color"]) if best is None else min(best, lum(w["color"]))
    return best


def local_bg(chain, fallback):
    """텍스트가 실제로 얹힌 배경 명도.

    ① 형제 스크림이 있으면 그것을 쓰고, ② 없으면 조상 체인을 안쪽부터 훑어
    채움이 있는 첫 노드를 쓴다. 블록 배경으로 일괄 비교하면 '다크 카드 위
    흰 글씨'가 전부 오탐으로 잡힌다.
    """
    if chain:
        s = scrim_lum(chain[-1])
        if s is not None:
            return s
    for n in reversed(chain):
        v = solid_of(n)
        if v is not None:
            return v
    return fallback


def role_of(t, sizes):
    """텍스트 역할 분류. 각주는 본문 하한을 적용받지 않는다."""
    s = (t["text"] or "").lstrip()
    if s[:1] in ("*", "※") or s[:1] == "†":
        return "footnote"
    if sizes and t["size"] == max(sizes):
        return "headline"
    if sizes and t["size"] <= min(sizes) + 1:
        return "footnote"
    return "body"


def analyze_block(blk):
    """블록 1개 → 측정치"""
    nodes = walk(blk)
    bg = solid_of(blk)
    # 배경을 못 읽으면 가장 큰 자식 프레임에서 상속
    if bg is None:
        for n, _, _ in nodes[1:]:
            v = solid_of(n)
            if v is not None:
                bg = v
                break
    texts = []
    for n, _, chain in nodes:
        if n["type"] != "TEXT":
            continue
        # IMG_ 슬롯 안의 라벨은 에셋 도착 시 사라지는 작업용 주석 — 채점 제외
        if any(a.get("name", "").startswith("IMG_") for a in chain):
            continue
        st = n.get("style") or {}
        size = st.get("fontSize")
        if not size:
            continue
        col = None
        for f in n.get("fills") or []:
            if f.get("visible", True) and f["type"] == "SOLID":
                col = lum(f["color"])
                break
        texts.append({
            "chars": len(n.get("characters") or ""),
            "size": round(size, 1),
            "family": st.get("fontFamily"),
            "lum": col,
            "bg": local_bg(chain, bg),
            "id": n["id"],
            "text": (n.get("characters") or "")[:40].replace("\n", " "),
        })
    sizes = [t["size"] for t in texts]
    for t in texts:
        t["role"] = role_of(t, sizes)
    h = (blk.get("absoluteBoundingBox") or {}).get("height", 0)
    rec = {
        "id": blk["id"],
        "name": blk.get("name", ""),
        "h": round(h),
        "bg_lum": round(bg, 4) if bg is not None else None,
        "bg_class": lum_class(bg) if bg is not None else "?",
        "max_font": max(sizes) if sizes else 0,
        "texts": texts,
        "chars": sum(t["chars"] for t in texts),
        "n_img": sum(1 for n, _, _ in nodes if n.get("name", "").startswith("IMG_")),
    }
    # 위계비 = 최대 폰트 / 나머지 텍스트 크기 중앙값
    rest = sorted(sizes)[:-1] if len(sizes) > 1 else []
    rec["hier"] = round(rec["max_font"] / statistics.median(rest), 2) if rest else None
    rec["density"] = round(rec["chars"] / (h / 1000), 1) if h else 0
    return rec


def check(blocks, page_h):
    """공리 판정. → (findings, stats)"""
    f = []           # (severity, axiom, where, message)
    seq = "".join(b["bg_class"] for b in blocks)

    # ── A-1 헤드라인 하한 ──
    weak = [b for b in blocks if b["max_font"] and b["max_font"] < HEADLINE_MIN
            and b["chars"] > 40]
    if weak:
        f.append(("WARN", "A-1", ",".join(b["name"] for b in weak[:5]),
                  f"헤드라인 {HEADLINE_MIN}px 미만 블록 {len(weak)}개 "
                  f"(Good 실측 중앙값 80 / Bad 55)"))

    # ── A-2 위계비 ── ★ Bad를 가르는 진짜 신호
    flat = [b for b in blocks if b["hier"] and b["hier"] < HIER_MIN and b["chars"] > 40]
    if flat:
        f.append(("FAIL" if len(flat) > len(blocks) * 0.3 else "WARN", "A-2",
                  ",".join(f"{b['name']}({b['hier']})" for b in flat[:5]),
                  f"위계비 {HIER_MIN} 미만 블록 {len(flat)}개. "
                  f"Bad 페이지의 실제 병증은 작은 본문이 아니라 낙차 없는 위계"))

    # ── A-3 / A-4 본문·각주 하한 (모바일 환산) ──
    tiny = [(b["name"], t) for b in blocks for t in b["texts"]
            if t["size"] < FOOTNOTE_MIN]
    if tiny:
        f.append(("FAIL", "A-4",
                  ",".join(f"{n}:{t['size']}px" for n, t in tiny[:5]),
                  f"각주 하한 {FOOTNOTE_MIN}px 미만 {len(tiny)}건 "
                  f"(모바일 환산 {FOOTNOTE_MIN*MOBILE_SCALE:.1f} CSS px 미만 = 판독 불가)"))
    subfloor = [(b["name"], t) for b in blocks for t in b["texts"]
                if t["role"] == "body" and t["size"] < BODY_FLOOR]
    if subfloor:
        f.append(("WARN", "A-3",
                  ",".join(f"{n}:{t['size']}px" for n, t in subfloor[:5]),
                  f"본문(각주 제외) {BODY_FLOOR}px 미만 {len(subfloor)}건 "
                  f"(권장 {BODY_TARGET}px = 모바일 {BODY_TARGET*MOBILE_SCALE:.1f} CSS px)"))

    # ── A-5 폰트 패밀리 수 ──
    fam = {}
    for b in blocks:
        for t in b["texts"]:
            fam[t["family"]] = fam.get(t["family"], 0) + 1
    tot = sum(fam.values()) or 1
    major = {k: v for k, v in fam.items() if v / tot >= 0.03}
    if len(major) > FONT_FAMILY_MAX:
        f.append(("WARN", "A-5", ", ".join(major),
                  f"3% 이상 점유 폰트 패밀리 {len(major)}종 (상한 {FONT_FAMILY_MAX})"))

    # ── B-1 대비비 ──
    lo = []
    for b in blocks:
        for t in b["texts"]:
            if t["lum"] is None or t["bg"] is None:
                continue
            cr = contrast(t["lum"], t["bg"])   # ← 지역 배경 기준 (블록 배경 아님)
            need = 3.0 if t["size"] >= 24 else 4.5
            if cr < need:
                lo.append((b["name"], t, round(cr, 2), need))
    if lo:
        f.append(("FAIL", "B-1",
                  ",".join(f"{n}:{t['text'][:14]}({c}:1)" for n, t, c, _ in lo[:5]),
                  f"WCAG 대비 미달 {len(lo)}건. ※ 이미지 슬롯 위 텍스트는 그라디언트 "
                  f"평균으로 근사하므로 스크림이 있으면 오탐 가능"))

    # ── B-2 동일 명도 연속 런 ──
    runs, cur, ch = [], 1, seq[:1]
    for c in seq[1:]:
        if c == ch:
            cur += 1
        else:
            runs.append((ch, cur)); ch, cur = c, 1
    runs.append((ch, cur))
    worst = max((n for _, n in runs), default=0)
    if worst > LIGHT_RUN_MAX:
        f.append(("FAIL", "B-2", f"최장 런 {worst}",
                  f"동일 배경 명도 {worst}연속 (상한 {LIGHT_RUN_MAX}). "
                  f"Good 실측 2~7 / Bad 7~21"))

    # ── B-3 다크 블록 수 ──
    nd = seq.count("D")
    if not (DARK_MIN <= nd <= DARK_MAX):
        f.append(("FAIL" if nd < DARK_MIN else "WARN", "B-3", f"D={nd}",
                  f"다크 블록 {nd}개 (권장 {DARK_MIN}~{DARK_MAX}). "
                  f"Bad 5종 중 4종이 0개"))

    # ── C-1 인접 블록 높이·구성 동일 (레이아웃 반복 근사) ──
    dup = []
    for i in range(len(blocks) - 1):
        a, b = blocks[i], blocks[i + 1]
        if a["bg_class"] == b["bg_class"] and a["h"] and b["h"] \
           and abs(a["h"] - b["h"]) / max(a["h"], b["h"]) < 0.08 \
           and abs(a["max_font"] - b["max_font"]) < 3:
            dup.append(f"{a['name']}↔{b['name']}")
    if dup:
        f.append(("WARN", "C-1", ", ".join(dup[:4]),
                  f"인접 블록이 배경·높이·최대폰트까지 유사 {len(dup)}쌍 — "
                  f"레이아웃 반복 의심 (Bad의 최다 QA 지적)"))

    # ── C-3 블록 수 / 총 길이 ──
    if not (BLOCK_MIN <= len(blocks) <= BLOCK_MAX):
        f.append(("WARN", "C-3", f"{len(blocks)}블록",
                  f"서사 블록 수 권장 {BLOCK_MIN}~{BLOCK_MAX}"))
    if page_h > 37400:
        f.append(("WARN", "C-3", f"{page_h}px", "총 길이 실측 상한(37,400px) 초과"))

    # ── C-5 텍스트 밀도 ──
    dense = [b for b in blocks if b["density"] > TEXT_DENSITY_MAX]
    if dense:
        f.append(("WARN", "C-5",
                  ",".join(f"{b['name']}({b['density']})" for b in dense[:4]),
                  f"텍스트 밀도 {TEXT_DENSITY_MAX}자/1000px 초과 {len(dense)}블록"))

    # ── F1 콘텐츠 폭 불변 (풀블리드 존재) ──
    # 블록 자식 중 폭 860 요소가 있으면 풀블리드로 간주
    if not any(b["n_img"] for b in blocks):
        f.append(("WARN", "F3", "-", "IMG_ 슬롯이 하나도 없음 — 이미지 계획 누락?"))

    # ── 리듬: 블록 높이 변동계수 (§4.1 클라이맥스) ──
    hs = [b["h"] for b in blocks if b["h"]]
    cv = statistics.pstdev(hs) / statistics.mean(hs) if hs else 0
    if cv < 0.25:
        f.append(("WARN", "§4.1", f"CV={cv:.2f}",
                  "블록 높이 변동계수 0.25 미만 = 평평한 페이지. 클라이맥스 블록 부재"))

    stats = {
        "blocks": len(blocks), "page_h": page_h,
        "bg_seq": seq, "dark": nd, "longest_run": worst,
        "height_cv": round(cv, 3),
        "max_font_med": statistics.median([b["max_font"] for b in blocks if b["max_font"]] or [0]),
        "hier_med": statistics.median([b["hier"] for b in blocks if b["hier"]] or [0]),
        "font_families": major,
    }
    return f, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file_key")
    ap.add_argument("node_id")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tok = token()
    doc = api(f"/files/{a.file_key}/nodes?ids={a.node_id}&geometry=paths", tok)
    root = doc["nodes"][a.node_id]["document"]
    blocks = [analyze_block(c) for c in root.get("children") or []]
    page_h = round((root.get("absoluteBoundingBox") or {}).get("height", 0))

    findings, stats = check(blocks, page_h)

    if a.json:
        print(json.dumps({"stats": stats, "findings": findings,
                          "blocks": [{k: v for k, v in b.items() if k != "texts"}
                                     for b in blocks]}, ensure_ascii=False, indent=1))
        return

    print(f"== {a.file_key} / {a.node_id} ==")
    print(f"블록 {stats['blocks']}개 · 총 {stats['page_h']:,}px · 배경 {stats['bg_seq']}")
    print(f"다크 {stats['dark']} · 최장런 {stats['longest_run']} · 높이CV {stats['height_cv']}")
    print(f"헤드라인 중앙값 {stats['max_font_med']}px · 위계비 중앙값 {stats['hier_med']}")
    print(f"폰트 {stats['font_families']}")
    print()
    n_fail = sum(1 for s, *_ in findings if s == "FAIL")
    if not findings:
        print("✅ 결정론적 공리 위반 없음")
    for sev, ax, where, msg in findings:
        print(f"[{sev}] {ax}  {msg}\n        → {where}")
    print()
    print(f"판정: {'FAIL' if n_fail else 'PASS(결정론 부분)'}  "
          f"(FAIL {n_fail} / WARN {len(findings)-n_fail})")
    print("※ 구성·질감·컨셉 일치 등 주관 항목은 detail-page-reviewer 에이전트가 판정한다.")


if __name__ == "__main__":
    main()

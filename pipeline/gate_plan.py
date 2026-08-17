#!/usr/bin/env python3
"""gate_plan.py — 2단계 플랜 게이트 (결정론)

설계 근거: docs/agent-architecture.md §1 2단계.
plan.json이 HITL 승인으로 넘어가기 전에 코드가 먼저 거른다.
MAST(2025)의 최대 실패 계급 = "정보를 조용히 떨어뜨림" → 소비 검증(traceability)이 핵심.

검사:
  A. 스키마 — 필수 키, design_system 필수 필드, blocks 필수 필드
  B. Traceability — 기획안(source_brief)의 모든 장면 번호가 플랜에 등장하는가.
     블록의 `scenes: [1,2]` 필드(권장) 또는 copy 문자열의 `기획안 N`/`(N)` 표기로 수집.
     의도적 생략은 `skipped_scenes: {"7": "사유"}`로 명시해야 통과.
  C. 미결 이슈 — copy_decisions에 ⚠가 있으면 `open_issues_ack: true` 없이는 불통과
     (수치 충돌은 임의로 고르지 않는다 — SKILL.md §2-2)
  D. 리듬 — bg_rhythm 문자열: 블록 수 일치, 연속 L ≤ 5, D 2~6개
  E. 인접 블록 동일 layout 금지 (SKILL.md: 인접 블록 동일 패턴 금지)
  F. constraints 필드 — 모든 아티팩트에 동승해야 할 제약(compliance·사용자 지침).
     없으면 경고, --strict면 오류 (agent-architecture.md §2 아티팩트 규약)

사용:
  python3 pipeline/gate_plan.py <plan.json> [--strict] [--json]
종료코드: 0 = 통과(HITL 승인으로), 1 = 반려
"""
import json
import re
import sys

TOP_REQUIRED = ("product", "source_brief", "design_system", "copy_decisions",
                "bg_rhythm", "blocks")
DS_REQUIRED = ("dominant", "accent", "neutral", "text", "fonts", "type_scale")
BLOCK_REQUIRED = ("seq", "scene_type", "layout", "bg", "h", "copy")
LIGHT_RUN_MAX = 5          # qa_check.py B-2와 동일 임계
DARK_MIN, DARK_MAX = 2, 6  # qa_check.py B-3와 동일 임계


def scene_refs(block):
    """블록이 소비하는 기획안 장면 번호 집합."""
    out = set()
    for s in block.get("scenes") or []:
        out.add(int(s))
    copy = str(block.get("copy") or "")
    # '기획안 1~5' / '기획안 3' / '(기획안 12)' 표기 인식
    for m in re.finditer(r"기획안\s*(\d+)(?:\s*[~\-]\s*(\d+))?", copy):
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        out.update(range(a, b + 1))
    return out


def check(plan_path, strict=False):
    errors, warnings = [], []
    try:
        plan = json.load(open(plan_path))
    except (OSError, json.JSONDecodeError) as e:
        return [f"plan.json을 읽을 수 없음: {e}"], []

    # A. 스키마
    for k in TOP_REQUIRED:
        if k not in plan:
            errors.append(f"스키마: 최상위 `{k}` 없음")
    ds = plan.get("design_system") or {}
    for k in DS_REQUIRED:
        if k not in ds:
            errors.append(f"스키마: design_system.`{k}` 없음")
    blocks = plan.get("blocks") or []
    for i, b in enumerate(blocks):
        for k in BLOCK_REQUIRED:
            if k not in b:
                errors.append(f"스키마: blocks[{i}](seq {b.get('seq','?')}) `{k}` 없음")

    # B. Traceability
    brief_path = plan.get("source_brief")
    if brief_path:
        try:
            brief = json.load(open(brief_path))
            brief_scenes = {s["no"] for s in brief.get("scenes", []) if "no" in s}
            covered = set()
            for b in blocks:
                covered |= scene_refs(b)
            skipped = {int(k) for k in (plan.get("skipped_scenes") or {})}
            missing = sorted(brief_scenes - covered - skipped)
            if missing:
                errors.append(
                    f"traceability: 기획안 장면 {missing} 이(가) 플랜에 없음 — "
                    f"블록에 `scenes` 필드로 명시하거나 `skipped_scenes`에 사유를 적어라")
            ghost = sorted(covered - brief_scenes)
            if ghost:
                warnings.append(f"traceability: 기획안에 없는 장면 참조 {ghost}")
        except (OSError, json.JSONDecodeError) as e:
            errors.append(f"traceability: source_brief 읽기 실패 ({e})")

    # C. 미결 이슈
    open_issues = [d for d in plan.get("copy_decisions", [])
                   if "⚠" in str(d.get("decision", ""))]
    if open_issues and not plan.get("open_issues_ack"):
        errors.append(
            f"미결 이슈 {len(open_issues)}건(⚠)이 사용자 확정 없이 남아 있음 — "
            f"확정받은 뒤 `open_issues_ack: true`를 기록하라. 임의 선택 금지")

    # D. 리듬
    rhythm = re.sub(r"[^ADLM]", "", str(plan.get("bg_rhythm", "")).split("(")[0])
    if rhythm and blocks and len(rhythm) != len(blocks):
        warnings.append(f"리듬: bg_rhythm {len(rhythm)}자 ≠ blocks {len(blocks)}개")
    if re.search(r"L{%d,}" % (LIGHT_RUN_MAX + 1), rhythm):
        errors.append(f"리듬: 연속 L {LIGHT_RUN_MAX + 1}개 이상 (B-2)")
    d_count = rhythm.count("D")
    if rhythm and not (DARK_MIN <= d_count <= DARK_MAX):
        errors.append(f"리듬: D {d_count}개 — {DARK_MIN}~{DARK_MAX} 범위 밖 (B-3)")

    # E. 인접 동일 layout
    for prev, cur in zip(blocks, blocks[1:]):
        if prev.get("layout") and prev.get("layout") == cur.get("layout"):
            errors.append(f"레이아웃: seq {prev.get('seq')}→{cur.get('seq')} "
                          f"인접 블록 동일 패턴 '{cur.get('layout')}'")

    # H. 클레임 서열 → 시각 자원 배분 (craft-axioms §9 U2 — gap-v6 G4·G23·G24)
    #    하위호환: `claims` 필드가 있는 플랜에만 강제. "당류 블록 이미지 0장" 재발 방지가 목적.
    claims = plan.get("claims")
    if claims:
        EMPH = {"climax", "normal", "breather", "notice"}
        BUDGET = {"hero", "full", "standard", "minimal"}
        r1 = next((c for c in claims if c.get("rank") == 1), None)
        if not r1:
            errors.append("클레임: rank 1이 없다 — 1순위 클레임을 서열화하라")
        missing_e = [b.get("seq") for b in blocks if b.get("emphasis") not in EMPH]
        if missing_e:
            errors.append(f"클레임: blocks {missing_e[:8]} 의 `emphasis` 누락/오기 "
                          f"({sorted(EMPH)})")
        climax = [b for b in blocks if b.get("emphasis") == "climax"]
        if not climax:
            errors.append("클레임: emphasis=climax 블록이 없다 — 1순위 클레임에 물리량을 배분하라")
        elif r1:
            r1_scenes = set(map(int, r1.get("scenes") or []))
            hit = any(r1_scenes & set(map(int, b.get("scenes") or [])) for b in climax)
            if not hit:
                errors.append(f"클레임: rank 1({r1.get('claim')})의 장면 {sorted(r1_scenes)}이 "
                              f"climax 블록에 배정되지 않았다")
            ev = r1.get("evidence") or []
            if len(ev) < 3:
                errors.append(f"클레임: rank 1의 증거 유형 {len(ev)}종 — 최소 3종 적층 "
                              f"(선언타이포·차트/표·시즐컷·리뷰 중) (§9 U2)")
        for b in climax:
            hs = [x.get("h", 0) for x in blocks if x.get("h")]
            if hs and b.get("h", 0) < max(hs):
                errors.append(f"클레임: climax(seq {b.get('seq')}) h={b.get('h')} < "
                              f"최장 {max(hs)} — 클라이맥스는 페이지 최장이어야 한다")
            if b.get("asset_budget") not in ("hero",):
                warnings.append(f"클레임: climax(seq {b.get('seq')})의 asset_budget이 "
                                f"'hero'가 아니다 — 이미지 ≥2·커버리지 ≥50% 배분 권장")

    # G. 배경 표면 시스템 (agentic-workflow 1단계 산출물 — 하위호환:
    #    design_system.surface_system이 선언된 플랜에만 강제한다)
    ss = ds.get("surface_system")
    if ss:
        SURFACES = {"solid", "texture", "gradient", "photo"}
        ratios = ss.get("ratios") or {}
        bad_keys = set(ratios) - SURFACES
        if bad_keys:
            errors.append(f"표면: surface_system.ratios에 미정의 표면 {sorted(bad_keys)}")
        # 블록별 surface 필수 + 어휘 검증
        missing, counts = [], {}
        for b in blocks:
            sv = b.get("surface")
            if sv not in SURFACES:
                missing.append(b.get("seq", "?"))
            else:
                counts[sv] = counts.get(sv, 0) + 1
        if missing:
            errors.append(f"표면: blocks {missing} 의 `surface` 필드 누락/오기 — "
                          f"{sorted(SURFACES)} 중 하나를 선언하라 (배너·고지 포함)")
        n = sum(counts.values())
        if n:
            # solid 상한 — craft-axioms §3.1: 단색 과다 = 다양성·창의성 부족
            solid_ratio = counts.get("solid", 0) / n
            if solid_ratio > 0.60:
                errors.append(f"표면: solid {solid_ratio:.0%} > 60% — 단색 과다는 "
                              f"다양성·창의성 부족이다 (§3.1). texture/gradient/photo로 분산하라")
            # 선언 비율 대비 편차 ±15%p
            for k, target in ratios.items():
                actual = counts.get(k, 0) / n
                if abs(actual - float(target)) > 0.15:
                    warnings.append(f"표면: {k} 선언 {float(target):.0%} vs 플랜 실측 "
                                    f"{actual:.0%} — 편차 15%p 초과, 디자인 시스템과 재정합하라")

    # F. constraints 동승
    if "constraints" not in plan:
        msg = ("constraints 필드 없음 — compliance·사용자 추가 지침이 "
               "아티팩트에 동승해야 유실되지 않는다 (agent-architecture.md §2)")
        (errors if strict else warnings).append(msg)

    return errors, warnings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    errors, warnings = check(args[0], strict="--strict" in sys.argv)

    if "--json" in sys.argv:
        print(json.dumps({"validated": not errors, "errors": errors,
                          "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"❌ {e}")
        for w in warnings:
            print(f"⚠️  {w}")
        print(f"\n{'✅ 게이트 통과 — HITL 승인으로' if not errors else '🚫 반려'} "
              f"(오류 {len(errors)}, 경고 {len(warnings)})")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

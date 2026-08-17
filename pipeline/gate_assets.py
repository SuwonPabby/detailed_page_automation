#!/usr/bin/env python3
"""gate_assets.py — Phase 0 ② asset 입력 게이트 (결정론)

설계 근거: docs/agent-architecture.md §1 Phase 0.
LLM 판단 이전에 코드가 먼저 판정한다. 이 게이트를 통과하지 못한 asset은
플랜 단계로 넘어갈 수 없다 (agentic-workflow.md Phase 0 ②).

검증 항목:
  1. 경로 실재 + 읽기 가능 + 이미지 확장자 + 용량 > 0
  2. 용도 선언 — '배경' | '참조' 둘 중 하나가 반드시 명시 (미선언 = 반려)
  3. 중복 경로 금지
  4. T2(증거성) 힌트 감지 — 제품컷·인증서 등은 AI 재생성 금지 플래그를 부착
     (docs/assets.md 3계층: 생성하면 위조)

매니페스트 형식 (에이전트가 Phase 0 문답으로 작성):
  {
    "product": "구스밀 주먹밥",
    "assets": [
      {"path": "data/assets/goosemeal/hero.png", "usage": "배경", "note": "훅 풀블리드"},
      {"path": "data/assets/goosemeal/mood.jpg", "usage": "참조", "note": "톤 참조만"}
    ]
  }

사용:
  python3 pipeline/gate_assets.py template > data/assets/<product>.manifest.json
  python3 pipeline/gate_assets.py check <manifest.json> [--json]
종료코드: 0 = Validated, 1 = 반려 (사유 출력)
"""
import json
import os
import sys

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}
USAGES = {"배경", "참조"}
# 제품 실물·증거성 자산 힌트 (gen_images.py PRODUCT_HINTS와 동일 계열 + 증거류)
T2_HINTS = ("제품컷", "실물", "라인업", "단면", "패키지", "인물", "모델",
            "인증", "특허", "성적서", "검사", "수상", "리뷰캡처")

TEMPLATE = {
    "product": "<제품명>",
    "assets": [
        {"path": "data/assets/<product>/<file>", "usage": "배경|참조", "note": "<용도 설명>"},
    ],
}


def check(manifest_path):
    errors, warnings, report = [], [], []
    try:
        with open(manifest_path) as f:
            m = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"매니페스트를 읽을 수 없음: {e}"], [], []

    assets = m.get("assets")
    if not isinstance(assets, list) or not assets:
        return ["`assets` 배열이 비어 있거나 없음"], [], []

    seen = set()
    for i, a in enumerate(assets):
        tag = f"assets[{i}]"
        path = a.get("path")
        if not path:
            errors.append(f"{tag}: `path` 없음")
            continue
        tag = f"{tag} {path}"

        if path in seen:
            errors.append(f"{tag}: 중복 경로")
            continue
        seen.add(path)

        usage = a.get("usage")
        if usage not in USAGES:
            errors.append(f"{tag}: 용도 미선언 — `usage`는 '배경'|'참조' 필수 "
                          f"(현재: {usage!r}). 추측으로 배치하지 않는다")

        if not os.path.isfile(path):
            errors.append(f"{tag}: 파일이 존재하지 않음")
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in IMAGE_EXTS:
            errors.append(f"{tag}: 이미지 확장자가 아님 ({ext})")
        size = os.path.getsize(path)
        if size == 0:
            errors.append(f"{tag}: 0바이트 파일")
        elif size < 30_000:
            warnings.append(f"{tag}: {size:,}B — 저해상 의심, 860px 폭 배치 전 확인")

        name = os.path.basename(path) + " " + (a.get("note") or "")
        t2 = any(h in name for h in T2_HINTS)
        report.append({"path": path, "usage": usage, "bytes": size,
                       "t2_no_regen": t2})
        if t2:
            warnings.append(f"{tag}: T2(증거성) 감지 — AI 재생성 절대 금지, 원본만 사용")

    return errors, warnings, report


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "template":
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2))
        return
    if len(sys.argv) < 3 or sys.argv[1] != "check":
        sys.exit(__doc__)

    errors, warnings, report = check(sys.argv[2])
    as_json = "--json" in sys.argv

    if as_json:
        print(json.dumps({"validated": not errors, "errors": errors,
                          "warnings": warnings, "assets": report},
                         ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"❌ {e}")
        for w in warnings:
            print(f"⚠️  {w}")
        print(f"\n{'✅ Validated' if not errors else '🚫 반려'} — "
              f"asset {len(report)}건, 오류 {len(errors)}, 경고 {len(warnings)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

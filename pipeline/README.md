# pipeline — Level 1 baseline 생성 파이프라인

기획안 xlsx → Figma 완성 상세페이지의 **baseline 구현**. 2026-08-09 구스밀 식물성 저당 주먹밥으로 첫 실행·검증 완료.

## 3단계 흐름

| 단계 | 수행 주체 | 입력 → 출력 |
|---|---|---|
| 1. 파싱 | `parse_brief.py` (기계적) | 기획안 xlsx → `data/briefs/<product>.json` — Main sheet 장면·카피·수정1/2·방어멘트, 사이드 테이블([Sx]/[Mx]), 배너, 부가 sheet 전체 |
| 2. 블록 플랜 | **에이전트(Claude) 판단** | brief → `data/briefs/<product>.plan.json` — 장면→scene_type→레이아웃 패턴 매핑, 최종 카피 확정, 배경 명도 리듬, 디자인 시스템 도출 |
| 3. Figma 빌드 | 에이전트 + `use_figma` | plan → 프로젝트 `636598794`에 새 파일, 블록 프레임 세로 스택 |

```bash
python3 pipeline/parse_brief.py <기획안.xlsx> data/briefs/<product>.json
```

## 단계 2에서 에이전트가 지켜야 할 것

- **카피 확정 규칙**: 기획안 L열(방어/거절 멘트)이 판정문이다 — `수용`이면 수정1/2 반영, `방어`면 원안 유지, `거절(규제)`면 대체 표현 사용. 규제 금지어(혈당·다이어트·비건·고단백 등)는 H열 코멘트를 따른다.
- 장면 분해는 [scene-taxonomy](../docs/analysis/scene-taxonomy.md), 레이아웃은 [layout-catalog](../docs/analysis/layout-catalog.md)에서 선택 — **인접 블록 동일 패턴 금지**, usp 연작은 근거 패턴을 매번 교체.
- 정량 기준은 [design-tokens §7](../docs/analysis/design-tokens.md): 헤드라인 70~100px / 본문 25~32px, 지배 hue 1개, 다크 블록 2~6개(훅·프리미엄·클로징), 연속 L 6개 금지.
- 폰트는 [fonts.md](../docs/fonts.md) 검증 목록만 (기본 Noto Sans KR + 임팩트 Black Han Sans).
- asset이 아직 없으면 **점선 placeholder 프레임**(`ASSET_<설명>`)으로 자리만 잡는다 — 기획안 I열(디자인가이드)의 문구를 라벨로.
- 카피의 수치가 sheet 간 불일치하면(구스밀: 갈비살 함량 3종, 불고기 kcal 2종) 임의로 고르지 말고 plan.json `copy_decisions`에 ⚠로 기록하고 보고한다.

## 단계 3 빌드 규약 (실전 검증됨)

- 루트: `createAutoLayout('VERTICAL', {itemSpacing:0})` 폭 860 고정 → 블록 프레임(`01_…`, `02_…`)을 순서대로 append. 블록은 세로 hug(`resize(860,·)` 후 `primaryAxisSizingMode='AUTO'`).
- 스크립트당 블록 2~3개(원자성 활용). 실패 시 파일 무변화 — 수정 후 재시도.
- ⚠ **비례 막대/고정폭 요소 함정**: `resize()` 후 `primaryAxisSizingMode='AUTO'`를 설정하면 폭이 콘텐츠 hug로 리셋된다. 비례를 표현하는 프레임은 반드시 `primaryAxisSizingMode='FIXED'` 유지 (첫 실행에서 실제로 발생, 사후 수정).
- 검증: 루트를 `get_screenshot(maxDimension=9000)`으로 받아 세로 분할 후 판독 → design-principles A~F 셀프 QA → 결함만 targeted 수정.

## 첫 실행 기록 (2026-08-09)

- 입력: `디자인23_기획안_구스밀_식물성저당주먹밥_v6.xlsx` (기획안 25행 + 사이드 테이블 10 + 컨셉/FAQ/리서치/경쟁사/줄글에세이)
- 출력: [바로끼니_식물성저당주먹밥_디자인23](https://www.figma.com/design/e4Nto2oOgqwbCcrI6Y4Btb) — 블록 22개, 총 20,111px, use_figma 10회(실패 2회 즉시 수정 포함)
- 플랜: `data/briefs/goosemeal-riceball.plan.json` (카피 판정 10건, ⚠수치 불일치 2건 포함)

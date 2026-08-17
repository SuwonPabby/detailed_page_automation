# 상세페이지 자동화 — 사용법 매뉴얼

버전 2026-08-15 · 브랜치 feat/pipeline-advancement 기준
설계 문서: docs/agentic-workflow.md(워크플로우) · docs/agent-architecture.md(에이전트 구성)

## 1. 이 시스템이 하는 일

기획안 엑셀 하나를 넣으면, Figma에 한국 이커머스 상세페이지 완성본을 만든다.
모든 단계는 4대 원칙을 기준으로 판정된다.

- P1. AI가 만든 티가 나지 않는다 — 최종 판정 기준
- P2. 정해진 템플릿을 최대한 활용한다 — 커스텀은 사유 있는 예외
- P3. 주어진 asset을 최대한 활용한다 — 생성보다 주입이 먼저
- P4. 부족한 이미지는 Higgsfield로 생성한다 — 단 P1·compliance 게이트 통과분만

진행 순서: 입력 게이트(Phase 0) → 파싱 → 디자인시스템+레이아웃 플랜 → [사용자 승인] →
부품 준비 → 조립 → 검수 루프(최대 4라운드) → 납품.

## 2. 사전 준비 (최초 1회)

1. Figma 토큰: 메인 워크트리의 .env에 FIGMA_API_KEY가 있어야 한다.
   (형식 특성상 shell source로 읽으면 깨진다 — 스크립트가 알아서 파싱한다)
2. Higgsfield MCP 인증: 대화형 세션에서 /mcp 또는 claude mcp login higgsfield.
   미인증이면 3단계(부품 생성)에서 멈추고 인증을 요청하게 된다.
3. Figma MCP: 공식 Figma MCP가 연결돼 있어야 한다 (쓰기는 전부 MCP 경유).
4. Python 의존성: openpyxl (파싱), fpdf2 (매뉴얼 PDF 재생성 시).
5. 쓰기 허용 Figma 공간은 프로젝트 detailed_page_automation (projectId 636598794) 하나뿐이다.
   레퍼런스 Full_design은 읽기 전용 — 절대 수정되지 않는다.

## 3. 실행 방법

Claude Code 세션에서:

    /detail-page
    또는: "이 기획안으로 상세페이지 만들어줘: <기획안.xlsx 경로>"

호출하면 시스템이 바로 작업을 시작하지 않고, 아래 Phase 0 문답을 먼저 진행한다.

## 4. Phase 0 — 시스템이 묻는 것과 답하는 법

### 질문 1. "기획서를 주세요"

기획안 xlsx 경로를 준다. 양식은 디자인23 기준(Main sheet '기획안', L열이 카피 판정문).
파싱이 실패하면 무엇이 안 읽히는지 알려주니 해당 셀을 고쳐 다시 주면 된다.

### 질문 2. "꼭 사용해야 하는 asset이 있나요?"

있다면 파일 경로와 함께 용도를 반드시 말해준다. 용도는 둘 중 하나다.

- 배경: 페이지에 직접 깔리는 소재 (제품컷, 촬영 이미지 등)
- 참조: 스타일·톤만 참고, 직접 배치하지 않는 소재

시스템이 매니페스트(json)를 만들어 gate_assets.py로 검증한다. 용도가 없거나
경로가 틀리면 반려되고 다시 묻는다. 제품 실물컷·인증서 같은 증거성(T2) 파일은
자동 감지되어 "AI 재생성 금지" 플래그가 붙는다 — 이런 건 반드시 원본을 줘야 한다.

### 질문 3. "추가로 유념할 사항이 있나요?"

자유롭게 서술하면 된다. 모호한 부분은 시스템이 되물어서 확정한다.
확정된 내용은 constraints로 기록되어 모든 후속 단계에 그대로 전달된다.

## 5. 진행 중 사용자가 개입하는 지점 (HITL)

개입 지점은 의도적으로 적게 설계돼 있다. 아래 네 경우에만 시스템이 멈추고 기다린다.

| 시점 | 무엇을 하는가 |
|---|---|
| 플랜 승인 | 레이아웃 플랜 전체를 한 번에 보여준다. 고칠 부분을 말하면 반영 후 재제시. 승인하면 플랜은 동결되고 이후 임의 변경되지 않는다 |
| 미결 이슈 확정 | 기획안 수치가 sheet끼리 충돌하면 시스템이 임의로 고르지 않고 물어본다 |
| T2 asset 주입 | 제품컷·인증서 등이 필요한 슬롯은 원본 파일을 요청한다 |
| 에스컬레이션 | 부품 재생성 3회 실패, 또는 같은 결함 2라운드 연속 시 판단을 요청한다 |

플랜 승인이 가장 중요한 개입이다. 여기서 고치는 것이 가장 싸다 —
조립 후에 고치면 라운드를 소모한다.

## 6. 검수 기준 — 무엇이 PASS인가

- 실격 공리 F1~F10 위반 0건 (하나라도 걸리면 점수 무관 FAIL)
- compliance(법적 게이트) 위반 0건 — craft보다 상위
- 점수 80/100 이상. 점수는 인상이 아니라 이진 체크리스트의 산술 합산이다
- 안정 도달: 축별 후퇴 없이 2라운드 연속 점수 변화가 3점 미만

검수는 두 에이전트가 독립으로 본다: detail-page-reviewer(채점·처방)와
red-team-auditor(실격·compliance 위반만 사냥). red-team의 위반 1건 = 즉시 FAIL.
라운드는 최대 4회 — 그 안에 안 되면 루프를 더 돌리지 않고 원인을 설계로 회송한다.

## 7. 산출물

| 산출물 | 위치 |
|---|---|
| 상세페이지 | Figma 프로젝트 636598794, 파일명 <브랜드>_<제품>_<기획안번호> |
| 파싱 결과 | data/briefs/<product>.json |
| 플랜 | data/briefs/<product>.plan.json (git 커밋 대상) |
| asset 매니페스트 | data/assets/<product>.manifest.json |
| 생성 부품 | data/assets/<fileKey>/ |

재시도 버전은 같은 Figma 파일 안의 새 페이지로 쌓인다 (v2 — craft 식 이름).
Figma 산출물 자체는 저장소에 커밋하지 않는다.

## 8. 명령어 치트시트 (수동 실행·디버깅용)

    # 기획안 파싱
    python3 pipeline/parse_brief.py <기획안.xlsx> data/briefs/<product>.json

    # asset 매니페스트 틀 만들기 / 검증
    python3 pipeline/gate_assets.py template > data/assets/<product>.manifest.json
    python3 pipeline/gate_assets.py check data/assets/<product>.manifest.json

    # 플랜 게이트 (스키마·traceability·리듬·인접패턴·미결이슈)
    python3 pipeline/gate_plan.py data/briefs/<product>.plan.json

    # 빌드 후 결정론 검사 + 법적 사이드카
    python3 pipeline/qa_check.py <fileKey> <rootNodeId>
    python3 pipeline/export_text.py <fileKey> <rootNodeId>

    # 매뉴얼 PDF 재생성
    python3 scripts/md2pdf.py docs/manual/usage-manual.md docs/manual/usage-manual.pdf

## 9. 자주 겪는 문제

| 증상 | 원인·대처 |
|---|---|
| gate_assets 반려: 용도 미선언 | 매니페스트의 usage를 '배경' 또는 '참조'로 채운다 |
| gate_plan 반려: traceability | 기획안 장면이 플랜에서 누락 — 블록에 scenes 필드를 채우거나 skipped_scenes에 사유를 적는다 |
| gate_plan 반려: 미결 이슈 | 수치 충돌을 사용자가 확정해야 한다. 확정 후 open_issues_ack: true |
| Higgsfield 도구가 없다 | MCP 미인증. 대화형 세션에서 /mcp로 인증 |
| 폰트 로딩 실패 | docs/fonts.md의 검증 목록만 사용 가능. Pretendard·SUIT는 Figma 클라우드에 없다 |
| use_figma 실패 반복 | 원자적이라 파일은 무변화. 에러 메시지를 읽고 스크립트를 고쳐 재시도 |
| 점수가 전 라운드보다 하락 | 정상이다. 수정이 새 결함을 만들었고 검수자가 잡은 것 |

## 10. 절대 하지 않는 것 (시스템의 하드 제약)

- Full_design 등 허용 프로젝트 외 Figma 공간에 쓰기
- T2(증거성) 이미지의 AI 생성 — 위조다
- compliance RED 표현 사용 (외국어 우회 포함)
- 통과를 위해 검수 규칙을 완화
- 승인된 플랜에서의 임의 이탈

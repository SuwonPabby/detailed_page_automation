# docs — detailed_page_automation

이 폴더는 **사람과 AI 에이전트 모두**가 읽는 프로젝트 기준 문서입니다.
Claude 외 다른 에이전트도 이 폴더만 읽고 작업을 시작할 수 있도록 작성되었습니다.

## 읽는 순서

| # | 문서 | 무엇이 적혀 있나 | 언제 읽나 |
|---|---|---|---|
| 1 | **[rules.md](./rules.md)** | 하드 제약. 쓰기 경계, 금지 사항 | **작업 시작 전 필수** |
| 2 | [project-overview.md](./project-overview.md) | 프로젝트 목표, 기존 워크플로우, Level 1/2 자동화 범위 | 맥락 파악 |
| 3 | [figma-spaces.md](./figma-spaces.md) | 두 Figma 공간의 구조와 노드 ID 인벤토리 | Figma를 다룰 때 |
| 4 | [design-principles.md](./design-principles.md) | Good/Bad 레퍼런스에서 추출한 디자인 판단 기준 | 페이지를 생성/평가할 때 |
| 5 | [fonts.md](./fonts.md) | 검증된 한글 폰트 목록·권장 조합·레퍼런스 폰트 치환 정책 | 텍스트를 만들 때 |
| 6 | [analysis/README.md](./analysis/README.md) | 분석 산출물 지도 + 생성 단계별 로드 규약 | **페이지를 생성할 때** |
| 7 | [analysis/scene-taxonomy.md](./analysis/scene-taxonomy.md) | 장면 유형 어휘 + 서사 시퀀스 | 기획안을 장면으로 분해할 때 |
| 8 | [analysis/layout-catalog.md](./analysis/layout-catalog.md) | 레이아웃 패턴 38종 + anti-pattern | 장면별 레이아웃 고를 때 |
| 9 | [analysis/design-tokens.md](./analysis/design-tokens.md) | 실측 폰트 스케일·팔레트·배경 리듬 + 생성 규칙 | 스타일 적용할 때 |
| 10 | ⭐ **[analysis/craft-axioms.md](./analysis/craft-axioms.md)** | "사람이 만든 것처럼 보이는" 조건의 공리계 + 실격 공리 F1~F10 + 판정 루브릭 | **페이지를 생성·검수할 때 (필수)** |
| 11 | 🔴 **[compliance.md](./compliance.md)** | 표시·광고 법적 하드 게이트 (식약처 고시·공정위 예규 1차 출처). craft보다 상위 | **카피를 확정할 때 (필수)** |

## 자동화 진입점

| 경로 | 무엇 |
|---|---|
| `.claude/skills/detail-page/SKILL.md` | 기획안 → Figma 전 과정 스킬 (파싱→플랜→빌드→검수 루프) |
| `.claude/agents/detail-page-reviewer.md` | 공리계로 채점하는 검수자 에이전트 (80점+실격0 통과) |
| `pipeline/parse_brief.py` | 기획안 xlsx → brief.json |

## 한 줄 요약

기획안 xlsx → (이 저장소가 제공하는 harness) → Figma에 완성된 상세페이지.
**이 저장소는 페이지 생성기가 아니라, 생성기를 구동하는 Claude Code harness**(tool / MCP / 프롬프트 / skill)입니다.

## 문서 상태

작성 기준일 **2026-08-08**. 아직 구현 단계 이전이며, 현재까지 확정된 사실과 미해결 항목만 담고 있습니다.
미해결 항목은 [rules.md의 "미해결" 절](./rules.md#미해결-확정-필요)에 모아두었습니다.

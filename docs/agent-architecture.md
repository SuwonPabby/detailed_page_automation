# Agent Architecture — agentic-workflow.md를 구현하는 에이전트 구성

[agentic-workflow.md](agentic-workflow.md)의 요구사항을 2024–2026 agentic 연구를 근거로 에이전트 구성으로 변환한 전략 문서.
리서치 전문은 세 갈래로 수행: ① 멀티에이전트 오케스트레이션 ② 생성자-비평자 루프 ③ 디자인 생성 시스템 사례.

## 0. 총괄 결론 — 에이전트를 늘리지 말고, 게이트를 코드로 짜라

문헌이 가장 강하게 말하는 것 세 가지:

1. **단계가 미리 알려진 파이프라인은 오케스트레이터 "에이전트"가 아니라 코드로 짠 상태머신이 이긴다.**
   StateFlow(COLM 2024): FSM 제약만으로 성공률 +13~28%, 비용 3~5배 절감.
   통제 실험(arXiv 2606.05670, 2026): 도구·프로토콜을 동일하게 맞추면 멀티에이전트 6개 중 5개가 단일 에이전트보다 **못함**.
   멀티에이전트 실패 200건 분석(MAST, 2025): 실패의 대부분은 모델 능력이 아니라 **역할 명세 부실과 검증 부재**.
2. **핸드오프는 대화가 아니라 타입 있는 아티팩트다.** MetaGPT(ICLR 2024)의 SOP 패턴 — 각 단계는 구조화 문서를 내고 다음 단계가 그것을 검증 후 소비. LLM 홉마다 패러프레이즈하면 왜곡이 누적된다(ACL 2025 "Broken Telephone") — 카피·수치·법적 문구는 **verbatim 필드로 전달**.
3. **비평자는 외부 근거로만.** 자기 출력 재독형 자기교정은 성능을 깎는다(ICLR 2024). 렌더 스크린샷 + 결정론 체커 출력이 근거인 우리 기존 reviewer 구조가 정확히 문헌의 정답 형태다.

따라서 전략은 "에이전트 군단"이 아니다:
**코드 FSM(스킬 본문 + pipeline/*.py 게이트) 위에, 구조적 이유가 있는 자리에만 에이전트 6종.**

```
[코드 레이어]  SKILL.md의 FSM + parse_brief / qa_check / export_text / transplant / 신규 gate 스크립트
[에이전트]     ①메인(컨트롤러+플래너+빌더) ②asset-worker×N(병렬) ③asset-validator
              ④detail-page-reviewer(기존, 업그레이드) ⑤red-team-auditor(신규) ⑥style-explorer(필수)
[사람]        HITL 게이트 2개: 플랜 승인(편집형) · T2 에셋 주입/최종 납품 확인
```

---

## 1. 단계별 구성

### Phase 0 — Input 게이트: 에이전트 없음, 코드가 판정

- 기획서: `parse_brief.py`가 판정자. 파싱 실패 항목을 **구체적으로 명시**해서 되물음
- asset: 경로 실재·용량은 스크립트(`gate_assets.py` 신규), **용도(배경/참조) 미선언 시 반려**는 규칙으로
- 추가 지침: 메인 에이전트가 모호성 되묻기 → 확정문을 `constraints` 필드에 고정

근거: UCAgent(2026) 등 2026 패턴 — **결정론 게이트가 먼저, LLM 판단은 그 뒤**. LLM이 할 일은 "무엇이 왜 안 읽히는지 설명"뿐이다.

HITL 원칙(HULA·ICSE 2025, Oversight-capacity 2026): 게이트는 **적고, 배치형이고, 편집 가능**해야 한다. Phase 0에서는 실패 시에만 사람을 부른다(escalation-triggered).

### 1~2단계 — Design System + Layout Plan: 메인 에이전트 하나가 연속 컨텍스트로

**별도 "플래너 에이전트"를 만들지 않는다.** 근거:

- Cognition(2025) "Don't Build Multi-Agents": 디자인 일관성(한 페이지의 한 목소리)은 "병렬 에이전트들의 암묵적 결정 충돌"이 정확히 망가뜨리는 지점. 토큰 결정과 레이아웃 결정은 강결합 → 한 컨텍스트
- 디자인 생성 문헌 전체(COLE→PosterGen→CreatiPoster)가 수렴한 순서: **콘텐츠 → 전역 스타일 1회 결정 → 레이아웃 spec → 에셋 → 조립**. 스타일은 전역에서 한 번, 요소별로 다시 정하지 않는다

메인 에이전트가 하는 일:

1. 카피 확정(L열 판정문, compliance 게이트) → 토큰 시트(1단계 산출물: font/color/**surface 비율 선언**)
2. **템플릿 검색 → 슬롯 채우기** (P2): RALF(CVPR 2024)·CAL-RAG(2025) — 검색 기반이 자유 생성을 신뢰도에서 압도. `blocks.json` 38패턴이 이미 검색 코퍼스다. 장면 taxonomy → 패턴 검색 → 변형
3. 산출: `plan.json` — 블록별 {템플릿 ID, 카피 verbatim, asset 슬롯(주어진 것/생성할 것), 리듬 시퀀스, constraints}

플랜 게이트(코드): 스키마 검증 + **traceability 검사** — 기획안의 모든 장면 ID가 플랜에 등장하는가. MAST(2025)에서 최대 실패 계급이 "정보를 조용히 떨어뜨림"이었다. 소비 검증은 생산 검증만큼 중요하다.

**HITL 게이트 B(최고 레버리지)**: 플랜 전체를 한 번에, 편집 가능한 형태로 승인받는다. HULA(ICSE 2025): 플랜 승인 게이트가 하류 재작업을 가장 싸게 막는 지점(플랜 승인율 82%). **승인된 플랜은 동결** — 조립 중 이탈 금지(arXiv 2509.08646: 동결된 플랜 = 감사 가능한 계약).

### 3단계 — Asset 준비: 병렬 worker + 이진 검증자

여기가 **유일하게 병렬 멀티에이전트가 근거 있는 자리**다(Anthropic 2025: 멀티에이전트는 독립·병렬 가능한 작업에서만 이김. 에셋 생성은 spec으로 완전 결정되는 독립 작업).

- **asset-worker × N**: plan.json의 생성 목록을 DAG로 컴파일(LLMCompiler 2024)해 병렬 실행. 각 worker 브리프는 {목표, 출력 스키마, 경계} 완비
- **P1 방어를 프롬프트 레벨에 내장**: 2025–26 실무 합의 —
  - 하우스 "포토그래피 접미사": 필름 스톡(Portra 400), 렌즈·조명 방향, **의도적 불완전성**(grain, 톤 변화) 명시. "8k/masterpiece/flawless" 금지
  - 생성은 배경·환경까지만, **제품·손·얼굴은 실물 유지**(T2) — 사람이 위조를 가장 빨리 감지하는 곳
  - 후처리 그레이드(grain/LUT)로 T1을 실물 사진 옆에 톤 정합
  - 재생성보다 `remove_background`/`outpaint` 등 **편집 도구 우선** (subject-consistent editing이 2025–26 표준)
- **asset-validator**: 부품별 **이진 체크리스트**(스펙 일치? AI 티 나는 요소? 텍스트 영역 비움?) 판정. 홀리스틱 점수 금지(§2.2 참조). 불합격 → 재생성, 상한 3회 → 사람 에스컬레이션
- T2는 검증 대상이 아니라 **주입 게이트**: 사람만 공급한다 (HITL이되 승인이 아니라 provisioning)

배경 생성은 **레이아웃 확정 후**: CreatiPoster(2025) — 전경(텍스트 존)을 조건으로 배경을 생성해야 텍스트 자리가 비워진 이미지가 나온다. 2-2에서 슬롯별 텍스트 존을 spec에 적고, worker 프롬프트에 negative space 지시로 전달.

### 4단계 — 조립 + 검수 루프: 빌더(메인) ↔ 검수자(격리) + red-team

**빌더 = 메인 에이전트 연속 컨텍스트.** 동결된 plan.json을 실행만 한다. Figma API 에러에는 반응하되 설계 이탈은 금지 — 이탈 필요 시 리플랜으로 회송.
LaDeCo(CVPR 2025)·Graphist(AAAI 2025): **이전 블록들의 렌더를 컨텍스트에 두고 위→아래 순차 조립**이 전 속성 일괄 예측을 이긴다. 블록 2~3개 빌드마다 스크린샷을 찍어 이어간다.

**검수자 = 기존 `detail-page-reviewer` + 문헌 기반 업그레이드 5개:**

| # | 변경 | 근거 |
|---|---|---|
| R1 | 루브릭을 **이미지로 검증 가능한 이진 항목의 합산**으로 재구성. 홀리스틱 80점 단독 게이트 폐지 | VLM judge는 순위는 정확, 절대점수는 구간 노이즈 ~40%(arXiv 2604.25235, 2026). Rubrics-as-Rewards(2025): 체크리스트형이 홀리스틱 대비 +31% |
| R2 | **pairwise 보조 신호**: "이번 라운드가 지난 라운드보다 나은가(축별로)". 통과 = 이진 게이트 전부 green + 순위 개선 정체(stability) | 랭킹이 VLM의 실제 강점. 정지 조건은 "80 돌파"가 아니라 "안정 + 게이트 green" |
| R3 | **빌더의 자기설명을 검수자 입력에서 제거.** 스크린샷 + 루브릭 + qa_check 출력만. 측정형 주장 검증용으로만 압축 node spec 허용 | informativeness bias(2026): VLM이 픽셀 대신 딸린 텍스트로 채점. self-certification이 최다 문서화된 루브릭 해킹(2026) |
| R4 | **반론 채널 금지**: 빌더는 지적 리스트를 받기만 한다. 협상 없음 | 2025 debate 문헌: 설득에 검수자가 굴복하는 실패(correct→incorrect 플립이 역방향보다 많음) |
| R5 | 모든 감점에 **위치(블록명/node ID) 필수** — 이미 하고 있음, 유지 | 로컬라이제이션이 grounding 강제 장치(Google 2024; AesEval 2026) |

**red-team-auditor (신규, 경량)**: 실격 공리 + compliance **위반만 찾는** 비대칭 패스. 점수를 올릴 수 없고 내릴 수만 있다. 검수자와 독립 실행, 합의 금지(deliberation은 편향을 증폭 — 2025).
GAN식 풀 debate는 **채택하지 않는다** — 문헌이 기각(3단원 리서치 §3).

**루프 규율(기존 4규율 유지 + 추가 3):**

- **라운드 상한 3~4.** 그 이상은 노이즈에 지불(Self-Refine 계열 합의: 1~2라운드에 이득 집중). 상한 도달 시 루프가 아니라 **공리/템플릿(생성자 prior)을 고친다** — v2 6라운드 → v3 1라운드가 된 이유가 바로 prior 개선이었다
- **동일 결함 2라운드 연속 실패 → 조립 반복이 아니라 레이아웃 리플랜으로 에스컬레이션** (Magentic-One 2024의 stall counter)
- **라운드 메모리**: 이전 지적·수정 이력을 유지, 이미 통과한 항목의 회귀는 명시 플래그 (Idea2Img 2023 — 실패 방향 재탐색 방지). 후속 라운드는 변경 영역 + 실격 게이트만 재검(전량 재채점은 점수 churn만 추가)

### style-explorer — 필수 단계 (2026-08-17 승격: 입력 독립성)

MIMO(2025)·판넬 합의: 1단계에서 **스타일 방향 2~3개(물성 세계관+팔레트+표면 후보)를 병렬 생성 → 대표 블록 1개씩 시안 → 선택(사용자 HITL 또는 pairwise 랭킹)** 후 진행.
**선택→필수 승격 사유**: 발산 단계가 없으면 단일 에이전트는 자기 분포의 중앙값으로 수렴해 **모든 입력이 같은 지문**을 갖는다 (v3~v6 실증 + research-anti-ai "중앙값 수렴"). 다양성은 취향이 아니라 입력 독립성의 구조적 보장 장치다.

---

## 2. 에이전트 명세 요약

| 에이전트 | 정체 | 모델 | 컨텍스트 | 입력 | 출력 |
|---|---|---|---|---|---|
| 메인 (컨트롤러+플래너+빌더) | 스킬 본문 | 세션 모델 | 연속 1개 | 기획안, 게이트 결과, 검수 리포트 | plan.json, Figma 빌드 |
| asset-worker ×N | Task 서브에이전트 | sonnet급 | 격리·병렬 | 슬롯 spec 1건 (완전 결정) | 에셋 파일 + 메타 |
| asset-validator | Task 서브에이전트 | 세션 모델 | 격리 | 에셋 + 이진 체크리스트 | pass/fail + 사유 |
| detail-page-reviewer | 기존 정의 + R1~R5 | opus (유지) | 격리 | 렌더 + qa_check 출력 + 루브릭 | 구조화 지적 리스트 |
| red-team-auditor | 신규 경량 정의 | 세션 모델 | 격리·검수자와 독립 | 렌더 + 실격 공리 + compliance | 위반 목록 (감점 전용) |
| style-explorer (필수) | Task 서브에이전트 ×2~3 | sonnet급 | 격리·병렬 | 토큰 후보 방향 | 방향별 샘플 블록 |

**아티팩트 규약** (모든 핸드오프 공통):

- 카피·수치·인증번호는 **verbatim 필드** — 어떤 에이전트도 패러프레이즈 금지
- `constraints` 필드가 모든 아티팩트에 동승 (compliance·공리·사용자 추가 지침) — 요약에 유실되지 않도록 전용 필드
- 서브에이전트는 **추론 트랜스크립트가 아니라 구조화 결과만 반환** (컨트롤러 컨텍스트 오염 방지 — Anthropic 2025)

---

## 3. 지금과의 차분 (구현 순서)

현 스킬은 "메인이 다 하고 검수자 하나가 루프"다. 격차는:

1. **Phase 0 게이트 신설** — `gate_assets.py` + 스킬 본문에 input 문답 절차 (신규)
2. **플랜 게이트** — plan.json 스키마 + traceability 검사 스크립트 + HITL 편집형 승인 절차 (신규)
3. **검수자 업그레이드 R1~R5** — 루브릭 이진화가 가장 큰 공사 (craft-axioms §7을 체크리스트로 재서술)
4. **red-team-auditor 정의** (신규, 작음)
5. **3단계 병렬화** — gen_images.py를 DAG 실행형으로, 포토그래피 접미사·후처리 그레이드 내장
6. **루프 규율 확장** — 라운드 상한·stall 에스컬레이션·라운드 메모리를 SKILL.md에 명문화
7. style-explorer (필수 — 입력 독립성 장치)

1→2→3이 레버리지 순서다. 1·2는 코드가 대부분이고, 3이 품질에 직결된다.

---

## 4. 리서치 출처 (요약)

오케스트레이션: Anthropic Building Effective Agents(2024)·multi-agent research system(2025) / StateFlow(COLM 2024) / MAST(arXiv 2503.13657) / MetaGPT(ICLR 2024) / Magentic-One(2024) / LLMCompiler(ICML 2024) / HULA(ICSE 2025) / Cognition "Don't Build Multi-Agents"(2025) / Broken Telephone(ACL 2025)
비평 루프: LLMs Cannot Self-Correct(ICLR 2024) / Kamoi TACL 2024 / VLM Judges Rank-not-Score(2026) / WebDevJudge(2025) / Rubrics as Rewards(2025) / One Token to Fool(2025) / rubric reward-hacking(2026) / Reflect-DiT(ICCV 2025) / Idea2Img(ECCV 2024)
디자인 생성: COLE(2024) / BannerAgency(EMNLP 2025 — Figma 편집형 출력의 직접 선례) / MIMO(2025) / PosterGen(2025) / CreatiPoster(2025) / RALF(CVPR 2024) / CAL-RAG(2025) / LaDeCo(CVPR 2025) / AesEval-Bench(2026) / PosterReward(CVPR 2026)

※ 2026 arXiv ID(26xx.x)는 미査読 프리프린트. 세부 수치는 방향성 근거로만 취급.

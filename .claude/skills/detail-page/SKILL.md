---
name: detail-page
description: 기획안 xlsx로부터 Figma에 한국 이커머스 상세페이지를 생성한다. 기획안 파싱 → 장면·레이아웃 플랜 → 공리계(craft-axioms) 기반 빌드 → 검수자 에이전트 루프. "상세페이지 만들어", "기획안으로 페이지 생성", "디자인23 작업" 등에 호출.
---

# detail-page — 상세페이지 생성 스킬

기획안 엑셀 하나로 Figma에 완성된 상세페이지를 만든다.
**이 스킬의 핵심 주장: 구조만 맞추면 와이어프레임이 나온다.** 사람이 만든 것처럼 보이게 하는 것은 §3의 공리계다.

## 0. 하드 제약 (위반 금지)

- 쓰기가 허용된 Figma 공간은 **프로젝트 `detailed_page_automation` (projectId `636598794`)** 뿐이다. `create_new_file`에 `projectId`를 **반드시** 명시한다(생략 시 Drafts로 떨어짐 = 위반).
- 레퍼런스 `Full_design`(`jjgud5OkeXKA4weyP3FEND`)은 **읽기 전용**. 렌더·조회만 한다.
- **Figma에는 파일 삭제 API가 없다.** 시험 삼아 파일을 만들지 말 것. 반복 작업은 **기존 파일 안에서 새 페이지**(`figma.createPage()`)로 한다.
- 전체 규칙 → `docs/rules.md`

## 1. 입력 — Phase 0 게이트 (docs/agentic-workflow.md Phase 0)

**스킬이 호출되면 바로 작업을 시작하지 않는다.** 입력 검증은 **2레이어**이며 둘 다 통과해야
§2로 넘어간다. 판정은 코드가 먼저, LLM은 설명만.

**레이어 0 — config 접근성 검증 (사람 관할 config가 전부 사용 가능한가):**

```bash
# 폰트는 REST로 못 보므로 먼저 use_figma로 허용 목록 존재 확인 →
#   config/fonts.json의 allowed를 스크립트에 넣어 present/missing 반환 → present를
#   [{family,style}] 형식으로 /tmp/figma_fonts.json 저장
python3 pipeline/gate_config.py --fonts /tmp/figma_fonts.json
# 검증: 템플릿 파일 접근 · 레퍼런스 접근 · 폰트 전수 사용 가능 · compliance 문서 · 플랫폼 규격
```

config는 `config/` 아래 5개(templates·fonts·references·compliance·platform) — **사람 관할,
AI 수정 금지.** 하나라도 접근 불가면 진행 금지 (예: 템플릿 파일 권한 소실, 폰트 목록의 서체가
Figma 클라우드에서 사라짐).

**레이어 1 — 입력물 검증:**

| # | 입력 | 게이트 | 실패 시 |
|---|---|---|---|
| ① | 기획안 xlsx (필수) | `parse_brief.py`가 파싱 성공 | 무엇이 왜 안 읽히는지 명시하고 재요청 |
| ② | 필수 사용 asset | 매니페스트 작성 → `gate_assets.py check` 통과 | 반려 사유 전달, 재요청 |
| ③ | 추가 지침 / advise | 모호한 지점을 **되물어 확정** | 확정될 때까지 진행 금지 |

- ② **T2 요청 체크리스트** (gap-v6 ⓒ 7건 대응 — 능동적으로 요청하라, 조용히 생략하지 마라):
  실존 리뷰 캡처(별점·닉네임 마스킹) / 인증·특허증 스캔 / 계약 모델 컷 **다포즈**(1포즈면 반복 사용 불가) /
  **제품 대표컷 1장 지정**(나머지 제품컷의 외형 일관성 판정 기준). 미제공 항목은 plan.json에
  `t2_missing: [...]`로 기록하고 해당 장면 생략을 **명시적 결정**으로 남긴다
- ② 절차: "이 기획에서 꼭 써야 하는 asset이 있는가?"를 묻고, 있으면
  `python3 pipeline/gate_assets.py template`으로 매니페스트 틀을 만들어 경로·**용도(배경/참조)**·note를
  받아 적은 뒤 `check`를 돌린다. **용도 미선언 asset은 추측으로 배치하지 않는다** — 게이트가 반려한다.
  T2(증거성) 플래그가 뜬 asset은 AI 재생성 절대 금지, 원본 주입만.
- ③에서 확정된 지침은 plan.json의 **`constraints` 필드에 verbatim으로 기록**한다.
  이 필드는 이후 모든 아티팩트·서브에이전트 브리프에 동승한다 (요약 유실 방지).
- asset이 없으면: designed placeholder로 자리만 확보 (§3 §5). **에셋은 3계층** —
  T0 절차생성/T1 AI생성/T2 주입필수(증거) → `docs/assets.md`
- 디자인 시스템 입력이 없으면 §4로 도출, 출력 Figma 링크가 없으면 프로젝트에 새 파일 생성.

## 2. 파이프라인 (Phase 0 입력게이트 → 파싱 → 플랜+HITL → 부품 → 조립 → 검수 루프)

전체 설계와 근거: `docs/agentic-workflow.md`(요구사항) · `docs/agent-architecture.md`(에이전트 구성).

### 2-1. 파싱 (기계적)

```bash
python3 pipeline/parse_brief.py <기획안.xlsx> data/briefs/<product>.json
```

기획안 양식(디자인23 기준): Main sheet `기획안` — B=섹션그룹 C=# D=섹션명 E=구분 F=카피초안 G=기획 H=추가코멘트 I=디자인가이드 J=수정1 K=수정2 **L=방어/거절 멘트**, M~P=사이드 데이터 테이블(`[S0]`/`[M1]` 앵커). 부가 sheet: 리서치·경쟁사·컨셉·줄글에세이·FAQ.

### 2-2. 플랜 (에이전트 판단) → `data/briefs/<product>.plan.json`

**🔴 카피 확정 0단계 — 법적 게이트 먼저.** `docs/compliance.md`의 RED 블랙리스트를 통과하지 못한 표현은 기획안에 있어도 쓰지 않는다(식품 질병·의약품 오인은 10년/1억). **외국어 우회 무효**, **`특허 보유`는 효능 근거가 아님**, `슈퍼푸드`·`디톡스`·`면역력 강화`·`무MSG` 등은 명시 금지. 기획안 원안이 RED에 걸리면 **임의로 고치지 말고 기획자에게 보고**한다.

**카피 확정 — L열이 판정문이다:**
| L열 | 처리 |
|---|---|
| `수용` | 수정1/2 반영 |
| `방어` | 원안 유지 (기획자가 이미 방어 논리를 썼다) |
| `거절(규제)` | 대체 표현 사용. H열의 금지어 지시를 따른다 |
| 판정문 없음 | 원안 유지. **새 표현을 창작하지 않는다** |

**수치가 sheet 간 충돌하면 임의로 고르지 말고** `copy_decisions`에 ⚠로 기록하고 사용자에게 보고한다.

**🎯 클레임 서열 → 시각 자원 배분 (카피 확정 직후, 레이아웃 전에 — craft-axioms §9 U2):**
디자이너는 규칙을 더 잘 지키는 게 아니라 **어디에 물량을 쏟을지 먼저 정한다** (gap-v6-vs-designer).

```json
"claims": [{"rank":1, "claim":"저당(대체당)", "scenes":[12], "evidence":["선언타이포","기준치차트","시즐컷"]}, ...],
"blocks": [{..., "emphasis":"climax|normal|breather|notice", "asset_budget":"hero|full|standard|minimal"}]
```

- **rank 1 클레임 = climax 블록** — 페이지 최장 + 평균×1.8↑ + 증거 유형 ≥3종 적층 + asset_budget `hero`
  (이미지 ≥2장·커버리지 ≥50%). v6의 실패("1순위 클레임인 당류 블록에 이미지 0장")를 구조로 차단
- emphasis별 패딩 배수: climax 1.7 / normal 1.0 / breather 0.6 / notice 0.65 (F7을 설계에서 해결)
- 같은 수치가 2개 이상 장면의 주요 증거로 배정되면 거부 (v6: 08↔11이 37.81% 중복)

**장면 → 레이아웃:** `docs/analysis/scene-taxonomy.md`(19종 통제 어휘) → `docs/analysis/layout-catalog.md`(38패턴). 인접 블록 동일 패턴 금지. usp 연작은 **근거 패턴을 매번 교체**.

**리듬 설계:** 배경 L/M/D 시퀀스를 미리 문자열로 적는다. 다크 2~6개(훅·프리미엄·신뢰·클라이맥스·클로징), 연속 L 6개 금지. **클라이맥스 블록 1~2개**를 지정한다.

**플랜 게이트 + HITL 승인 (신규 — docs/agent-architecture.md §1 2단계):**

- 각 블록에 **`scenes: [기획안 장면 번호]`** 필드를 반드시 채운다. 의도적으로 뺀 장면은
  `skipped_scenes: {"7": "사유"}`로 명시한다. 소비 검증(traceability)은 게이트가 한다.
- 배경/장식 슬롯에는 **텍스트 존**(비워야 할 영역)을 spec에 적는다 — 3단계 생성 프롬프트의 재료다.
- `python3 pipeline/gate_plan.py <plan.json>` 통과 후, **플랜 전체를 사용자에게 한 번에
  편집 가능한 형태로 제시해 승인받는다** (배치형 HITL — 블록별 찔끔 승인 금지).
- **승인된 플랜은 동결이다.** 빌드 중 이탈 금지. 이탈이 필요해지면 빌드를 멈추고
  플랜 수정 → 게이트 → 재승인으로 돌아온다.

### 2-2.5. 부품 준비 (조립 전에 부품을 다 만든다)

plan.json의 AI 생성 슬롯 목록이 작업지시서다. 슬롯끼리는 독립이므로 **병렬로** 생성한다.

- provider: Higgsfield MCP (사용자 확정 1순위). 슬롯 spec을 **완전 결정된 브리프**
  (목표·크기·텍스트 존·팔레트·금지어)로 만들어 생성한다.
- **하우스 포토그래피 접미사를 모든 T1 프롬프트에 강제한다** (P1 방어 — "AI 티" 원천 차단):
  필름 스톡(`Kodak Portra 400`)·구체적 렌즈/조명 방향(`85mm, natural window light from left`)·
  **의도적 불완전성**(`subtle film grain, natural tonal variation, slight imperfections`).
  `8k / masterpiece / flawless / trending on artstation` 계열 금지.
  생성 범위는 배경·질감·환경까지 — **제품 실물·손·얼굴은 생성하지 않는다** (compliance §5-1 + T2).
- 재생성보다 **편집 도구 우선**: `remove_background` / `outpaint` / `reframe`.
- **`surface: texture` 블록의 텍스처도 부품이다**: `python3 pipeline/gen_textures.py`로 생성 →
  `upload_assets`로 올려 imageHash 확보 → 조립 시 `[SOLID 베이스, IMAGE(저불투명·TILE)]`
  레이어드 필로 얹는다 (v3 검증 방식 — SOLID를 유지해야 qa_check 명도 계산이 결정론으로 남는다).
- 부품마다 **asset-validator 에이전트**(`.claude/agents/asset-validator.md`)로 이진 판정.
  FAIL → 검증자의 재생성 지시로 재시도, **부품당 상한 3회** → 사람 에스컬레이션.
- T2 슬롯은 생성 대상이 아니다 — 사용자에게 원본 주입을 요청한다.

### 2-3. 빌드 (`use_figma`)

`docs/analysis/craft-axioms.md`를 **열어놓고** 짓는다. 코드 레시피는 §5.
스크립트당 블록 2~3개. 실패해도 원자적이라 파일은 무변화 — 고쳐서 재시도.

- **동결된 플랜을 실행만 한다.** 여기서 새로 창작하지 않는다. API 에러에는 반응하되
  설계 이탈은 금지 — 이탈 필요 시 2-2 재승인으로 회송.
- **강조 집중 (§2.7)**: 블록마다 제목 강조 필수 + 하위 강조는 1개만 + 두 강조는 세로 100px 이상 간격.
- **위→아래 순차 조립 + 이전 블록 렌더를 보면서** 짓는다 (2~3블록마다 스크린샷 확인).
  전 속성 일괄 생성보다 페이지 목소리가 유지된다 (LaDeCo·CVPR 2025).

### 2-4. 검수 루프 ★

```
빌드 → qa_check.py(결정론) → export_text.py(법적 사이드카)
     → detail-page-reviewer ∥ red-team-auditor (병렬·독립, 서로의 출력 안 봄)
     → 지적 반영 → 재검수 → PASS까지 (상한 4라운드)
```

- **red-team-auditor**(`.claude/agents/red-team-auditor.md`)는 실격·compliance 위반만 찾는
  비대칭 감사자다. 검수자와 **독립 실행, 합의 금지** — red-team의 위반 1건 = 즉시 FAIL.
- 검수자에게 **빌더의 자기설명을 넘기지 않는다.** 입력은 렌더 + qa_check 출력 + 공리계뿐.
- **라운드 메모리**: 라운드마다 {지적, 수정, 축별 개선/후퇴}를 기록해 다음 라운드에 넘긴다.
  이미 통과한 항목의 회귀는 최우선 수정 대상이다. 재검수는 **변경 블록 + 실격 게이트**만
  전수로, 나머지는 회귀 플래그 확인만 (전량 재채점은 점수 churn만 만든다).

```bash
python3 pipeline/qa_check.py   <fileKey> <rootNodeId>   # 공리 위반 + compliance 토큰 + 클립 이탈
python3 pipeline/export_text.py <fileKey> <rootNodeId>  # 인증번호 텍스트 사이드카 + 필수항목 누락 검사
```

**`qa_check.py`가 척추다.** 대비비·명도 런·위계비·폰트 하한·클립 이탈·텍스트 충돌·수치 정합·compliance 토큰은 전부 결정론적으로 계산된다. 에이전트는 그것이 못 보는 것(구성·질감·컨셉 일치·겹침의 질)만 판정한다.

**루프 규율 4가지** (실전 6라운드에서 도출 → 전문은 [craft-axioms §8](../../../docs/analysis/craft-axioms.md#8-루프에서-실제로-배운-것-6라운드-실전-기록))

1. **매 라운드, 검수자 지적 중 "결정론적으로 계산 가능했던 것"을 체커로 이관하라.** 이관하면 같은 종류가 재발하지 않고 검수자는 더 깊은 층위를 본다.
2. **통과시키려고 규칙을 완화하지 마라.** 실전에서 두 번 시도했고 두 번 다 반증됐다. 규칙 변경은 코퍼스 실측을 근거로 대고, 검수자에게 **"이 변경이 우회인지 검증하라"** 고 명시적으로 요청하라.
3. **수치가 안 맞으면 수치를 바꾸지 말고 주장을 바꿔라.** compliance는 craft 위에 있다.
4. **점수가 내려가는 라운드는 정상이다.** 수정이 새 결함을 만들었다는 뜻이고, 그것을 검수자가 잡았다는 뜻이다.
5. **라운드 상한 4.** 그 이상은 노이즈에 지불하는 것이다(자기개선 문헌 합의: 이득은 1~2라운드에 집중).
   상한 도달 시 루프를 더 돌리지 말고 **공리/템플릿(생성자 prior)을 고쳐라** — v2가 6라운드 걸린 것이
   v3에서 1라운드가 된 이유는 라운드 수가 아니라 prior 개선이었다.
6. **동일 결함이 2라운드 연속 살아남으면 조립 반복이 아니라 레이아웃 리플랜으로 에스컬레이션한다**
   (stall counter — 그 결함은 조립 실수가 아니라 설계 결함이라는 신호다).
7. **정지 조건은 "80 돌파"가 아니라 "게이트 all-green + 안정"이다.** 절대점수는 ±수 점 노이즈가 있다.
   실격 0 + compliance 0 + 축별 후퇴 0 + 2라운드 연속 점수 변화 < 3점이면 안정 도달로 판정한다.

검수자 정의: `.claude/agents/detail-page-reviewer.md`. 통과 기준 **80/100 + 실격 0건**.
검수자가 없는 세션이면 `general-purpose` 에이전트에 그 파일을 읽히고 역할을 위임한다.
**스스로 통과 판정하지 않는다.** 자기 산출물에 대한 자기 채점은 항상 후하다.

## 3. 공리계 (요약 — 전문은 `docs/analysis/craft-axioms.md`)

### 실격 공리 (하나라도 걸리면 FAIL)

`F1` 콘텐츠 폭이 한 번도 안 바뀜(풀블리드 0개) · `F2` 모든 카드 동일 라운드 · `F3` 회색 점선 placeholder · `F4` 텍스트와 이미지가 절대 안 겹침 · `F5` 강조가 굵기 하나뿐 · `F6` 이모지를 아이콘으로 · `F7` 모든 블록 여백 동일 · `F8` 장식 레이어 0개인 블록 · `F9` 카드 안의 카드 · `F10` 중성 배경이 순수 무채색

### 메타 공리

**디폴트를 다른 디폴트로 바꾸지 마라.** 크림/베이지 배경, 세리프 이탤릭, 오로라 메시 그라디언트, 글래스모피즘, 그라디언트 텍스트는 **이미 AI 디폴트**다. 모든 선택은 이 제품의 컨셉·사실에서 파생시켜라.

⚠️ 중앙정렬은 실격이 아니다 — 860px 세로 페이지에서는 정상 관습이다. 판정할 것은 **콘텐츠 폭이 변하는가**다.

## 4. 디자인 시스템 도출 (입력이 없을 때)

**0. 방향 탐색 — 필수 (style-explorer, 입력 독립성 장치).** 아래 1~8을 결정하기 전에
**서로 다른 방향 2~3개**(물성 세계관 + 팔레트 + 표면 비율 조합)를 병렬로 만들고 각각 대표
블록 1개를 시안으로 지어, 사용자 선택(HITL) 또는 pairwise 랭킹으로 확정한다.
단일 샷 직행은 중앙값 수렴 = 모든 입력이 같은 지문이 되는 지름길이다.
각 방향은 **이 제품의 컨셉 sheet에서 파생**해야 하며, 이전 제품의 결정을 복사하면 안 된다.

1. 기획안 `컨셉` sheet에서 **USP 한 줄, 악당, 톤(warm/cold), 유형(Pain/Gain)** 을 뽑는다.
2. 팔레트 = **지배 hue 1 + 포인트 0~1 + 파생 오프화이트**. 지배 hue는 **이 제품의 패키지·카테고리에서 도출**하고(추측·관성 금지), 중성색은 그 hue 쪽으로 물들인다(F10). 파생 공식: 지배 hue의 채도 4~8%·명도 95~97% (예: hue가 그린이면 `#F3F6F1`류, 레드면 `#FCF5EA`류 — **예시는 공식의 사례지 기본값이 아니다**).
3. 타입 스케일(860px 폭 실측): 임팩트 120~196 / **헤드라인 70~100(중앙값 88)** / 서브 44~64 / **본문 25~32** / 각주 20~28. **낙차 ≥ 2.5:1**.
4. 폰트는 `config/fonts.json`(사람 관할)의 allowed만 — **무드·타이밍 매핑이 함께 있다**(세리프=디폴트/산세리프=무드/손글씨·장체·볼드·귀여움). 선택 근거를 plan에 기록. 상세 표는 `docs/fonts.md`. 기본 `Noto Sans KR`, 디스플레이 `Black Han Sans`(임팩트) / `Jua`·`Do Hyeon`(친근), 숫자·라벨 `Gothic A1`(9웨이트). **전 페이지 단일 서체면 감점.** Pretendard·SUIT·NanumSquare Neo는 **로드 불가**.
5. **배경 표면 시스템(surface system)** — 기획의 전체 플로우를 조망하고 톤앤매너의 함수로
   **여기서 비율을 선언**한다. 블록별 즉흥 결정 금지 (v6 실전: 결정 주체가 없어 전 블록 SOLID가 됐다).
   - 표면 어휘 4종: `solid`(평면 단색) / `texture`(T0 절차적 텍스처 레이어드 필) / `gradient` / `photo`(풀블리드 사진)
   - `design_system.surface_system.ratios`에 목표 비율을 적고, 각 블록의 `surface` 필드가 이를 구현한다
   - **완전 평면 solid > 60% = 다양성·창의성 부족** (craft-axioms §3.1). 배너·법정 고지는 예외
   - 컨셉별 기본 가이드: 전통·프리미엄 → 한지/종이 텍스처 / 신선·자연·비건 → 그레인 + 사진 비중↑ /
     테크·기능 → 그라디언트 위주. 실사 에셋이 많아도 **사진 없는 블록에는 텍스처를 깐다** — 사진과 텍스처는 배타가 아니다
   - 한국 실무 근거(`docs/analysis/research-detail-page.md`): 잘 만든 페이지의 기대 분포는
     **photo 다수 · solid 소수** (컷 배합 관행: 연출 3–4 : GIF 2–3 : 누끼 1). **누끼 단독 남발 = 저가 인상**
   - **표면 전환은 감정 비트 경계에서만** — 여백·배경 전환 = 주제 전환 신호. L/M/D 전환과 동기화
   - 식품: L 표면은 웜 크림 계열 기본(식욕 색채심리 — 단 F10의 브랜드 hue 파생이 우선).
     **다크는 프리미엄·인증·기술 비트 전용, 시즐 비트 금지** (§4.8) — 니어블랙 + 웜 메탈릭 + 웨이트 +1
   - 텍스처는 **명도중립·고대비 타일**(hanji_hi/kraft_hi — mean>220·σ>5 자기검증 내장)을
     MULTIPLY 0.85~0.9로. 어두운 저대비 타일은 불투명 조절로 못 살린다 (v6 실측 — backlog B6)
6. **물성 세계관 1줄 선언** (gap-v6 G35 — HITL 승인 대상): "이어 붙인 스크랩북" / "한지 공예" /
   "정육점 포장지" 식의 **하나의 허구**를 선언하고, 전환 어휘·모티프·질감을 전부 그 세계관에서
   파생시킨다. 세계관 없는 장치 나열은 인용에 그친다 (v6의 zigzag가 그랬다)
7. **서브 팔레트 축** (G14): 맛/옵션별 색 코딩(예: 불고기=다크레드, 제육=레드오렌지) +
   보조 무대색(옐로 면 등) 선언 — 지배 hue 모노톤 금지 (§9 U6)
8. **사진 그레이드 스펙** (G33): 페이지 대표 톤 1줄(예: "웜, R−G ≥ +10") — 모든 사진·생성물이
   이 기준으로 통일되어야 "한 촬영"으로 읽힌다. asset-validator V9의 기준값

## 5. Figma 코드 레시피 (실전 검증됨)

```js
// 색 (0–1 범위)
const C=h=>{const n=parseInt(h.slice(1),16);return{r:((n>>16)&255)/255,g:((n>>8)&255)/255,b:(n&255)/255}};
const S=h=>[{type:'SOLID',color:C(h)}];
const V=[[0,1,0],[-1,0,1]];  // 세로 그라디언트 transform
const GRAD=(a,b,t)=>[{type:'GRADIENT_LINEAR',gradientTransform:t||V,
  gradientStops:[{position:0,color:{...C(a),a:1}},{position:1,color:{...C(b),a:1}}]}];
const SCRIM=(hex,a0,a1)=>[{type:'GRADIENT_LINEAR',gradientTransform:V,
  gradientStops:[{position:0,color:{...C(hex),a:a0}},{position:1,color:{...C(hex),a:a1}}]}];
```

**블록 골격 — 풀블리드를 쓰려면 블록 패딩은 0이어야 한다 (F1)**
```js
// 블록: 패딩 0, 폭 860 고정
function block(name,bg){const b=figma.createAutoLayout('VERTICAL',{name,itemSpacing:0});
  b.fills=S(bg);b.counterAxisAlignItems='CENTER';root.appendChild(b);
  b.resize(860,10);b.primaryAxisSizingMode='AUTO';b.counterAxisSizingMode='FIXED';return b}
// 텍스트용 안쪽 패딩 컨테이너 (풀블리드 요소는 block에 직접 append)
function wrap(parent,o){/* paddingLeft/Right 60, paddingTop/Bottom = o.py */}
```

**인라인 색 전환 (§2.1 — F5를 푸는 1순위 도구)**
```js
function paint(t,sub,hex,sty){const i=t.characters.indexOf(sub);if(i<0)return t;
  t.setRangeFills(i,i+sub.length,S(hex));
  if(sty)t.setRangeFontName(i,i+sub.length,{family:t.fontName.family,style:sty});return t}
paint(headline,"<강조할 핵심어>",ACCENT);   // 한 문장 안에서 색이 바뀐다 — 색은 plan.design_system에서
paint(body,"<스캔 포인트 구간>",TEXT_INK,"Bold");  // 본문 부분 볼드
```

**마커 하이라이트 (§2.2)** — 부모 auto-layout + ABSOLUTE 자식을 index 0으로
```js
function marker(t,hex,o){o=o||{};
  const w=figma.createAutoLayout('HORIZONTAL',{name:'marker'});w.fills=[];
  w.appendChild(t);
  const r=figma.createRectangle();w.appendChild(r);r.layoutPositioning='ABSOLUTE';
  r.fills=S(hex);const pad=o.pad||10,hh=o.h||0.32;
  r.resize(t.width+pad*2,t.height*hh);
  r.x=-pad;r.y=t.height*(1-hh)-t.height*(o.lift||0.14);
  w.insertChild(0,r);   // ← 텍스트 뒤로
  return w}
```
⚠️ `t`는 **hug 크기**여야 한다. 헤드라인은 `\n`으로 **직접 줄바꿈**하라(§2.4 — 자동 줄바꿈은 줄 길이가 균일해져 티가 난다).

**말풍선 태그 (꼬리는 VECTOR로 — 회전 계산 불필요)**
```js
const v=figma.createVector();b.appendChild(v);v.layoutPositioning='ABSOLUTE';
v.vectorPaths=[{windingRule:'NONZERO',data:'M 0 0 L 20 0 L 10 13 Z'}];
v.fills=S(bg);v.strokes=[];v.x=b.width/2-10;v.y=b.height-1;
```

**designed placeholder (§5 — F3 회피)**
```js
function imgSlot(name,w,h,parent,o){o=o||{};
  const f=figma.createFrame();f.name='IMG_'+name;f.resize(w,h);
  f.fills=GRAD(o.a||DOM_DARK,o.b||DOM_MID);        // plan.design_system.dominant의 저채도 파생 2단 — 회색 금지, 타 제품 값 재사용 금지
  f.clipsContent=true;f.cornerRadius=o.circle?w/2:(o.rad||0);
  if(parent)parent.appendChild(f);
  const lb=T(name,17,'Medium','#FFFFFF');lb.opacity=0.36;   // 구석에 작게
  f.appendChild(lb);lb.x=22;lb.y=h-32;return f}
```
`createFrame()`은 layoutMode NONE이라 자식이 **절대 좌표**로 놓인다 → 겹침·블리드의 무대.

**겹침 + 가독성 계약 (§6.5 — F4를 지키되 실패하지 않기)**
```js
const stage=figma.createFrame();stage.resize(860,660);stage.clipsContent=true;stage.fills=[];
block.appendChild(stage);                       // 풀블리드 무대
const img=imgSlot('...',860,660,null,{});stage.appendChild(img);img.x=0;img.y=0;
const scrim=figma.createRectangle();stage.appendChild(scrim);
scrim.resize(860,660);scrim.fills=SCRIM('#04140B',0.15,0.92);   // ← 스크림 필수
const t=T('...',92,'Regular','#FFFFFF',{f:'Black Han Sans'});
stage.appendChild(t);t.x=60;t.y=396;            // 스크림 위에 텍스트
```
사진 밖으로 흘리려면 `img.x=420; img.width=520`처럼 무대 밖으로 나가게 두고 `clipsContent=true`.

**우측 블리드 + 점선 리더 (레퍼런스 `1:1533` 기법)**
```js
const ln=figma.createLine();stage.appendChild(ln);
ln.resize(96,0);ln.strokes=S('#B9C4B5');ln.strokeWeight=2;ln.dashPattern=[3,7];
```

**리더선 앵커 — 수치를 사진 지점에 물리적으로 연결 (gap-v6 G2, 디자이너 08 기법)**
```js
// 수치 태그 ↔ 사진의 해당 지점을 점선으로 잇는다. 차트와 사진의 분리를 없앤다
function leader(stage, fromX, fromY, toX, toY, hex){
  const v=figma.createVector();stage.appendChild(v);v.layoutPositioning='ABSOLUTE';
  v.vectorPaths=[{windingRule:'NONE',data:`M ${fromX} ${fromY} L ${toX} ${toY}`}];
  v.strokes=S(hex||'#E0A93B');v.strokeWeight=2;v.dashPattern=[4,6];v.fills=[];v.x=0;v.y=0;
  const dot=figma.createEllipse();stage.appendChild(dot);dot.resize(10,10);
  dot.fills=S(hex||'#E0A93B');dot.x=toX-5;dot.y=toY-5;return v}
```

**누끼 인터락 — 컷아웃을 경계에 물린다 (G1·G19)**
```js
// remove_background 산출 누끼를 색면 경계·카드 모서리에 걸치기. '카드에 갇힌 사진'을 깬다
// 전제: 누끼 PNG를 upload_assets로 올려 imageHash 확보 (배경 투명)
const cut=figma.createRectangle();cut.resize(w,h);
cut.fills=[{type:'IMAGE',imageHash:HASH,scaleMode:'FIT'}];
block.appendChild(cut);cut.layoutPositioning='ABSOLUTE';
cut.y=boundaryY-h*0.55;   // 경계선을 55:45로 물고
cut.x=860-w*0.8;          // 우측을 살짝 흘린다 (§1.5)
```

**회전 스티커·테이프 (G20 — 회전 예산 §9 U4: 페이지당 3~5개)**
```js
function sticker(parent,txt,hex,deg){const s=figma.createAutoLayout('HORIZONTAL',{name:'스티커'});
  s.fills=S(hex);s.cornerRadius=999;s.paddingLeft=22;s.paddingRight=22;s.paddingTop=12;s.paddingBottom=12;
  parent.appendChild(s);s.layoutPositioning='ABSOLUTE';
  const t=T(txt,26,'Black','#FFFFFF');s.appendChild(t);
  s.rotation=deg||-12;   // ±8~20°. 본문 텍스트에는 금지
  return s}
```

**자사 열 승격 표 (G21) — 비교표는 공정하지 않다**
```js
// 타사 열: 저채도 침강(#EDEFEA 배경·#8A9187 텍스트·라운드 6)
// 자사 열: 흰 카드 + 지배색 헤더 + 라운드 16 + 3px 골드 스트로크 + 폭 1.15배
// 두 열을 동격 카드로 만들면 정보는 남고 설득이 죽는다 (v6 실측)
```

**각주 마이크로 스타일 (G22)** — 각주는 사진 구석 1줄 17~19px + 반투명 플레이트.
다중행 베이지 패널로 블록 하단을 점유시키지 마라 (v6 07은 블록의 40%가 고지문이었다).
**수치 표기 (G12)**: 본문은 반올림(37%), 라벨 정밀값(37.81%)은 각주로 — 그래픽 파워와 정합을 둘 다.

**제품 파생 배지 (G18)** — 넘버 배지 형태를 **이 제품의 실루엣**에서 파생한다 (예: 삼각 제품이면 라운드 삼각, 병 제품이면 라운드 사각+숄더). 아래는 삼각 제품의 사례 코드다.
```js
const tri=figma.createVector();tri.vectorPaths=[{windingRule:'NONZERO',
  data:'M 30 4 C 34 4 38 7 40 11 L 55 38 C 58 44 54 50 48 50 L 12 50 C 6 50 2 44 5 38 L 20 11 C 22 7 26 4 30 4 Z'}];
tri.fills=S('#1F4A2C');  // 60×54 라운드 삼각 배지 — 위에 넘버 텍스트 겹치기
```

## 6. 함정 (실제로 당한 것들)

| 함정 | 증상 | 대처 |
|---|---|---|
| `resize()` 후 `primaryAxisSizingMode='AUTO'` | 비례 막대 폭이 콘텐츠 hug로 리셋 | 비례 요소는 `'FIXED'` 유지 |
| `figma.currentPage`가 호출마다 리셋 | 다른 페이지에 그려짐 | 매 호출 `await figma.setCurrentPageAsync(pg)` |
| `layoutSizing*` vs `*AxisSizingMode` 혼동 | `Expected 'FIXED'\|'AUTO'` 에러 | 자식=`FIXED/HUG/FILL`, 프레임 자신=`FIXED/AUTO` |
| `figma.notify()` | "not implemented" | 쓰지 않는다. 출력은 `return` |
| 폰트 스타일명 추측 | 로딩 실패 | `docs/fonts.md` 문자열 그대로. `Black Han Sans`는 `Regular` 하나뿐 |
| 텍스트 mutate 전 `loadFontAsync` 누락 | `Cannot write to node with unloaded font` | 스크립트 첫머리에 쓸 폰트 전부 `Promise.all`로 로드 |
| `use_figma` 실패 후 즉시 재시도 | 같은 에러 반복 | 원자적이라 파일은 무변화. **에러를 읽고 고쳐서** 재시도 |

## 7. 산출물 규약

- 파일명: `<브랜드>_<제품>_<기획안번호>`, 프로젝트 636598794
- 반복 시도는 **같은 파일 안 새 페이지**(`v2 — craft` 식). 이전 버전을 남겨 대조한다
- 블록 레이어명: `<seq>_<장면>` (예: `01_훅`) — **시스템 명세다**: qa_check의 역할 면제(ROLE_EXEMPT)가 이름 토큰(배너/브릿지/고지/옵션/FAQ/조리법)에 결합돼 있다. plan의 seq와 접두 일치 필수. 이미지 슬롯은 `IMG_<설명>`. 이름 규약을 벗어나면 `--plan`의 scene_type 면제로 보완된다
- 플랜·파싱 결과는 `data/briefs/`에 커밋. **Figma 산출물은 저장소에 커밋하지 않는다**

## 8. 참조

`docs/agentic-workflow.md`(워크플로우 요구사항) · `docs/agent-architecture.md`(에이전트 구성·근거) · `docs/analysis/craft-axioms.md`(공리계·판정 루브릭) · `docs/analysis/scene-taxonomy.md` · `docs/analysis/layout-catalog.md` · `docs/analysis/design-tokens.md` · `docs/fonts.md` · `docs/rules.md` · `pipeline/README.md` · `docs/manual/usage-manual.md`(사용법 매뉴얼)
레퍼런스 정답지 선택 규칙: ① 동일 제품의 디자이너 완성본이 있으면 그것 ② 없으면 `docs/figma-spaces.md`의 Good 9종 중 **같은/가까운 카테고리** ③ 그것도 없으면 Good 케이스 2종 이상을 병렬 참조. **특정 제품(구스밀 등)을 기본값으로 고정하지 않는다** — 테스트 입력이 정답지로 굳는 것이 과적합의 시작이다

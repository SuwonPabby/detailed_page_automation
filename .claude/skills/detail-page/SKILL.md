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

## 1. 입력

| 항목 | 필수 | 없을 때 |
|---|---|---|
| 기획안 xlsx | ✅ | 진행 불가 |
| 디자인 시스템(폰트/색/키워드) | ⬜ | 기획안 `컨셉` sheet + 레퍼런스 팔레트에서 도출 (§4) |
| asset 폴더 | ⬜ | designed placeholder로 자리만 확보 (§3 §5). **에셋은 3계층** — T0 절차생성/T1 AI생성/T2 주입필수(증거) → `docs/assets.md` |
| 출력 Figma 링크 | ⬜ | 프로젝트에 새 파일 생성 |

## 2. 4단계 파이프라인

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

**장면 → 레이아웃:** `docs/analysis/scene-taxonomy.md`(19종 통제 어휘) → `docs/analysis/layout-catalog.md`(38패턴). 인접 블록 동일 패턴 금지. usp 연작은 **근거 패턴을 매번 교체**.

**리듬 설계:** 배경 L/M/D 시퀀스를 미리 문자열로 적는다. 다크 2~6개(훅·프리미엄·신뢰·클라이맥스·클로징), 연속 L 6개 금지. **클라이맥스 블록 1~2개**를 지정한다.

### 2-3. 빌드 (`use_figma`)

`docs/analysis/craft-axioms.md`를 **열어놓고** 짓는다. 코드 레시피는 §5.
스크립트당 블록 2~3개. 실패해도 원자적이라 파일은 무변화 — 고쳐서 재시도.

### 2-4. 검수 루프 ★

```
빌드 → qa_check.py(결정론) → export_text.py(법적 사이드카)
     → detail-page-reviewer 에이전트 → 지적 반영 → 재검수 → PASS까지
```

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

1. 기획안 `컨셉` sheet에서 **USP 한 줄, 악당, 톤(warm/cold), 유형(Pain/Gain)** 을 뽑는다.
2. 팔레트 = **지배 hue 1 + 포인트 0~1 + 파생 오프화이트**. 중성색은 지배 hue 쪽으로 물들인다(F10). 딥그린이면 `#F3F6F1`, 오렌지레드면 `#FCF5EA`.
3. 타입 스케일(860px 폭 실측): 임팩트 120~196 / **헤드라인 70~100(중앙값 88)** / 서브 44~64 / **본문 25~32** / 각주 20~28. **낙차 ≥ 2.5:1**.
4. 폰트는 `docs/fonts.md`의 검증 목록만. 기본 `Noto Sans KR`, 디스플레이 `Black Han Sans`(임팩트) / `Jua`·`Do Hyeon`(친근), 숫자·라벨 `Gothic A1`(9웨이트). **전 페이지 단일 서체면 감점.** Pretendard·SUIT·NanumSquare Neo는 **로드 불가**.

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
paint(headline,"식물성 저당 주먹밥","#E9B949");   // 한 문장 안에서 색이 바뀐다
paint(body,"단백질은 많은데 지방은 적어서","#1C2119","Bold");  // 본문 부분 볼드
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
  f.fills=GRAD(o.a||'#123D26',o.b||'#20603C');      // 브랜드 팔레트 저채도, 회색 금지
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
- 블록 레이어명: `01_훅`, `05_저당_POINT1` — 번호 + 장면. 이미지 슬롯은 `IMG_<설명>`
- 플랜·파싱 결과는 `data/briefs/`에 커밋. **Figma 산출물은 저장소에 커밋하지 않는다**

## 8. 참조

`docs/analysis/craft-axioms.md`(공리계·판정 루브릭) · `docs/analysis/scene-taxonomy.md` · `docs/analysis/layout-catalog.md` · `docs/analysis/design-tokens.md` · `docs/fonts.md` · `docs/rules.md` · `pipeline/README.md`
레퍼런스 정답지: `Full_design` 구스밀 `1:1305` (동일 제품의 디자이너 완성본)

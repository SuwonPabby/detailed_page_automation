# fonts — 한글 폰트 (실측 검증 완료)

검증일 **2026-08-08**. Figma 캔버스에 실제로 렌더링해 눈으로 확인한 결과입니다.

## ⚠️ 폰트를 다운로드하지 마세요

**로컬에 폰트를 설치하거나 저장소에 넣는 것은 아무 효과가 없습니다.**

우리는 Figma **원격 MCP 서버**(`mcp.figma.com`)를 통해 Figma 클라우드에 그립니다. 렌더링은 Figma 쪽에서 일어나므로, 작업 머신의 파일시스템은 Figma가 볼 수 없습니다. **쓸 수 있는 폰트는 Figma가 이미 보유한 것뿐**입니다.

폰트가 필요하면 다운로드가 아니라 **조회**하세요:

```js
const fonts = await figma.listAvailableFontsAsync();
```

현재 사용 가능한 패밀리는 총 **1,938개**, 그중 한글 후보는 **36개**입니다.

> 로컬 폰트 설치가 의미 있는 경우는 Figma **데스크톱 앱**에서 작업할 때뿐입니다. 지금 구조(원격 MCP)에서는 해당 없습니다.

## 검증 결과 — 10종 전부 한글 정상 출력

40px로 `활기찬 건강한 다이어트 1234`를 렌더링해 확인했습니다. 두부(tofu) 현상 없음.

| 폰트 | 웨이트 수 | 사용 가능한 스타일 | 성격 |
|---|---|---|---|
| **Noto Sans KR** | 7 | Thin, Light, DemiLight, Regular, Medium, Bold, Black | 고딕 · 범용 |
| **Gothic A1** | 9 | Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold, ExtraBold, Black | 고딕 · 위계 세분화 |
| **IBM Plex Sans KR** | 7 | Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold | 고딕 · 모던 |
| **NanumGothic** | 3 | Regular, Bold, ExtraBold | 고딕 · 친숙 |
| **Noto Serif KR** | 7 | ExtraLight, Light, Regular, Medium, SemiBold, Bold, Black | 명조 |
| **NanumMyeongjo** | 3 | Regular, Bold, ExtraBold | 명조 · 전통 |
| **Hahmlet** | 9 | Thin ~ Black | 명조 · 묵직 |
| **Black Han Sans** | 1 | Regular | 디스플레이 · 강한 임팩트 |
| **Do Hyeon** | 1 | Regular | 디스플레이 · 둥근 |
| **Jua** | 1 | Regular | 디스플레이 · 친근 |

## 권장 조합

상세페이지는 **[design-principles.md](./design-principles.md) B항 — "폰트 큼, 최소 64px"** 규칙을 따라야 하므로, 큰 사이즈에서 버티는 굵은 웨이트가 필수입니다.

| 역할 | 1순위 | 대안 |
|---|---|---|
| **기본 본문 + 제목** | `Noto Sans KR` (7웨이트로 위계 커버) | `Gothic A1` (9웨이트, 더 촘촘한 위계) |
| **대형 헤드라인** (64px+) | `Noto Sans KR Black` / `Gothic A1 Black` | `Black Han Sans` (임팩트 최대, 단일 웨이트) |
| **전통 · 프리미엄 컨셉** | `NanumMyeongjo` / `Noto Serif KR` | `Hahmlet` |
| **친근 · 캐주얼 컨셉** | `Jua` / `Do Hyeon` | — |

컨셉 키워드에 따라 고릅니다 — 밀밭명가(`한국적인/전통문양`)라면 명조, 구스밀(`비건/친근한`)이라면 `Jua` 계열이 맞습니다. → [design-principles.md E항](./design-principles.md)

**기본값으로는 `Noto Sans KR`을 쓰세요.** 웨이트가 충분하고 한글·영문·숫자 균형이 가장 안정적입니다.

## 레퍼런스 폰트 치환 정책 (2026-08-08 검증)

레퍼런스 `Full_design`의 실제 사용 폰트를 쓰기 파일에서 `loadFontAsync`로 검증한 결과:

| 레퍼런스 폰트 (사용 비중) | 로드 가능? | 치환 |
|---|---|---|
| **Pretendard(+Variable)** (70%) | ❌ FAIL | → **Noto Sans KR** (웨이트 매핑: 500→Medium, 600→Bold, 700→Bold, 800+→Black) |
| NanumSquare Neo | ❌ FAIL | → Noto Sans KR 또는 Gothic A1 |
| SUIT Variable | ❌ FAIL | → Noto Sans KR |
| Cafe24 PRO Slim / Happy Time / Solmoe KimDaeGeonOTF (포인트) | ❌ FAIL | → 디스플레이 대체: Jua/Do Hyeon(친근), Song Myung(전통 세리프) |
| NanumMyeongjo | ✅ 사용 가능 | 그대로 |

레퍼런스 폰트들은 디자이너 로컬/팀 공유 폰트로, **우리 쓰기 환경에서는 로드가 불가능**합니다.

**치환 원칙**: 패밀리보다 **위계(크기·웨이트 낙차)를 보존**한다 — [design-tokens.md §1](./analysis/design-tokens.md) 참조. `data/blocks.json`에는 원본 폰트명이 그대로 기록되어 있고, 치환은 생성 시점 정책이다.

## 주의사항

- **스타일 이름을 추측하지 마세요.** 위 표의 문자열을 그대로 쓰거나 `listAvailableFontsAsync()`로 확인하세요. Inter의 `Semi Bold`(공백 있음) vs Gothic A1의 `SemiBold`(공백 없음)처럼 패밀리마다 표기가 다릅니다. 틀리면 폰트 로딩이 실패합니다.
- **텍스트를 만지기 전에 반드시 `await figma.loadFontAsync(...)`.** 빠뜨리면 `Cannot write to node with unloaded font` 에러가 납니다. 기존 텍스트를 수정할 때는 하드코딩된 기본값이 아니라 `getStyledTextSegments(['fontName'])`로 **현재 폰트**를 읽어 로드하세요.
- `NanumMyeongjo`는 한글 자간이 다른 폰트보다 넓게 잡힙니다. 조밀한 레이아웃에서는 자간 조정이 필요할 수 있습니다.
- 이름에 `KR`이 들어가도 한글 폰트가 아닌 경우가 있습니다(`Orbitron`, `TASA Orbiter`, `Yeseva One` 등은 이름 매칭에 걸렸을 뿐 라틴 전용). **이름이 아니라 렌더링으로 판단하세요.**

## 디스플레이 후보 확장 (2026-08-16 로드 검증 — v7 상한 공리 대응)

`loadFontAsync` 실측. **장체(콘덴스드)는 Figma 클라우드 한글 풀에 없다** — 디자이너의
Cafe24 PRO Slim·Gmarket Sans·SUIT 계열 전부 로드 불가 확인.

**로드 가능 신규 20종** (Regular 단일 웨이트 위주): Gugi(기하학적 개성) · Song Myung(명조 디스플레이) ·
Stylish · Yeon Sung · Bagel Fat One(라운드 팻) · Orbit · Moirai One · Diphylleia · Grandiflora One ·
Dokdo/East Sea Dokdo·Kirang Haerang·Single Day·Poor Story·Gamja Flower·Cute Font·Hi Melody·
Gaegu·Nanum Brush Script(손글씨 계열) · Black And White Picture
**로드 불가**: Sunflower, Nanum Pen Script

### 130px+ 선언 타이포 전략 (§9 U1 — 장체 부재 하에서)

1. **1순위: `Gothic A1 Black` + 자간 −3~−4% + lineHeight 98%** — 9웨이트 패밀리라 같은 지면에서
   위계 낙차 표현 가능. Black Han Sans보다 대형 급수에서 덜 뭉툭
2. 컨셉이 팻/친근이면 `Bagel Fat One`, 기하/모던이면 `Gugi`, 프리미엄 명조면 `Song Myung` 검토
3. ⚠️ 신규 20종은 로드만 검증됨 — 실사용 전 해당 급수(130px+)로 렌더 확인 필수 (두부·자간 문제)

## 무드·타이밍 매핑 (2026-08-17 — 기계 소비용 원본은 config/fonts.json)

사용자 정의 분류. **폰트 선택이 퀄리티를 크게 좌우한다** — 무드 선택 근거를 plan에 기록할 것.

| 분류 | 무드 | 언제 쓰면 이쁜가 | 가용 서체 |
|---|---|---|---|
| **세리프 = 디폴트** | 기본 서사 | 본문·브랜드 스토리·차분한 설득 | Noto Serif KR(7w 주력) · NanumMyeongjo · Jeju Myeongjo · Gowun Batang · Hahmlet(9w) · Song Myung(헤드 강조) |
| **산세리프 = 무드** | 고급·프리미엄·여성적·이국적 (힘빼기) | 프리미엄 연출 블록, 뷰티·여성 카테고리, 가벼운 서브카피 — **Light~DemiLight 웨이트가 핵심** | Noto Sans KR(Pretendard 대체) · IBM Plex Sans KR(이국) · Gothic A1(숫자 겸용) · NanumGothic(고지) · Jeju Gothic |
| 손글씨·구어체 | 사람의 목소리 | 리뷰 인용·감탄 카피·테이프 문구. **페이지당 1~2회** | Nanum Brush Script |
| 장체 임팩트 | 대형 선언 | 클라이맥스 선언(130px+) | (부재) → **Gothic A1 Black 자간-3% lh98%** |
| 볼드·개성 | 힘·주장 | 훅·클라이맥스 헤드, 주력 1종만 | Black Han Sans · Gugi |
| 귀여움 | 친근·B급 | 간식·키즈 톤 헤드·배지·말풍선 | Jua · Do Hyeon · Bagel Fat One |

wishlist 10종(Pretendard·Cafe24 PRO Slim·Jalnan 2 등)은 Organization 플랜 업로드 대기 —
대체 매핑은 config/fonts.json `wishlist` 참조. ⚠️ 표시 서체는 대형 급수 렌더 검증 후 사용.

## ⭐ 정정 (2026-08-17): 커스텀 폰트는 개인 계정 업로드로 가능하다

"조직 플랜 전용"은 조직 공유 폰트 얘기였고, **개인 계정 업로드(프로필 → Settings → Account →
Your uploaded fonts)는 Pro 플랜에서 동작**한다. 업로드 폰트는 원격 MCP loadFontAsync와
REST 서버 렌더 모두에서 정상 동작 확인 (Pretendard 9웨이트 + Gmarket Sans TTF 3웨이트 실측).
⚠️ 반드시 MCP 인증 계정(appevory)으로 업로드. family명은 파일 내부명 기준
(예: "Gmarket Sans TTF" — "G마켓 산스" 아님). 나머지 wishlist는 파일 수동 확보 후 같은 절차.

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

## 주의사항

- **스타일 이름을 추측하지 마세요.** 위 표의 문자열을 그대로 쓰거나 `listAvailableFontsAsync()`로 확인하세요. Inter의 `Semi Bold`(공백 있음) vs Gothic A1의 `SemiBold`(공백 없음)처럼 패밀리마다 표기가 다릅니다. 틀리면 폰트 로딩이 실패합니다.
- **텍스트를 만지기 전에 반드시 `await figma.loadFontAsync(...)`.** 빠뜨리면 `Cannot write to node with unloaded font` 에러가 납니다. 기존 텍스트를 수정할 때는 하드코딩된 기본값이 아니라 `getStyledTextSegments(['fontName'])`로 **현재 폰트**를 읽어 로드하세요.
- `NanumMyeongjo`는 한글 자간이 다른 폰트보다 넓게 잡힙니다. 조밀한 레이아웃에서는 자간 조정이 필요할 수 있습니다.
- 이름에 `KR`이 들어가도 한글 폰트가 아닌 경우가 있습니다(`Orbitron`, `TASA Orbiter`, `Yeseva One` 등은 이름 매칭에 걸렸을 뿐 라틴 전용). **이름이 아니라 렌더링으로 판단하세요.**

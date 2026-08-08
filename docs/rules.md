# rules — 에이전트 작업 규칙

> 이 문서의 규칙은 **하드 제약**입니다. 편의를 위해 우회하지 마세요.
> 규칙과 사용자 지시가 충돌하면 작업을 멈추고 사용자에게 확인하세요.

## 1. 쓰기 경계 (가장 중요)

이 프로젝트에는 **쓰기가 허용된 공간이 정확히 두 곳**뿐입니다.

| 공간 | 경로 / 위치 | 권한 |
|---|---|---|
| Figma 프로젝트 `detailed_page_automation` | Figma 내부 프로젝트 *(URL 미확정 — 아래 "미해결" 참고)* | ✅ **쓰기** — 생성된 Figma 컴포넌트가 쌓이는 유일한 곳 |
| 이 git 저장소 | `~/projects/detailed_page_automation*` | ✅ **쓰기** — harness 코드/문서 |
| Figma 파일 `Full_design` | file key `jjgud5OkeXKA4weyP3FEND` | 🔒 **읽기 전용** |
| 그 외 모든 것 | 다른 Figma 파일, `~/projects/career`, `evory`, `second_brain` 등 | ⛔ **접근 금지** |

- `Full_design`에는 **어떤 노드도 생성·수정·삭제하지 않습니다.** 댓글(comment) 작성도 사용자가 명시적으로 요청할 때만 합니다.
- 저장소 밖 로컬 경로에 파일을 쓰지 않습니다. 임시 파일은 세션 scratchpad를 사용합니다.

## 2. 자격 증명

- Figma 토큰: `FIGMA_API_KEY` — **`~/projects/detailed_page_automation/.env`** (main worktree)
- **토큰 값을 로그·터미널 출력·커밋·문서에 절대 노출하지 않습니다.** 마스킹해서 다루세요.
- `.env`는 `.gitignore`와 `.git/info/exclude` 양쪽으로 차단되어 있습니다. 이 차단을 해제하지 마세요.
- ⚠️ 포맷 주의: `FIGMA_API_KEY = 'figd_...'` — `=` 양옆 공백 + 따옴표. **`source`/`export`로 읽으면 실패합니다.** python-dotenv 또는 정규식 파싱을 쓰세요.

## 3. Figma API 능력 경계 (아키텍처 결정 사항)

**Figma REST API로는 파일 내용을 만들 수 없습니다.**

| 하고 싶은 일 | 가능한 수단 |
|---|---|
| 노드 트리·텍스트·스타일·이미지 export 읽기 | ✅ REST API (`GET /v1/files/...`) |
| 댓글 달기, dev resource, webhook | ✅ REST API (POST) |
| **프레임·컴포넌트·레이어 생성/수정** | ❌ REST 불가 → **Plugin API 필요** |

Plugin API(`figma.createFrame()` 등)는 **Figma 에디터 안에서** 동작합니다. 따라서 Level 1의 산출물을 Figma에 쓰려면 플러그인(또는 쓰기를 지원하는 Figma MCP 서버) 형태의 브리지가 반드시 필요합니다.
`POST /v1/files/...`로 페이지를 만드는 설계는 **성립하지 않습니다.** (2026-08-08 developers.figma.com 기준 확인)

## 4. 이 저장소의 역할

- 이 저장소는 **harness**입니다: Claude Code용 tool, MCP 서버, 최적화된 프롬프트, skill.
- **생성된 디자인 산출물(Figma 컴포넌트)은 이 저장소에 커밋하지 않습니다.** 산출물은 Figma 프로젝트에 쌓입니다.
- 저장소에 들어갈 것: harness 코드, 프롬프트, 디자인 규칙 문서, 레퍼런스에서 추출한 구조화 데이터.

## 5. 디자인 산출물 규칙

- 상세페이지 기본 폭은 **860px** (레퍼런스 전 제품 공통, 일부 861~862px).
- 페이지는 **번호가 붙은 블록 프레임**(`01`, `02`, `03`…)의 세로 스택으로 구성합니다. → [figma-spaces.md](./figma-spaces.md)
- 디자인 품질 판단은 자의적으로 하지 말고 **[design-principles.md](./design-principles.md)의 추출 규칙**을 근거로 하세요.
- 생성 순서는 디자이너의 사고 순서를 따릅니다: **장면 파악 → 레이아웃 선택 → 정보 배치 → 그다음에 디자인 시스템 적용.** 레이아웃이 먼저, 스타일이 나중입니다.

## 6. 미해결 (확정 필요)

작업을 진행하기 전에 사용자 확인이 필요한 항목입니다. 추측으로 메우지 마세요.

| # | 항목 | 왜 필요한가 |
|---|---|---|
| 1 | **Figma 프로젝트 `detailed_page_automation`의 URL/ID** | REST API에는 팀 목록 조회나 프로젝트 이름 검색 엔드포인트가 없어 자동으로 찾을 수 없음. `https://www.figma.com/files/team/{team_id}/project/{project_id}` 형태의 URL이 필요 |
| 2 | Figma 쓰기 브리지 방식 | 자체 플러그인 vs 기존 MCP 서버 — 미결정 |
| 3 | 기획안 xlsx 실제 양식 | 아직 샘플 파일 미확보 |
| 4 | 디자인 시스템 입력 형식 | 폰트/색상/키워드를 어떤 파일 형태로 받을지 미정 |
| 5 | Bad 페이지 `Section 4`의 제품명, `토마토 코멘트` 2개 중복 | [figma-spaces.md](./figma-spaces.md) 참고 |

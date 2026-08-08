# rules — 에이전트 작업 규칙

> 이 문서의 규칙은 **하드 제약**입니다. 편의를 위해 우회하지 마세요.
> 규칙과 사용자 지시가 충돌하면 작업을 멈추고 사용자에게 확인하세요.

## 1. 쓰기 경계 (가장 중요)

**Figma 안에서 쓰기가 허용된 공간은 프로젝트 `detailed_page_automation` 단 하나입니다.**
로컬에서는 이 git 저장소만 씁니다. 그 외에는 어디에도 쓰지 않습니다.

| 공간 | 식별자 | 권한 |
|---|---|---|
| **Figma 프로젝트 `detailed_page_automation`** | **projectId `636598794`** | ✅ **쓰기** — 생성된 Figma 산출물이 쌓이는 **유일한** 곳 |
| 이 git 저장소 | `~/projects/detailed_page_automation*` | ✅ **쓰기** — harness 코드/문서 |
| Figma 파일 `Full_design` | file key `jjgud5OkeXKA4weyP3FEND` | 🔒 **읽기 전용** |
| 같은 팀의 다른 프로젝트 | `Team project`(597088086), `evory`(601372486), `lecture`(597090360) | ⛔ **금지** |
| 개인 Drafts 폴더 | — | ⛔ **금지** (아래 함정 참고) |
| 그 외 모든 것 | 다른 Figma 파일, `~/projects/career`, `evory`, `second_brain` 등 | ⛔ **금지** |

소속 팀은 `euijin lee's team` (planKey `team::1633815531118805138`) 하나뿐이며, 계정은 `appevory@gmail.com` (**Full seat / pro**)입니다.

### ⚠️ 함정: `create_new_file`은 기본값이 Drafts입니다

`create_new_file`에 **`projectId`를 넘기지 않으면 파일이 개인 Drafts 폴더에 생성됩니다.** 이는 쓰기 경계 위반입니다. 반드시 명시하세요.

```jsonc
{
  "planKey":   "team::1633815531118805138",
  "projectId": "636598794",          // ← 절대 생략 금지
  "fileName":  "...",
  "editorType": "design"
}
```

### 그 밖의 금지 사항

- `Full_design`에는 **어떤 노드도 생성·수정·삭제하지 않습니다.** 댓글(comment) 작성도 사용자가 명시적으로 요청할 때만 합니다.
- `use_figma`의 `fileKey`는 **위 프로젝트에 속한 파일**이어야 합니다. 호출 전에 파일이 어느 프로젝트 소속인지 확인하세요 — `GET /v1/projects/636598794/files`에 그 key가 있어야 합니다.
- 저장소 밖 로컬 경로에 파일을 쓰지 않습니다. 임시 파일은 세션 scratchpad를 사용합니다.
- **파일 생성은 되돌릴 수 없습니다.** Figma에는 파일 삭제 API가 없어(노드만 삭제 가능) 잘못 만든 파일은 사용자가 UI에서 수동으로 지워야 합니다. 시험 삼아 파일을 만들지 말고, 반복 작업은 기존 파일 안에서 페이지/프레임 단위로 하세요. → [figma-spaces.md](./figma-spaces.md)

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

`POST /v1/files/...`로 페이지를 만드는 설계는 **성립하지 않습니다.**

**검증 방법** (2026-08-08): Figma 공식 OpenAPI 스펙(`github.com/figma/rest-api-spec`)의 non-GET 엔드포인트는 총 12개이며 전부 comments / webhooks / dev_resources / variables / developer_logs입니다. 노드·파일·프로젝트를 만드는 엔드포인트는 존재하지 않고, 실제로 `POST /v1/files`, `POST /v1/projects`, `POST /v1/files/{key}/nodes` 모두 **HTTP 404**를 반환합니다.

### ✅ 쓰기 경로: Figma 공식 MCP 서버

canvas 쓰기는 **Figma 공식 원격 MCP 서버**로 합니다. 2026년 2월 Claude Code 파트너십으로 write 기능이 출시되어, 프레임·컴포넌트·variables·auto layout을 MCP 클라이언트에서 직접 생성/수정할 수 있습니다.

| 항목 | 값 |
|---|---|
| 서버 URL | `https://mcp.figma.com/mcp` |
| 설치 | `claude mcp add --transport http figma https://mcp.figma.com/mcp` |
| 인증 | Figma OAuth — `/mcp` → figma → Authenticate (**브라우저에서 사용자가 직접 수행**) |
| 조건 | 유료 플랜의 Full 또는 Dev seat. 베타 기간 무료이나 추후 사용량 기반 과금 예정 |
| 주의 | MCP 도구는 **새 세션에서** 로드됩니다 |
| SSH 인증 | `claude mcp login figma --no-browser` — URL을 출력해주면 로컬 브라우저에서 열고, 리다이렉트된 주소창 URL 전체를 터미널에 붙여넣습니다 (`ssh -t` 필요) |

자체 Figma 플러그인을 만들 필요는 없습니다. 공식 MCP를 먼저 검토하세요.

### ✅ 검증된 쓰기 워크플로우 (2026-08-08 실제 성공)

```
1. mcp__figma__whoami              → planKey 확인
2. figma-create-new-file skill 로드 → (필수)
3. mcp__figma__create_new_file      → projectId 636598794 명시! → file_key 획득
4. figma-use skill 로드             → (필수)
5. mcp__figma__use_figma            → Plugin API JS 실행 → 노드 생성
6. REST GET /v1/files/{key}         → 교차 검증
```

**⚠️ skill 선행 로드는 Figma가 강제하는 필수 절차입니다.** `use_figma` 호출 전 `figma-use`, `create_new_file` 호출 전 `figma-create-new-file`을 반드시 읽어야 합니다. 건너뛰면 디버깅하기 어려운 실패가 납니다. Claude Code에 Figma 플러그인이 없으면 MCP 리소스로 읽습니다:

```
ReadMcpResourceTool(server="figma", uri="skill://figma/figma-use/SKILL.md")
```

호출 시 `skillNames`에 `resource:figma-use`를 넘기세요(리소스로 로드한 경우 `resource:` 접두사 필수).

**핵심 API 규칙** (전체는 skill 문서 참조): 색상은 0–1 범위 · 텍스트 수정 전 `loadFontAsync` 필수 · `figma.notify()` 금지 · 페이지 전환은 `await figma.setCurrentPageAsync()` · 생성한 노드 ID를 반드시 `return` · 스크립트는 **원자적**(실패 시 아무것도 안 써짐).

### 프로젝트 ID를 찾는 법

REST에는 팀 목록/프로젝트 검색 API가 없지만, **MCP `whoami`가 planKey를 주므로** 거기서 team ID를 뽑아 REST로 넘어갈 수 있습니다.

```bash
# whoami → "team::1633815531118805138" → team_id = 1633815531118805138
curl -s -H "X-Figma-Token: $TOKEN" \
  "https://api.figma.com/v1/teams/1633815531118805138/projects"
curl -s -H "X-Figma-Token: $TOKEN" \
  "https://api.figma.com/v1/projects/636598794/files"
```

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
| 1 | **한글 폰트 검증** | 쓰기 테스트는 Inter/영문으로만 했음. 상세페이지는 전량 한글이므로 `listAvailableFontsAsync()`로 한글 지원 폰트를 확인하고 기본 폰트를 정해야 함 |
| 2 | 기획안 xlsx 실제 양식 | 아직 샘플 파일 미확보 |
| 3 | 디자인 시스템 입력 형식 | 폰트/색상/키워드를 어떤 파일 형태로 받을지 미정 |
| 4 | Bad 페이지 `Section 4`의 제품명, `토마토 코멘트` 2개 중복 | [figma-spaces.md](./figma-spaces.md) 참고 |
| 5 | 파일 분할 단위 | 제품 1개 = 파일 1개인지, 여러 제품을 한 파일에 페이지로 나눌지 미정 |

### 해결된 항목 (기록)

- ~~Figma 프로젝트 URL/ID~~ → **projectId `636598794`** 확정 (2026-08-08)
- ~~Figma MCP OAuth 인증~~ → 완료, `✔ Connected`
- ~~쓰기 브리지 방식~~ → Figma 공식 MCP로 확정, 실제 쓰기 성공 검증

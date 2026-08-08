# analysis — Full_design 분석 산출물

레퍼런스 코퍼스 `Full_design`(Good 9종 + Bad 5종)을 블록 단위로 분석한 결과물.
**소비자는 상세페이지 생성 에이전트**다. 디자이너 사고 순서의 각 단계에 문서가 1:1로 대응한다.

> 진행 상태: **M1 완료** (파이프라인 + 파일럿 2제품 20블록). M2~M4에서 전수 확장 예정.

## 언제 무엇을 읽나 (progressive disclosure)

| 생성 단계 | 읽을 것 |
|---|---|
| 항상 (골든 프롬프트 상시 로드) | ../rules.md, ../design-principles.md, 이 README |
| 1. 기획안을 장면으로 분해 | [scene-taxonomy.md](./scene-taxonomy.md) |
| 2. 장면별 레이아웃 선택 | [layout-catalog.md](./layout-catalog.md) → 후보 패턴의 예시 노드를 **그 자리에서 스크린샷** |
| 3. 정보 배치 | 카탈로그의 결합 규칙 + 예시 스크린샷 |
| 4. 디자인 시스템 적용 | design-tokens.md *(M3 예정)* + ../fonts.md |
| 특정 제품 통째로 참고 | products/*.md *(M4 예정)*, ../../data/blocks.json |

## 온디맨드 스크린샷 규약

이미지는 저장소에 없다. 카탈로그와 blocks.json의 **노드 ID가 곧 이미지 참조**다:

```
mcp__figma__get_screenshot(fileKey="jjgud5OkeXKA4weyP3FEND", nodeId="1:58")
```

`Full_design` 읽기는 항상 허용(../rules.md §1)이므로 생성 세션 중 언제든 가능하다.

## 데이터 파일

| 파일 | 내용 |
|---|---|
| `data/blocks.json` | 블록 레코드 전체 — 구조 필드(스크립트 산출) + 라벨(scene_type/layout/notes, Claude 판정). 이미지 배경 블록은 `bg_override`가 SOLID 기반 `bg.class`보다 우선 |
| `data/labels/*.json` | 제품별 라벨 원천 (apply_labels.py로 blocks.json에 병합) |
| `data/layout-catalog.json` | *(M4 예정)* 패턴 ID → 예시 노드 기계용 인덱스 |
| `data/raw/` | 원본 캐시 (.gitignore — `scripts/fetch_figma.py`로 재취득) |

## 파이프라인 재실행

```bash
python3 scripts/fetch_figma.py sections        # 구조 스캔 (캐시됨)
python3 scripts/fetch_figma.py all <product>   # 블록 + 스크린샷
python3 scripts/extract_blocks.py <product>    # 구조 필드 → blocks.json (라벨 보존)
python3 scripts/apply_labels.py <product>      # 라벨 병합
python3 scripts/extract_blocks.py --stats      # 요약
```

product 키: `glowshot kkuljam goosemeal olivit cleanse-juice iljin-wire milbat cleanse fileconv` (Good) / `sangha-soup block-soup tomato section4 potato` (Bad) — 매핑은 `scripts/fetch_figma.py`의 `PRODUCTS`.

# scene-taxonomy — 장면(블록) 유형 분류 체계

> 상태: **M3 (Good 9제품 207블록 라벨 완료)** — 서사 전이 통계는 [design-tokens.md §6](./design-tokens.md) 참조.

상세페이지는 **장면(scene)의 세로 시퀀스**다. 기획안을 장면 단위로 분해할 때(디자이너 사고 1단계)
아래 통제 어휘로 각 장면의 역할을 판정한다. 모든 라벨은 `data/blocks.json`에 노드 ID와 함께 기록된다.

## 장면 유형 (통제 어휘)

| scene_type | 역할 | 실측 예시 (블록 노드 ID) |
|---|---|---|
| `hook` | 첫 블록. **소비자의 문제/욕망으로 시작** (제품 자랑 아님) | 글로우샷 `1:4`, 파일변환 `1:84755`, 꿀잠모드 `1:541`, 밀밭명가 `1:82822`, 클렌즈 `1:84518` |
| `problem` | 문제 심화/공감 (말풍선, 인용, 경쟁제품 비판) | 꿀잠모드 `1:558` `1:588`, 올리빗 `1:31210`, 밀밭명가 `1:83277`, 클렌즈 `1:84519` |
| `solution-frame` | 해결의 프레임 제시 — 제품 등장 전 "올바른 방법/이제 보여드림" | 글로우샷 `1:25`, 꿀잠모드 `1:600`, 밀밭명가 `1:83268` |
| `product-reveal` | 제품 첫 등장. 풀블리드 히어로/연출컷 | 글로우샷 `1:46`, 꿀잠모드 `1:578`, 밀밭명가 `1:83266` |
| `product-lineup` | 라인업 각 제품의 각론 소개 (다품목 페이지) | 올리빗 `1:29635` `1:31211` |
| `usp` | 핵심 셀링포인트. **넘버링 연작** (POINT n / 특징 n / check point n) | 글로우샷 `1:58`…, 꿀잠모드 `1:613`…, 밀밭명가 `1:83314`…, 클렌즈 `1:84521`… |
| `comparison` | 비교가 블록의 주목적 (자사 vs 타사, 제품 구분) | 올리빗 `1:21813`, 클렌즈 `1:84527`(자사 라인업 구분) |
| `ingredient-spec` | 성분/원료/재료 소개 | 꿀잠모드 `1:967`(부원료 7종), 올리빗 `1:21817` |
| `transition` | 서사 전환 브릿지 (짧은 스트립 또는 무텍스트 사진) | 글로우샷 `1:90`, 꿀잠모드 `1:598` `1:1067`, 밀밭명가 `1:83333` `1:83447` |
| `trust-cert` | 인증·수상·특허·매장 실재 증명 | 글로우샷 `1:356`(GMP), 꿀잠모드 `1:1134`, 밀밭명가 `1:82923` `1:83106`(수상), 올리빗 `1:29649`(매장), 클렌즈 `1:84528`(입점) |
| `benefit-recap` | 베네핏 감성 재확인 — 컨셉 키워드 회수 | 글로우샷 `1:371`, 꿀잠모드 `1:960`, 올리빗 `1:29648` |
| `target-audience` | "이런 분께 추천" 체크리스트 | 글로우샷 `1:394`, 꿀잠모드 `1:1189`, 올리빗 `1:26487`, 밀밭명가 `1:83590`, 클렌즈 `1:84520` |
| `usage-guide` | 섭취법/사용법/프로그램/숙성 단계 | 글로우샷 `1:427`, 올리빗 `1:21815`, 밀밭명가 `1:83489`, 클렌즈 `1:84522` |
| `tip` | 교육/레시피/건강정보 — **제품과 거리를 둔 콘텐츠로 전문성 신호** | 꿀잠모드 `1:736`(건강정보), 올리빗 `1:23366`(Recipe) `1:28058`, 클렌즈 `1:84524` |
| `review` | 구매후기 (압축 필수 — design-principles F항) | 구스밀 `1:1939`(리뷰 카드 4장, 핵심 문구만 볼드) |
| `cta-offer` | 구성/가격/옵션/이벤트 | 올리빗 `1:24920`(Pricing Guide), 파일변환 `1:84621` 하반부 |
| `faq` | 자주 묻는 질문 | 글로우샷 `1:487`, 올리빗 `1:31205`(8문), 밀밭명가 `1:83641`, 클렌즈 `1:84529` |
| `notice` | 정보고시/영양정보/법적 고지 | 올리빗 `1:31208` `1:31209`, 밀밭명가 `1:83678`, 클렌즈 `1:84530` `1:84531`, 꿀잠모드 `1:585`(연출컷 고지) |
| `brand-story` | 브랜드/창업자 서사 | 올리빗 `1:31207` `1:21814`, 밀밭명가 `1:83688` |

## 제품별 서사 시퀀스 (실측)

```
글로우샷 (이너뷰티 건기식, 14):
  hook → solution-frame → product-reveal → usp×2 → transition → usp×3
       → trust-cert → benefit-recap → target-audience → usage-guide → faq

파일변환 (B2B 서비스, 6):
  hook → usp×3(cta-offer 결합) → usage-guide → faq

꿀잠모드 (수면 건기식, 23):
  hook → problem → product-reveal×2 → notice → problem → transition → solution-frame
       → usp×2(특허) → usp+tip → usp → benefit-recap → ingredient-spec
       → transition → usp → trust-cert → transition×2 → usp → target-audience×2
  ⭐ faq 없이 target-audience로 종료

올리빗 (식품 마리네이드, 21):
  brand-story → problem → transition → product-lineup×2 → cta-offer
       → usp → comparison → brand-story → usage-guide → transition → usp
       → ingredient-spec → trust-cert → target-audience → tip×2
       → benefit-recap → faq → notice×2
  ⭐ 브랜드 원칙 요약으로 시작하는 유일 사례. 가격이 페이지 앞쪽(seq6)

밀밭명가 (김치, 17):
  hook → trust-cert×2 → product-reveal → solution-frame → problem
       → usp → transition → usp → transition → usp → usage-guide → tip
       → target-audience → faq → notice → brand-story
  ⭐ 수상 실적을 훅 직후 전면 배치. brand-story가 정보고시 뒤 맨 끝(감성 여운 종료)

클렌즈 (주스 프로그램, 14 — 래스터):
  hook(+목차) → problem → target-audience → usp → usage-guide → usp → tip
       → usp×2 → comparison → trust-cert → faq → notice×2
  ⭐ target-audience가 앞부분(셀프 진단으로 몰입 유도)

퓨레나 케키바 (클렌즈 주스 섹션의 variant B, 12):
  hook → problem → solution-frame → transition → target-audience
       → usp×4 → cta-offer → faq → notice
  ⭐ 같은 섹션의 variant A(19블록)는 올리빗 대안 시안 중복 — 통계 제외

일진와이어 (B2B 볼트/부속, 6):
  hook(mega-block: 신뢰+usp+배송 통합) → usage-guide×2 → notice → faq×2
  ⭐ 10,616px 메가 블록 1개에 전반부가 통합된 작업 파일. B2B 특성상
     후반 전체가 구매 실무(치수 재는 법, 주문법, 교환/반품, 답변 불가 질문)

구스밀 (식물성 주먹밥, 서사 51블록 + 파편 21):
  hook(목차+셀럽) → ingredient-spec → target-audience → review⭐ → usp 연작(01~06)
       → cta-offer(옵션) → comparison(칼로리) → tip(페어링) → usage-guide(조리법)
       → benefit-recap → notice → cta-offer(쿠폰·배송 배너)
  ⚠️ 캔버스 y 순서가 파편화로 신뢰 불가 — 위는 논리적 재구성
```

## 서사 원칙 (6제품 관찰 — M3 통계로 확정 예정)

1. **문제/욕망으로 열고, 실무 정보로 닫는다.** 6종 중 5종이 소비자 문제로 시작(올리빗만 브랜드 원칙 요약). 마지막은 faq → **notice(정보고시/영양정보)**가 표준 — 식품·건기식은 규정 블록이 실제 최종 블록이다. faq는 필수가 아니다(꿀잠모드).
2. **usp는 넘버링 연작이 6/6.** POINT n(글로우샷·꿀잠·클렌즈) / 특징 n(파일변환) / check point n(올리빗) / Point 0n(밀밭). 페이지 본문의 중심 뼈대.
3. **usp 안에 근거가 내장된다.** 임상 차트·특허증·비교 표·인용 출처가 usp 블록 내부 요소. 독립 "근거 블록"은 없다.
4. **transition이 호흡을 만든다.** 텍스트 스트립("이제 지방을 뺄 차례")과 **무텍스트 원물/제품 사진**(꿀잠모드 3회) 두 방식. usp 연작 사이에 배치.
5. **신뢰 전략은 제품 성격을 따른다**: 건기식 → 임상 데이터+GMP/특허(글로우샷·꿀잠), 로컬 식품 → 수상·매장·CCTV 실재 증명(밀밭·올리빗), 유통 브랜드 → 대형마트 입점(클렌즈). 기획안의 신뢰 자산 종류에 따라 trust-cert 표현을 골라야 한다.
6. **tip(교육 콘텐츠)은 차별화 장치.** "제품과 무관한 정보입니다"를 명시하면서 전문성을 신호(꿀잠모드 건강정보, 올리빗 레시피, 클렌즈 ABC 지식).
7. **후반 표준 마감 시퀀스**: (trust/benefit-recap) → target-audience → usage-guide → faq → notice. 순서는 유동적이나 구성 요소는 안정적.

## 라벨링 규칙

- 한 블록이 두 역할을 겸하면 **주된 역할**을 `scene_type`으로, 부역할은 `notes`에 기록.
- 판정 근거는 시각(스크린샷)과 텍스트 내용 모두 사용. 명시 단어("FAQ", "이용 방법", "Point") 우선.
- **이미지 배경 블록은 `bg_override`가 `bg.class`(SOLID 기반)보다 우선한다** — 래스터/사진 배경에서 SOLID 추출은 흰색으로 오판된다(클렌즈 전 블록, 꿀잠모드 오프닝 등).
- 새 유형 추가 시 이 표를 갱신하고 커밋 메시지에 사유를 남긴다. M2 추가분: `product-lineup`, `tip`.

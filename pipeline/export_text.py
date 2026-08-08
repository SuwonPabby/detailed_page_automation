#!/usr/bin/env python3
"""export_text.py — 텍스트 사이드카 산출 (법적 필수 + SEO)

**왜 필요한가.** 상세페이지를 통 이미지로 굽는 한국 관행은 두 가지 문제를
동시에 만든다:

1. **법적** — 상품정보제공고시 Ⅳ.2: 인증·허가 정보는 *"소비자가 쉽게 알아볼 수
   있는 크기의 문자(Text)"* 로 표시해야 하며 *"인증번호를 확인할 수 없는
   사진으로 대체할 수 없다."* Figma → PNG 파이프라인은 **구조적으로 이 규정을
   위반하게 설계되어 있다.**
2. **SEO** — 이미지 안 텍스트는 색인되지 않는다.

둘의 해법이 같다: **텍스트 이원화.** 이 스크립트가 그 한쪽을 만든다.

산출물은 판매자가 상세정보 **텍스트 영역**에 붙여넣는 용도다. 이미지를 대체하는
것이 아니라 **병행**한다.

사용:
  python3 pipeline/export_text.py <fileKey> <rootNodeId> [-o out_dir]
"""
import argparse
import json
import os
import re
import sys
import urllib.request

ENV = os.path.expanduser("~/projects/detailed_page_automation/.env")
API = "https://api.figma.com/v1"

# 반드시 텍스트로 나가야 하는 항목 (상품정보제공고시 Ⅳ.2 + 전자상거래법 §13)
CERT_PATTERNS = [
    ("특허", re.compile(r"특허\s*(?:제)?\s*[\d\-]{6,}\s*호?")),
    ("인증번호", re.compile(r"(?:KC|인증)\s*[A-Z0-9\-]{5,}")),
    ("심의번호", re.compile(r"심의\s*(?:번호)?\s*[:：]?\s*[A-Z0-9\-]{4,}")),
    ("HACCP", re.compile(r"HACCP")),
]
# 정보고시 성격 블록 (이름 기준)
NOTICE_HINTS = ("고지", "표시사항", "정보고시", "notice")
# 식품(즉석조리식품) 필수 표시항목 — 누락 검사용
REQUIRED_FIELDS = [
    "제품명", "식품유형", "내용량", "원재료명", "영양성분", "소비기한",
    "보관방법", "제조원", "판매원", "원산지", "알레르기", "수입 여부",
    "소비자상담 관련 전화번호",
]


def token():
    with open(ENV) as f:
        for line in f:
            m = re.match(r"\s*FIGMA_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                return m.group(1)
    sys.exit("FIGMA_API_KEY not found")


def api(path, tok):
    req = urllib.request.Request(API + path, headers={"X-Figma-Token": tok})
    return json.load(urllib.request.urlopen(req))


def texts_of(node, out=None):
    out = [] if out is None else out
    if node["type"] == "TEXT":
        s = (node.get("characters") or "").strip()
        if s:
            out.append(s)
    for c in node.get("children") or []:
        texts_of(c, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file_key")
    ap.add_argument("node_id")
    ap.add_argument("-o", "--out", default="data/exports")
    a = ap.parse_args()

    tok = token()
    root = api(f"/files/{a.file_key}/nodes?ids={a.node_id}", tok)["nodes"][a.node_id]["document"]
    blocks = root.get("children") or []

    certs, notices, footnotes = [], [], []
    for b in blocks:
        name = b.get("name", "")
        chunk = texts_of(b)
        joined = "\n".join(chunk)
        for label, rx in CERT_PATTERNS:
            for m in rx.finditer(joined):
                certs.append((label, m.group(0).strip(), name))
        if any(h in name for h in NOTICE_HINTS):
            notices.append((name, chunk))
        for s in chunk:
            if s.lstrip()[:1] in ("*", "※"):
                footnotes.append((name, s.strip()))

    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, a.file_key)

    lines = ["# 상세정보 텍스트 (이미지와 **병행** 게재)", "",
             "> 상품정보제공고시 Ⅳ.2 — 인증·허가 정보는 문자(Text)로 표시해야 하며",
             "> 인증번호를 확인할 수 없는 사진으로 대체할 수 없습니다.",
             "> 이 파일의 내용을 상세정보 **텍스트 영역**에 그대로 게재하세요.", ""]

    lines += ["## 인증·허가 정보 (텍스트 게재 필수)", ""]
    if certs:
        seen = set()
        for label, val, where in certs:
            if val in seen:
                continue
            seen.add(val)
            lines.append(f"- **{label}**: {val}  <!-- 출처 블록: {where} -->")
    else:
        lines.append("- (검출된 인증·허가 번호 없음)")
    lines.append("")

    lines += ["## 필수 표시사항", ""]
    if notices:
        for name, chunk in notices:
            for s in chunk:
                lines.append(f"- {s}")
    else:
        lines.append("- (정보고시 블록을 찾지 못했습니다)")
    lines.append("")

    # 누락 검사
    body = "\n".join(sum((c for _, c in notices), []))
    missing = [f for f in REQUIRED_FIELDS if f not in body]
    lines += ["## ⚠️ 누락 의심 항목", ""]
    if missing:
        lines.append("아래 항목이 페이지 텍스트에서 발견되지 않았습니다. "
                     "전자상거래법 §13 + 상품정보제공고시상 통신판매 필수 기재입니다:")
        lines.append("")
        for f in missing:
            lines.append(f"- [ ] {f}")
    else:
        lines.append("없음")
    lines.append("")

    lines += ["## 각주·고지 문구", ""]
    for name, s in footnotes:
        lines.append(f"- {s}")
    lines.append("")
    lines += ["## 검색 노출용 키워드 (이미지 속 텍스트는 색인되지 않음)", "",
              "상품명·태그·구조화 상품정보에 아래 핵심어를 병기하세요:", ""]
    heads = []
    for b in blocks:
        ch = texts_of(b)
        if ch:
            heads.append(ch[0] if len(ch[0]) < 40 else ch[0][:40])
    lines.append(", ".join(dict.fromkeys(heads)))

    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"{base}.md")
    print(f"  인증·허가 {len(set(v for _, v, _ in certs))}건 · 정보고시 블록 {len(notices)}개 "
          f"· 각주 {len(footnotes)}건")
    if missing:
        print(f"  ⚠️ 누락 의심 {len(missing)}개: {', '.join(missing)}")


if __name__ == "__main__":
    main()

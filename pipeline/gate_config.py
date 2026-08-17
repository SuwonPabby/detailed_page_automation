#!/usr/bin/env python3
"""gate_config.py — 입력 검증 레이어 2: config 접근 가능성 검증

레이어 1(입력물)은 parse_brief.py + gate_assets.py가 담당한다. 이 게이트는
사람 관할 config(config/*.json)가 전부 **실제로 접근 가능한지**를 검증한다.
둘 다 통과해야 파이프라인이 다음으로 넘어간다.

검증 항목:
  1. templates  — 템플릿 Figma 파일이 API로 열리는가
  2. references — 레퍼런스 파일이 열리는가
  3. fonts      — 허용 목록의 폰트가 전부 Figma 클라우드에 있는가
                  (폰트 목록은 REST로 못 얻으므로 use_figma 덤프 파일을 받는다)
  4. compliance — 규정 문서가 존재하는가
  5. platform   — 규격 값이 유효한가

사용:
  # 1) 에이전트가 use_figma로 폰트 덤프 생성:
  #    return (await figma.listAvailableFontsAsync()).map(f=>f.fontName)
  #    → [{family,style},...] 를 /tmp/figma_fonts.json 에 저장
  python3 pipeline/gate_config.py --fonts /tmp/figma_fonts.json
  python3 pipeline/gate_config.py --skip-fonts        # 폰트 제외 (불완전 통과)
종료코드: 0 = 전부 접근 가능, 1 = 반려
"""
import argparse
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(REPO, "config")
ENV = os.path.join(REPO, ".env")


def token():
    for line in open(ENV):
        m = re.match(r"\s*FIGMA_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
        if m:
            return m.group(1)
    return None


def cfg(name):
    return json.load(open(os.path.join(CFG, name)))


def figma_file_ok(file_key, tok):
    try:
        req = urllib.request.Request(
            f"https://api.figma.com/v1/files/{file_key}?depth=1",
            headers={"X-Figma-Token": tok})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        return d.get("name")
    except Exception as e:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", help="use_figma listAvailableFontsAsync 덤프 json")
    ap.add_argument("--skip-fonts", action="store_true")
    a = ap.parse_args()

    errors, ok = [], []

    # 0. config 파일 자체
    for f in ("templates.json", "fonts.json", "references.json",
              "compliance.json", "platform.json"):
        if not os.path.isfile(os.path.join(CFG, f)):
            errors.append(f"config/{f} 없음")
    if errors:
        for e in errors:
            print(f"❌ {e}")
        sys.exit(1)

    tok = token()
    if not tok:
        errors.append(".env의 FIGMA_API_KEY를 읽을 수 없음")

    # 1. 템플릿 파일 접근
    if tok:
        t = cfg("templates.json")
        name = figma_file_ok(t["file_key"], tok)
        (ok.append(f"templates: '{name}' 접근 가능") if name
         else errors.append(f"templates: {t['file_key']} 접근 불가"))

        # 2. 레퍼런스 파일 접근
        r = cfg("references.json")
        name = figma_file_ok(r["file_key"], tok)
        (ok.append(f"references: '{name}' 접근 가능") if name
         else errors.append(f"references: {r['file_key']} 접근 불가"))

    # 3. 폰트 전수 확인
    if a.skip_fonts:
        ok.append("fonts: SKIP (불완전 통과 — 빌드 전 반드시 검증할 것)")
    elif not a.fonts:
        errors.append("fonts: 덤프 미제공 — use_figma로 listAvailableFontsAsync 결과를 "
                      "json 저장 후 --fonts로 전달하라 (또는 --skip-fonts)")
    else:
        try:
            dump = json.load(open(a.fonts))
            have = {(f["family"], f["style"]) for f in dump}
            missing = []
            for fam, styles in cfg("fonts.json")["allowed"].items():
                for st in styles:
                    if (fam, st) not in have:
                        missing.append(f"{fam} {st}")
            (errors.append(f"fonts: 허용 목록 중 미설치 {len(missing)}건 — "
                           + ", ".join(missing[:6])) if missing
             else ok.append(f"fonts: 허용 {sum(len(v) for v in cfg('fonts.json')['allowed'].values())}"
                            f"개 스타일 전부 사용 가능"))
        except (OSError, json.JSONDecodeError, KeyError) as e:
            errors.append(f"fonts: 덤프 파싱 실패 ({e})")

    # 4. compliance 문서
    doc = os.path.join(REPO, cfg("compliance.json")["doc"])
    (ok.append(f"compliance: {cfg('compliance.json')['doc']} 존재") if os.path.isfile(doc)
     else errors.append(f"compliance: {doc} 없음"))

    # 5. platform 규격
    p = cfg("platform.json")
    if isinstance(p.get("canvas_width"), int) and 300 <= p["canvas_width"] <= 2000:
        ok.append(f"platform: canvas {p['canvas_width']}px")
    else:
        errors.append(f"platform: canvas_width 값 이상 ({p.get('canvas_width')})")

    for o in ok:
        print(f"✅ {o}")
    for e in errors:
        print(f"❌ {e}")
    print(f"\n{'✅ config 검증 통과' if not errors else '🚫 반려 — 해결 전 진행 금지'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

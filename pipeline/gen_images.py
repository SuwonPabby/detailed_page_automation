#!/usr/bin/env python3
"""gen_images.py — 이미지 슬롯 채우기 (provider 추상화)

역할: Figma 산출물의 `IMG_*` 플레이스홀더를 읽어, 각 슬롯의 설명문으로
이미지를 생성하고 `data/assets/<fileKey>/`에 저장한다.
**업로드는 이 스크립트가 하지 않는다** — `mcp__figma__upload_assets(nodeId)`가
MCP 전용이므로 에이전트가 수행한다. 이 스크립트는 생성까지만 담당하고
업로드 매핑(json)을 남긴다.

Provider 선정 (2026-08-09 사용자 확정):
  - ⭐ 주력: **Higgsfield** — 공식 MCP(https://mcp.higgsfield.ai/mcp)로 구독
    크레딧을 에이전트가 직접 소모하는 유일한 경로. 사용자 결정으로 1순위.
    이미지 생성은 이 스크립트가 아니라 **에이전트가 Higgsfield MCP 도구로** 수행.
    (선행 조건: `claude mcp login higgsfield` 인증 + 새 세션에서 도구 로드)
  - 폴백: gemini(Nano Banana Pro/3.1 Flash), flux(FLUX.2 Pro) — Higgsfield
    불가·크레딧 소진 시에만. 이 스크립트의 API 경로는 폴백 전용.
  - GPT Image 2: 구독으로 API 불가 확정(별도 종량제), 우회는 ToS 위반 → 탈락

법적 하드 게이트 (docs/compliance.md §5-1):
  1. 제품 실물컷은 AI 생성 금지 — 배경·질감·일반 재료 플랫레이만 (--role 강제)
  2. 신선식품·유아식품·건기식 카테고리는 생성 자체 블록
  3. 1장이라도 쓰면 AI 활용 고지 텍스트 필수 → 매핑 json에 플래그 기록

키: ~/projects/detailed_page_automation/.env 에
  GEMINI_API_KEY = '...'   또는   BFL_API_KEY = '...'

사용:
  python3 pipeline/gen_images.py list <fileKey> <rootNodeId>      # 슬롯 인벤토리
  python3 pipeline/gen_images.py gen  <fileKey> <slots.json>      # 생성 실행
"""
import argparse
import base64
import json
import os
import re
import sys
import urllib.request

ENV = os.path.expanduser("~/projects/detailed_page_automation/.env")
FIGMA_API = "https://api.figma.com/v1"

# 제품 실물을 지칭하는 슬롯은 AI 생성 대상에서 제외한다 (compliance §5-1 규칙 1)
PRODUCT_HINTS = ("제품컷", "실물", "라인업", "단면", "패키지", "인물", "모델")

# 모든 T1 생성 프롬프트에 강제되는 하우스 포토그래피 접미사 — "AI 티" 원천 차단.
# Higgsfield MCP 경로(에이전트 직접 생성)에서도 동일 문구를 쓴다 (SKILL.md §2-2.5).
PHOTO_SUFFIX = (
    " Shot on 85mm lens, Kodak Portra 400 film look, natural window light "
    "from one side, shallow depth of field, subtle film grain, natural tonal "
    "variation, slight real-world imperfections, candid off-center composition.")
BLOCKED_CATEGORIES = ("신선식품", "농산물", "축산물", "수산물", "유아", "건강기능식품", "건기식")


def env(key):
    with open(ENV) as f:
        for line in f:
            m = re.match(rf"\s*{key}\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                return m.group(1)
    return None


def figma(path):
    tok = env("FIGMA_API_KEY") or sys.exit("FIGMA_API_KEY not found")
    req = urllib.request.Request(FIGMA_API + path, headers={"X-Figma-Token": tok})
    return json.load(urllib.request.urlopen(req))


def find_slots(node, out=None):
    out = [] if out is None else out
    name = node.get("name", "")
    if name.startswith("IMG_"):
        bb = node.get("absoluteBoundingBox") or {}
        desc = name[4:]
        role = "product" if any(h in desc for h in PRODUCT_HINTS) else "visual"
        out.append({
            "nodeId": node["id"], "desc": desc, "role": role,
            "w": round(bb.get("width", 0)), "h": round(bb.get("height", 0)),
        })
    for c in node.get("children") or []:
        find_slots(c, out)
    return out


# ── providers ─────────────────────────────────────────────────────────
def gen_gemini(prompt, w, h, tier):
    """tier: 'hero' → Nano Banana Pro / 'bg' → 3.1 Flash (모델 ID는 .env로 교체 가능)"""
    key = env("GEMINI_API_KEY") or sys.exit("GEMINI_API_KEY not in .env")
    model = env("GEMINI_HERO_MODEL" if tier == "hero" else "GEMINI_BG_MODEL") \
        or ("gemini-3-pro-image" if tier == "hero" else "gemini-3.1-flash-image")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    ar = f"{w}:{h}" if w and h else "1:1"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": _near_ar(w, h)}},
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    resp = json.load(urllib.request.urlopen(req))
    for part in resp["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            return base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError("no image in response")


def gen_flux(prompt, w, h, tier):
    key = env("BFL_API_KEY") or sys.exit("BFL_API_KEY not in .env")
    body = json.dumps({"prompt": prompt, "width": min(w or 1024, 1440),
                       "height": min(h or 1024, 1440)}).encode()
    req = urllib.request.Request("https://api.bfl.ai/v1/flux-2-pro", data=body,
                                 headers={"Content-Type": "application/json",
                                          "x-key": key})
    task = json.load(urllib.request.urlopen(req))
    import time
    for _ in range(60):
        time.sleep(2)
        r = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://api.bfl.ai/v1/get_result?id={task['id']}",
            headers={"x-key": key})))
        if r.get("status") == "Ready":
            return urllib.request.urlopen(r["result"]["sample"]).read()
    raise TimeoutError("flux polling timed out")


PROVIDERS = {"gemini": gen_gemini, "flux": gen_flux}


def _near_ar(w, h):
    """지원 종횡비로 스냅"""
    if not w or not h:
        return "1:1"
    r = w / h
    table = [("21:9", 21/9), ("16:9", 16/9), ("3:2", 1.5), ("4:3", 4/3),
             ("1:1", 1.0), ("3:4", 0.75), ("2:3", 2/3), ("9:16", 9/16)]
    return min(table, key=lambda t: abs(t[1] - r))[0]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("list")
    p1.add_argument("file_key"); p1.add_argument("node_id")
    p2 = sub.add_parser("gen")
    p2.add_argument("file_key"); p2.add_argument("slots_json")
    p2.add_argument("--provider", default="gemini", choices=list(PROVIDERS))
    p2.add_argument("--category", default="일반가공식품",
                    help="기획안 식품유형 — 금지 카테고리면 하드 블록")
    a = ap.parse_args()

    if a.cmd == "list":
        root = figma(f"/files/{a.file_key}/nodes?ids={a.node_id}")["nodes"][a.node_id]["document"]
        slots = find_slots(root)
        print(json.dumps(slots, ensure_ascii=False, indent=1))
        prod = [s for s in slots if s["role"] == "product"]
        print(f"\n# 슬롯 {len(slots)}개 — AI 생성 가능 {len(slots)-len(prod)} / "
              f"제품 실물(생성 금지, 실사 필요) {len(prod)}", file=sys.stderr)
        return

    # gen
    if any(b in a.category for b in BLOCKED_CATEGORIES):
        sys.exit(f"⛔ '{a.category}'는 네이버 AI 이미지 원천 금지 카테고리다 "
                 f"(compliance §5-1). 생성을 중단한다.")
    slots = json.load(open(a.slots_json))
    outdir = os.path.join("data", "assets", a.file_key)
    os.makedirs(outdir, exist_ok=True)
    mapping = {"provider": a.provider, "ai_disclosure_required": False, "items": []}
    for i, s in enumerate(slots):
        if s["role"] == "product":
            print(f"skip (제품 실물 — AI 금지): {s['desc']}")
            continue
        prompt = s.get("prompt") or (
            f"Commercial food-brand background visual for a Korean e-commerce "
            f"detail page. {s['desc']}. No text, no letters, no people, no logos. "
            f"Natural light, realistic textures, muted deep-green brand mood.")
        # 하우스 포토그래피 접미사 (P1 방어 — agent-architecture.md §1 3단계):
        # 필름 질감·조명 방향·의도적 불완전성. 과잉완성어(8k/masterpiece)는 쓰지 않는다.
        prompt += PHOTO_SUFFIX
        tier = "hero" if max(s.get("w", 0), s.get("h", 0)) >= 700 else "bg"
        png = PROVIDERS[a.provider](prompt, s.get("w"), s.get("h"), tier)
        fn = os.path.join(outdir, f"slot_{i:02d}.png")   # ASCII 파일명 (한글은 mojibake)
        with open(fn, "wb") as f:
            f.write(png)
        mapping["items"].append({"nodeId": s["nodeId"], "file": fn, "desc": s["desc"]})
        mapping["ai_disclosure_required"] = True
        print(f"✓ {s['desc']} → {fn}")
    mpath = os.path.join(outdir, "mapping.json")
    json.dump(mapping, open(mpath, "w"), ensure_ascii=False, indent=1)
    print(f"\n매핑: {mpath}")
    if mapping["ai_disclosure_required"]:
        print("⚠️ AI 활용 고지 텍스트를 하단 정보고시에 삽입해야 한다 (compliance §5-1 규칙 3)")
    print("다음 단계(에이전트): mcp__figma__upload_assets(fileKey, nodeId=...) → "
          "submitUrl에 curl -F 'file=@slot_XX.png;type=image/png' POST")


if __name__ == "__main__":
    main()

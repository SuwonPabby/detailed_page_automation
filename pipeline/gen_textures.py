#!/usr/bin/env python3
"""gen_textures.py — 외부 API 없이 절차적으로 배경 텍스처를 생성한다 (PIL만 사용).

용도: craft-axioms의 표면(§4)·장식(F8)·중성색 물들이기(F10)를 이미지 레이어로 보강.
생성물은 타일링 가능한 PNG로, Figma에는 upload_assets → imageHash를 얻어
[SOLID 베이스, IMAGE(저불투명·TILE)] 순서의 레이어드 fill로 얹는다 —
SOLID를 유지해야 qa_check.py의 명도 계산이 결정론적으로 남는다.

사용: python3 pipeline/gen_textures.py [출력폴더=data/assets/textures]
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SEED = 23  # 디자인23 — 재현 가능해야 한다


def noise_layer(size, amp=18, base=128, blur=0):
    """모노 그레인. amp=진폭, base=중심 밝기."""
    rnd = random.Random(SEED)
    img = Image.new("L", (size, size))
    img.putdata([max(0, min(255, int(rnd.gauss(base, amp)))) for _ in range(size * size)])
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    return img


def fibers(size, n, color, width, rng):
    """종이 섬유 — 짧은 곡선 스트로크를 흩뿌린다."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        ln = rng.uniform(6, 22)
        ang = rng.uniform(0, 3.14159)
        import math
        dx, dy = math.cos(ang) * ln, math.sin(ang) * ln
        a = int(rng.uniform(22, 58))
        d.line([(x, y), (x + dx, y + dy)], fill=(*color, a), width=width)
    return layer


def tileable(img):
    """가장자리 이음새 완화: 절반 오프셋 후 중앙 블렌드."""
    size = img.size[0]
    off = Image.new("RGBA", img.size)
    half = size // 2
    off.paste(img.crop((half, half, size, size)), (0, 0))
    off.paste(img.crop((0, half, half, size)), (half, 0))
    off.paste(img.crop((half, 0, size, half)), (0, half))
    off.paste(img.crop((0, 0, half, half)), (half, half))
    return Image.blend(img, off, 0.5)


def grain_mono(path, size=512):
    """1) 미세 그레인 (다크 블록용, SOFT_LIGHT/OVERLAY 저불투명)."""
    g = noise_layer(size, amp=26, base=128)
    g.convert("RGBA").save(path)


def kraft_paper(path, size=640):
    """2) 크래프트지 — 웜 베이지 + 섬유 + 그레인 (라이트 블록용)."""
    rng = random.Random(SEED + 1)
    base = Image.new("RGBA", (size, size), (233, 224, 207, 255))
    n = noise_layer(size, amp=9, base=128, blur=0)
    speck = Image.merge("RGBA", (n, n, n, Image.new("L", (size, size), 40)))
    img = Image.alpha_composite(base, speck)
    img = Image.alpha_composite(img, fibers(size, 1300, (146, 126, 92), 1, rng))
    img = Image.alpha_composite(img, fibers(size, 450, (255, 252, 244), 1, rng))
    tileable(img).save(path)


def hanji_green(path, size=640):
    """3) 딥그린 물든 한지결 — 훅/클로징 다크 블록용 표면."""
    rng = random.Random(SEED + 2)
    base = Image.new("RGBA", (size, size), (18, 61, 38, 255))       # #123D26
    n = noise_layer(size, amp=12, base=120, blur=1)
    speck = Image.merge("RGBA", (n, n, n, Image.new("L", (size, size), 52)))
    img = Image.alpha_composite(base, speck)
    img = Image.alpha_composite(img, fibers(size, 950, (52, 112, 76), 1, rng))
    img = Image.alpha_composite(img, fibers(size, 260, (8, 26, 17), 2, rng))
    tileable(img).save(path)


def grain_scatter(path, size=640):
    """4) 곡물 낟알 스캐터 — 장식 레이어용(제품 컨셉 파생: 12곡 주먹밥)."""
    rng = random.Random(SEED + 3)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palette = [(233, 185, 73), (150, 132, 100), (110, 140, 96), (94, 70, 48)]
    for _ in range(90):
        x, y = rng.uniform(0, size), rng.uniform(0, size)
        w = rng.uniform(3.2, 7.5)
        h = w * rng.uniform(1.6, 2.3)
        ang = rng.uniform(0, 360)
        a = int(rng.uniform(28, 70))
        seed_img = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
        sd = ImageDraw.Draw(seed_img)
        c = palette[rng.randrange(len(palette))]
        sd.ellipse([12 - w / 2, 12 - h / 2, 12 + w / 2, 12 + h / 2], fill=(*c, a))
        seed_img = seed_img.rotate(ang, resample=Image.BICUBIC)
        img.alpha_composite(seed_img, (int(x) - 12, int(y) - 12))
    img.save(path)


def _paper_hi(path, size, base, fiber_color, n_fiber, blotch_color, n_blotch, seed, tint):
    """명도 중립·고대비 종이 타일 (v6 실측 교훈 — backlog B6).

    구 hanji_green은 mean 60·σ 1.0 — 어둡기만 하고 질감이 없어, MULTIPLY로 얹으면
    블록 명도만 끌어내리고 육안 질감은 0이었다. 처방은 불투명 조절이 아니라 타일 자체:
    **밝은 바탕(mean≈237) + 섬유·반점이 σ를 만든다** → MULTIPLY 0.85~0.9에서도
    SOLID 명도 이탈이 작고(≈×0.94) 질감이 실제로 보인다.
    """
    import math
    rnd = random.Random(seed)
    img = Image.new("RGB", (size, size), base)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(n_blotch):
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        r = rnd.uniform(6, 26)
        d.ellipse([x - r, y - r, x + r, y + r], fill=blotch_color + (rnd.randint(10, 26),))
    img = img.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(n_fiber):
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        ang = rnd.uniform(0, math.pi)
        L = rnd.uniform(8, 30)
        pts = [(x, y)]
        for _ in range(3):
            ang += rnd.uniform(-0.5, 0.5)
            x += math.cos(ang) * L / 3
            y += math.sin(ang) * L / 3
            pts.append((x, y))
        d.line(pts, fill=fiber_color + (rnd.randint(26, 60),), width=1)
    img = Image.blend(img, Image.new("RGB", (size, size), tint), 0.06)
    img.save(path)
    # 자기검증 (B6): 밝고(σ가 보일 만큼) 대비가 실재하는지
    from PIL import ImageStat
    st = ImageStat.Stat(img.convert("L"))
    assert st.mean[0] > 220 and st.stddev[0] > 5, \
        f"{path.name}: mean={st.mean[0]:.0f} σ={st.stddev[0]:.1f} — 명도중립·가시성 기준 미달"


def hanji_hi(path, size=512):
    """한지(그린 틴트) — 밝은 오프화이트 블록용. v6 05·14 검증."""
    _paper_hi(path, size, (243, 245, 239), (110, 130, 105), 2600,
              (170, 185, 160), 90, seed=SEED, tint=(210, 225, 205))


def kraft_hi(path, size=512):
    """크래프트지(웜 틴트) — 정보 스트립·웜 크림 블록용."""
    _paper_hi(path, size, (242, 238, 228), (150, 125, 90), 2200,
              (200, 180, 140), 110, seed=SEED * 2, tint=(225, 210, 180))


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "data" / "assets" / "textures"
    out.mkdir(parents=True, exist_ok=True)
    grain_mono(out / "grain_mono.png")
    kraft_paper(out / "kraft_paper.png")
    hanji_green(out / "hanji_green.png")
    grain_scatter(out / "grain_scatter.png")
    hanji_hi(out / "hanji_hi.png")
    kraft_hi(out / "kraft_hi.png")
    for p in sorted(out.glob("*.png")):
        print(p.name, p.stat().st_size, "bytes")


if __name__ == "__main__":
    main()

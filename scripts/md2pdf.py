#!/usr/bin/env python3
"""md2pdf.py — 한글 마크다운 문서를 PDF로 변환 (fpdf2 + 시스템 한글 폰트)

pandoc/chrome 없는 환경용 경량 변환기. 매뉴얼 수준의 마크다운 부분집합만 지원:
  # ~ ### 제목 / 불릿·번호 목록 / 표 / 4칸 들여쓰기 코드 블록 / 문단

사용: python3 scripts/md2pdf.py <in.md> <out.pdf>
의존: python3 -m pip install --user --break-system-packages fpdf2
"""
import re
import sys

from fpdf import FPDF

FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"  # 컬렉션 0번 = Regular
MARGIN = 18
INK = (31, 31, 28)        # docs 팔레트 text
ACCENT = (0, 80, 39)      # dominant green
RULE = (200, 205, 198)


class Doc(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.add_font("KR", fname=FONT, collection_font_number=0)
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(True, margin=MARGIN)
        self.add_page()

    def footer(self):
        self.set_y(-12)
        self.set_font("KR", size=8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 8, f"{self.page_no()}", align="C")

    def body_width(self):
        return self.w - self.l_margin - self.r_margin


def clean(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s


def table(pdf, rows):
    cols = max(len(r) for r in rows)
    w = pdf.body_width() / cols
    for ri, row in enumerate(rows):
        row = row + [""] * (cols - len(row))
        # 줄바꿈 필요 높이 계산
        pdf.set_font("KR", size=8.6)
        lines = 1
        for c in row:
            n = len(pdf.multi_cell(w - 2, 4.6, clean(c), dry_run=True,
                                   output="LINES"))
            lines = max(lines, n)
        h = lines * 4.6 + 2.4
        if pdf.get_y() + h > pdf.h - MARGIN:
            pdf.add_page()
        y0 = pdf.get_y()
        for ci, c in enumerate(row):
            x0 = pdf.l_margin + ci * w
            pdf.set_xy(x0, y0)
            if ri == 0:
                pdf.set_fill_color(*ACCENT)
                pdf.set_text_color(255, 255, 255)
            else:
                pdf.set_fill_color(255, 255, 255) if ri % 2 else \
                    pdf.set_fill_color(243, 246, 241)
                pdf.set_text_color(*INK)
            pdf.set_draw_color(*RULE)
            pdf.rect(x0, y0, w, h, style="DF" if (ri == 0 or ri % 2 == 0) else "D")
            pdf.set_xy(x0 + 1, y0 + 1.2)
            pdf.multi_cell(w - 2, 4.6, clean(c))
        pdf.set_y(y0 + h)
    pdf.ln(2.5)


def render(pdf, md):
    lines = md.splitlines()
    i, para, tbl = 0, [], []

    def flush_para():
        if para:
            pdf.set_font("KR", size=9.6)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 5.4, clean(" ".join(para)))
            pdf.ln(1.6)
            para.clear()

    def flush_tbl():
        if tbl:
            table(pdf, tbl)
            tbl.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        # 표
        if ln.startswith("|"):
            flush_para()
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                tbl.append(cells)
            i += 1
            continue
        flush_tbl()
        # 코드 블록 (4칸 들여쓰기)
        if ln.startswith("    ") and not para:
            flush_para()
            block = []
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                if lines[i].strip() or block:
                    block.append(lines[i][4:] if lines[i].startswith("    ") else "")
                i += 1
            while block and not block[-1].strip():
                block.pop()
            pdf.set_fill_color(243, 246, 241)
            pdf.set_font("KR", size=8.4)
            pdf.set_text_color(20, 60, 40)
            pdf.multi_cell(0, 4.8, "\n".join(block), fill=True,
                           new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            continue
        # 제목
        m = re.match(r"(#{1,3})\s+(.*)", ln)
        if m:
            flush_para()
            lvl, txt = len(m.group(1)), clean(m.group(2))
            size = {1: 17, 2: 12.5, 3: 10.5}[lvl]
            if lvl == 2 and pdf.get_y() > pdf.h * 0.78:
                pdf.add_page()
            pdf.ln(3 if lvl > 1 else 1)
            pdf.set_font("KR", size=size)
            pdf.set_text_color(*(ACCENT if lvl <= 2 else INK))
            pdf.multi_cell(0, size * 0.52, txt)
            if lvl == 1:
                pdf.set_draw_color(*ACCENT)
                pdf.set_line_width(0.6)
                pdf.line(MARGIN, pdf.get_y() + 1, pdf.w - MARGIN, pdf.get_y() + 1)
                pdf.ln(4)
            else:
                pdf.ln(1.6)
            i += 1
            continue
        # 목록
        m = re.match(r"(\s*)([-*]|\d+\.)\s+(.*)", ln)
        if m:
            flush_para()
            indent = 4 + len(m.group(1)) * 1.6
            bullet = "•" if m.group(2) in "-*" else m.group(2)
            pdf.set_font("KR", size=9.6)
            pdf.set_text_color(*INK)
            pdf.set_x(MARGIN + indent)
            pdf.multi_cell(pdf.body_width() - indent, 5.4,
                           f"{bullet} {clean(m.group(3))}")
            pdf.ln(0.6)
            i += 1
            continue
        # 빈 줄 / 문단
        if not ln.strip():
            flush_para()
        else:
            para.append(ln.strip())
        i += 1
    flush_para()
    flush_tbl()


def main():
    if len(sys.argv) != 3:
        sys.exit("사용: python3 scripts/md2pdf.py <in.md> <out.pdf>")
    pdf = Doc()
    render(pdf, open(sys.argv[1], encoding="utf-8").read())
    pdf.output(sys.argv[2])
    print(f"OK → {sys.argv[2]} ({pdf.page_no()}p)")


if __name__ == "__main__":
    main()

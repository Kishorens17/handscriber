# -*- coding: utf-8 -*-
"""
note_renderer.py — Paper Renderer (HandScribe v2.1)

Key improvements:
  - Pixel-accurate text wrapping  → fills full page width correctly
  - Unicode / symbol substitution → no more □ boxes for Ω, ρ, etc.
  - Heading-aware rendering       → larger font + bold effect + underline + spacing
  - Better section breathing room → visual hierarchy between sections
"""

import sys
import io
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Directories ───────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent / "assets"
FONTS_DIR  = ASSETS_DIR / "fonts"
OUTPUT_DIR = Path(__file__).parent / "output"

# ── Page dimensions — A4 at 150 DPI ──────────────────────────────────────────
PAGE_W = 1240
PAGE_H = 1754

# ── Layout ────────────────────────────────────────────────────────────────────
MARGIN_LEFT   = 75
MARGIN_RIGHT  = 65       # slightly narrower right margin so text fills the page
MARGIN_TOP    = 140
MARGIN_BOTTOM = 70
LINE_SPACING  = 56       # slightly more breathing room
FONT_SIZE     = 36
INK_COLOR     = (15, 30, 80)

# ── Font registry ─────────────────────────────────────────────────────────────
FONTS = {
    "Caveat": {
        "file": "Caveat-Regular.ttf",
        "url":  "https://github.com/google/fonts/raw/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
    },
    "Patrick Hand": {
        "file": "PatrickHand-Regular.ttf",
        "url":  "https://github.com/google/fonts/raw/main/ofl/patrickhand/PatrickHand-Regular.ttf",
    },
    "Kalam": {
        "file": "Kalam-Regular.ttf",
        "url":  "https://github.com/google/fonts/raw/main/ofl/kalam/Kalam-Regular.ttf",
    },
    "Architects Daughter": {
        "file": "ArchitectsDaughter-Regular.ttf",
        "url":  "https://github.com/google/fonts/raw/main/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Font loading
# ─────────────────────────────────────────────────────────────────────────────

def _download_font(font_name: str = "Caveat") -> Path:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    info = FONTS.get(font_name, FONTS["Caveat"])
    font_path = FONTS_DIR / info["file"]
    legacy = ASSETS_DIR / "Caveat-Regular.ttf"
    if font_name == "Caveat" and legacy.exists() and not font_path.exists():
        shutil.copy(legacy, font_path)
        return font_path
    if font_path.exists():
        return font_path
    print(f"Downloading {font_name} font …")
    r = requests.get(info["url"], timeout=20)
    r.raise_for_status()
    font_path.write_bytes(r.content)
    print(f"  ✅  {font_name} saved to {font_path}")
    return font_path


def _load_font(font_name: str = "Caveat", size: int = FONT_SIZE) -> ImageFont.FreeTypeFont:
    try:
        path = _download_font(font_name)
        return ImageFont.truetype(str(path), size)
    except Exception as exc:
        print(f"⚠️  Font '{font_name}' failed ({exc}). Using default.")
        return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# Paper generators
# ─────────────────────────────────────────────────────────────────────────────

def _make_lined(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (253, 251, 240))
    draw = ImageDraw.Draw(img)
    draw.line([(MARGIN_LEFT - 12, 0), (MARGIN_LEFT - 12, h)], fill=(210, 65, 65), width=2)
    y = MARGIN_TOP
    while y < h - MARGIN_BOTTOM:
        draw.line([(0, y), (w, y)], fill=(175, 195, 225), width=1)
        y += LINE_SPACING
    return img

def _make_white(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(4, 4), (w - 5, h - 5)], outline=(228, 228, 228), width=2)
    return img

def _make_graph(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    minor, major = 26, 130
    for x in range(0, w, minor): draw.line([(x,0),(x,h)], fill=(195,215,240), width=1)
    for y in range(0, h, minor): draw.line([(0,y),(w,y)], fill=(195,215,240), width=1)
    for x in range(0, w, major): draw.line([(x,0),(x,h)], fill=(145,180,220), width=2)
    for y in range(0, h, major): draw.line([(0,y),(w,y)], fill=(145,180,220), width=2)
    return img

def _make_dot_grid(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (252, 252, 250))
    draw = ImageDraw.Draw(img)
    step = 36
    for x in range(45, w - 20, step):
        for y in range(45, h - 20, step):
            draw.ellipse([(x-2,y-2),(x+2,y+2)], fill=(185,185,200))
    return img

def _make_legal_pad(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (255, 252, 195))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(w,78)], fill=(255,246,140))
    draw.line([(0,78),(w,78)], fill=(200,55,55), width=2)
    lbl  = _load_font("Caveat", 26)
    draw.text((w//2, 40), "LEGAL PAD", font=lbl, fill=(160,55,55), anchor="mm")
    draw.line([(MARGIN_LEFT-12, 78),(MARGIN_LEFT-12, h)], fill=(200,55,55), width=2)
    y = MARGIN_TOP
    while y < h - MARGIN_BOTTOM:
        draw.line([(0,y),(w,y)], fill=(140,175,215), width=1)
        y += LINE_SPACING
    return img

def _make_cornell(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (252, 250, 242))
    draw = ImageDraw.Draw(img)
    cue_x     = int(w * 0.295)
    summary_y = int(h * 0.800)
    y = MARGIN_TOP
    while y < summary_y - 20:
        draw.line([(0,y),(w,y)], fill=(175,195,225), width=1)
        y += LINE_SPACING
    y = summary_y + LINE_SPACING
    while y < h - MARGIN_BOTTOM:
        draw.line([(0,y),(w,y)], fill=(175,195,225), width=1)
        y += LINE_SPACING
    draw.line([(cue_x, 0),    (cue_x, summary_y)], fill=(200,60,60), width=2)
    draw.line([(0, summary_y),(w,    summary_y)],   fill=(200,60,60), width=2)
    lbl = _load_font("Caveat", 22)
    draw.text((cue_x//2, MARGIN_TOP//2),       "Cues / Questions", font=lbl, fill=(180,120,120), anchor="mm")
    draw.text(((cue_x+w)//2, MARGIN_TOP//2),   "Notes",            font=lbl, fill=(120,120,190), anchor="mm")
    draw.text((w//2, (summary_y+h)//2),         "Summary",          font=lbl, fill=(110,160,120), anchor="mm")
    return img

def _make_engineering(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (241, 252, 241))
    draw = ImageDraw.Draw(img)
    minor, major = 13, 52
    for x in range(0,w,minor): draw.line([(x,0),(x,h)], fill=(168,218,168), width=1)
    for y in range(0,h,minor): draw.line([(0,y),(w,y)], fill=(168,218,168), width=1)
    for x in range(0,w,major): draw.line([(x,0),(x,h)], fill=(110,185,110), width=2)
    for y in range(0,h,major): draw.line([(0,y),(w,y)], fill=(110,185,110), width=2)
    return img

def _make_professional(w=PAGE_W, h=PAGE_H):
    img  = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(w,88)],  fill=(236,239,246))
    draw.line([(0,88),(w,88)],      fill=(178,185,205), width=2)
    hdr  = _load_font("Caveat", 30)
    draw.text((52,44), "NOTES", font=hdr, fill=(98,108,145), anchor="lm")
    draw.rectangle([(0,0),(8,88)],  fill=(120,135,180))
    draw.line([(MARGIN_LEFT-12,88),(MARGIN_LEFT-12,h-65)], fill=(215,220,232), width=1)
    draw.line([(42,h-58),(w-42,h-58)], fill=(200,205,218), width=1)
    return img

PAPER_STYLES = {
    "Lined (Classic)":  _make_lined,
    "White (Blank)":    _make_white,
    "Graph Paper":      _make_graph,
    "Dot Grid":         _make_dot_grid,
    "Legal Pad":        _make_legal_pad,
    "Cornell Notes":    _make_cornell,
    "Engineering":      _make_engineering,
    "Professional":     _make_professional,
}
DEFAULT_PAPER = "Lined (Classic)"


# ─────────────────────────────────────────────────────────────────────────────
# Unicode → ASCII symbol substitution
# Prevents □ boxes for Greek letters, math symbols, physics units
# ─────────────────────────────────────────────────────────────────────────────
_SYMBOL_MAP = {
    # Greek lowercase
    'α':'alpha', 'β':'beta',  'γ':'gamma', 'δ':'delta',
    'ε':'eps',   'ζ':'zeta',  'η':'eta',   'θ':'theta',
    'ι':'iota',  'κ':'kappa', 'λ':'lambda','μ':'mu',
    'ν':'nu',    'ξ':'xi',    'π':'pi',    'ρ':'rho',
    'σ':'sigma', 'τ':'tau',   'υ':'ups',   'φ':'phi',
    'χ':'chi',   'ψ':'psi',   'ω':'omega',
    # Greek uppercase
    'Γ':'Gamma', 'Δ':'Delta', 'Θ':'Theta', 'Λ':'Lambda',
    'Ξ':'Xi',    'Π':'Pi',    'Σ':'Sigma', 'Φ':'Phi',
    'Ψ':'Psi',   'Ω':'Ohm',   '\u2126':'Ohm',
    # Units
    '°':'deg',   '℃':'degC',  '℉':'degF',
    # Math operators
    '×':' x ',   '÷':'/',     '±':'+/-',   '∝':'prop to',
    '≥':'>=',    '≤':'<=',    '≠':'!=',    '≈':'~=',
    '∞':'inf',
    # Arrows
    '→':'->',  '←':'<-',  '↑':'(up)', '↓':'(dn)',
    '⇒':'=>',  '⇔':'<=>',
    # Powers & roots
    '√':'sqrt', '∛':'cbrt',
    '²':'^2',  '³':'^3',  '⁴':'^4',  '⁰':'^0',  '¹':'^1',
    '₀':'0',   '₁':'1',   '₂':'2',   '₃':'3',   '₄':'4',
    # Calculus
    '∂':'d',    '∇':'grad',  '∆':'delta', '∑':'sum',  '∫':'int',
    # Punctuation
    '\u2019':"'", '\u2018':"'",
    '\u201c':'"', '\u201d':'"',
    '\u2013':'-', '\u2014':'--',
    # Symbols
    '★':'*', '☆':'*', '⭐':'*',
    '✓':'v', '✗':'x', '✔':'v',
    '•':'-',
}

def _sub(text: str) -> str:
    """Replace unmappable Unicode with readable ASCII equivalents."""
    for ch, repl in _SYMBOL_MAP.items():
        text = text.replace(ch, repl)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Pixel-accurate text measurement and wrapping
# ─────────────────────────────────────────────────────────────────────────────

def _px(font, text: str) -> float:
    """Return the pixel width of text in font."""
    if not text:
        return 0.0
    try:
        return float(font.getlength(text))
    except AttributeError:
        bbox = font.getbbox(text)
        return float(bbox[2] - bbox[0]) if bbox else 0.0


def _wrap(line: str, font, max_px: int) -> list:
    """
    Word-wrap a single line to fit within max_px using actual pixel widths.
    Far more accurate than character-count wrapping — fills the page properly.
    """
    line = line.rstrip()
    if not line:
        return ['']
    if _px(font, line) <= max_px:
        return [line]
    words = line.split()
    result, current = [], []
    for word in words:
        trial = ' '.join(current + [word])
        if _px(font, trial) <= max_px or not current:
            current.append(word)
        else:
            result.append(' '.join(current))
            current = [word]
    if current:
        result.append(' '.join(current))
    return result or ['']


# ─────────────────────────────────────────────────────────────────────────────
# Render-operation builder
# Each op: {text, font, x_off, y_adv, extra_y, underline, ink_override, bold}
# ─────────────────────────────────────────────────────────────────────────────

def _build_ops(text: str,
               base_font, base_size: int,
               h2_font,   h2_size: int,
               h3_font,   h3_size: int,
               col_w: int, ls: int) -> list:
    """
    Convert markdown-ish note text into a flat list of render operations.
    Handles: ## headings, ### sub-headings, bullets, blank lines, dividers.
    """
    ops  = []
    half = ls // 2

    def _op(text='', font=None, x_off=0, y_adv=None, extra_y=0,
            underline=False, ink=None, bold=False):
        return dict(text=text, font=font or base_font,
                    x_off=x_off, y_adv=y_adv if y_adv is not None else ls,
                    extra_y=extra_y, underline=underline,
                    ink=ink, bold=bold)

    for raw in text.splitlines():
        s = raw.rstrip()

        # ── Blank line → half-space gap ───────────────────────────────────────
        if not s:
            ops.append(_op(y_adv=half))
            continue

        # ── Horizontal rule ───────────────────────────────────────────────────
        if re.match(r'^[-=_]{3,}\s*$', s):
            ops.append(_op(y_adv=4, extra_y=half // 2,
                           underline=True, ink=(175, 180, 200)))
            continue

        # ── Heading 3  ###  ───────────────────────────────────────────────────
        if s.startswith('### '):
            content = _sub(s[4:].strip())
            wrapped = _wrap(content, h3_font, col_w)
            for i, ln in enumerate(wrapped):
                ops.append(_op(ln, h3_font,
                               y_adv=h3_size + 4,
                               extra_y=half if i == 0 else 0))
            ops.append(_op(y_adv=half // 2))
            continue

        # ── Heading 2  ##  ───────────────────────────────────────────────────
        if s.startswith('## '):
            content = _sub(s[3:].strip())
            wrapped = _wrap(content, h2_font, col_w)
            for i, ln in enumerate(wrapped):
                is_last = (i == len(wrapped) - 1)
                ops.append(_op(ln, h2_font,
                               y_adv=h2_size + 6,
                               extra_y=ls if i == 0 else 0,
                               underline=is_last,
                               bold=True))
            ops.append(_op(y_adv=half // 2))
            continue

        # ── Heading 1  #  ────────────────────────────────────────────────────
        if s.startswith('# ') and not s.startswith('##'):
            content = _sub(s[2:].strip())
            wrapped = _wrap(content, h2_font, col_w)
            for i, ln in enumerate(wrapped):
                is_last = (i == len(wrapped) - 1)
                ops.append(_op(ln, h2_font,
                               y_adv=h2_size + 8,
                               extra_y=ls if i == 0 else 0,
                               underline=is_last,
                               bold=True))
            ops.append(_op(y_adv=half // 2))
            continue

        # ── Regular text (strip inline markdown) ─────────────────────────────
        clean = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
        clean = re.sub(r'\*(.*?)\*',     r'\1', clean)
        clean = re.sub(r'`([^`]+)`',     r'\1', clean)
        clean = _sub(clean)

        # ── Bullet / numbered list ────────────────────────────────────────────
        bm = re.match(r'^([-*]\s+|\d+[.)]\s+)', clean)
        if bm:
            pfx   = bm.group(1)
            rest  = clean[len(pfx):]
            first = _wrap(pfx + rest, base_font, col_w)
            ops.append(_op(first[0], y_adv=ls))
            for seg in first[1:]:
                ops.append(_op('   ' + seg, y_adv=ls))
        else:
            for ln in _wrap(clean, base_font, col_w):
                ops.append(_op(ln, y_adv=ls))

    return ops


# ─────────────────────────────────────────────────────────────────────────────
# Column & pagination layout helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_columns(paper_style: str, columns: int, paper_w: int):
    """Return (col_x_starts, col_text_width, effective_cols)."""
    is_cornell = (paper_style == "Cornell Notes")
    if is_cornell:
        cue_x   = int(paper_w * 0.295)
        notes_x = cue_x + 20
        notes_w = paper_w - notes_x - MARGIN_RIGHT
        return [notes_x], notes_w, 1

    usable = paper_w - MARGIN_LEFT - MARGIN_RIGHT
    if columns == 2:
        gutter = 40
        col_w  = (usable - gutter) // 2
        return [MARGIN_LEFT, MARGIN_LEFT + col_w + gutter], col_w, 2

    return [MARGIN_LEFT], usable, 1


def _paginate_ops(ops: list, max_y: int, eff_cols: int):
    """
    Split ops into pages × columns.
    Returns list of pages; each page = list of eff_cols columns; each column = list of ops.
    """
    pages = []
    current = [[] for _ in range(eff_cols)]
    col_idx = 0
    col_y   = 0

    for op in ops:
        needed = op['extra_y'] + op['y_adv']

        if col_y + needed > max_y:
            # Overflow: move to next column / next page
            col_idx += 1
            if col_idx >= eff_cols:
                pages.append(current)
                current = [[] for _ in range(eff_cols)]
                col_idx = 0
            col_y = 0

        current[col_idx].append(op)
        col_y += needed

    if any(current):
        pages.append(current)

    return pages or [[[] for _ in range(eff_cols)]]


# ─────────────────────────────────────────────────────────────────────────────
# Draw a single column of ops
# ─────────────────────────────────────────────────────────────────────────────

def _draw_column(draw, ops: list, x_start: int, col_w: int,
                 y_start: int, max_y: int, ink_color: tuple):
    y = y_start
    for op in ops:
        y += op['extra_y']
        if y + op['y_adv'] > max_y:
            break

        if op['text']:
            # Bold effect: draw text twice with 1 px offset
            if op['bold']:
                shadow = tuple(min(255, c + 60) for c in (op['ink'] or ink_color))
                draw.text((x_start + op['x_off'] + 1, y + 1),
                          op['text'], font=op['font'], fill=shadow)
            draw.text((x_start + op['x_off'], y),
                      op['text'], font=op['font'],
                      fill=op['ink'] or ink_color)

        # Underline (used for headings and dividers)
        if op['underline']:
            if op['text']:
                line_len = min(int(_px(op['font'], op['text']) * 1.05), col_w)
            else:
                line_len = col_w
            ul_y = y + op['y_adv'] - 4
            draw.line([(x_start, ul_y), (x_start + line_len, ul_y)],
                      fill=op['ink'] or ink_color, width=2)

        y += op['y_adv']


# ─────────────────────────────────────────────────────────────────────────────
# Budget calculator — tells the AI exactly how much content to generate
# ─────────────────────────────────────────────────────────────────────────────

def calculate_budget(
    font_name: str   = "Caveat",
    font_size: int   = FONT_SIZE,
    paper_style: str = DEFAULT_PAPER,
    columns: int     = 1,
    pages: int       = 2,
) -> dict:
    """
    Calculate the exact line/word budget for the given layout configuration.
    This is passed to the AI so it knows precisely how much content to generate.

    Returns dict with:
        total_lines:   total content lines across all pages
        word_budget:   approximate max word count
        words_per_line: avg words that fit on one line
        lines_per_page: content lines per page (across all columns)
    """
    font = _load_font(font_name, font_size)

    # Get column layout
    col_starts, col_w, eff_cols = _compute_columns(paper_style, columns, PAGE_W)

    # Lines per column (vertical space)
    available_h    = PAGE_H - MARGIN_TOP - MARGIN_BOTTOM
    raw_lines_col  = int(available_h / LINE_SPACING)

    # Discount ~25% for headings, spacing, and section gaps
    content_lines_col = int(raw_lines_col * 0.75)

    # Lines per page = lines_per_col * effective_columns
    lines_per_page = content_lines_col * eff_cols

    # Total across all pages
    total_lines = lines_per_page * pages

    # Words per line (pixel-based measurement)
    avg_char_w = max(1.0, _px(font, 'abcdefghij') / 10.0)
    chars_per_line = max(10, int(col_w / avg_char_w))
    words_per_line = max(3, int(chars_per_line / 6.5))  # avg 6.5 chars/word

    word_budget = total_lines * words_per_line

    return {
        "total_lines":    total_lines,
        "word_budget":    word_budget,
        "words_per_line": words_per_line,
        "lines_per_page": lines_per_page,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core render function
# ─────────────────────────────────────────────────────────────────────────────

def render_notes(
    text: str,
    output_prefix: str       = "notes",
    font_name: str           = "Caveat",
    font_size: int           = FONT_SIZE,
    ink_color: tuple         = INK_COLOR,
    paper_style: str         = DEFAULT_PAPER,
    columns: int             = 1,
    show_page_numbers: bool  = True,
) -> list:
    """
    Render study-note text onto A4 paper pages and save as PNGs.
    Returns list of absolute paths to saved PNG files.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load paper template
    paper_fn       = PAPER_STYLES.get(paper_style, _make_lined)
    paper_template = paper_fn()
    paper_w, paper_h = paper_template.size

    # Load fonts
    h2_size    = font_size + 7
    h3_size    = font_size + 3
    pg_size    = max(18, font_size - 14)
    base_font  = _load_font(font_name, font_size)
    h2_font    = _load_font(font_name, h2_size)
    h3_font    = _load_font(font_name, h3_size)
    pg_font    = _load_font(font_name, pg_size)

    # Column layout
    col_starts, col_w, eff_cols = _compute_columns(paper_style, columns, paper_w)
    max_y = paper_h - MARGIN_TOP - MARGIN_BOTTOM

    # Build and paginate render ops
    ops   = _build_ops(text, base_font, font_size, h2_font, h2_size,
                       h3_font, h3_size, col_w, LINE_SPACING)
    pages = _paginate_ops(ops, max_y, eff_cols)
    total = len(pages)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_paths = []

    for page_num, page_cols in enumerate(pages, start=1):
        img  = paper_template.copy()
        draw = ImageDraw.Draw(img)

        # Page number — top right
        if show_page_numbers:
            draw.text(
                (paper_w - MARGIN_RIGHT, 62),
                f"Page {page_num} of {total}",
                font=pg_font, fill=(158, 160, 178), anchor="rm",
            )

        # Draw each column
        for ci, col_ops in enumerate(page_cols):
            x = col_starts[ci] if ci < len(col_starts) else col_starts[-1]
            _draw_column(draw, col_ops, x, col_w,
                         MARGIN_TOP, paper_h - MARGIN_BOTTOM, ink_color)

        suffix   = f"_p{page_num}" if total > 1 else ""
        filename = f"{output_prefix}_{timestamp}{suffix}.png"
        filepath = str(OUTPUT_DIR / filename)
        img.save(filepath)
        saved_paths.append(filepath)
        print(f"  ✅ Saved page {page_num}: {filepath}")

    return saved_paths


# ─────────────────────────────────────────────────────────────────────────────
# PDF Export
# ─────────────────────────────────────────────────────────────────────────────

def export_pdf(image_paths: list) -> bytes:
    """Bundle all PNG pages into a single PDF. Returns PDF as bytes."""
    images = []
    for p in image_paths:
        try:
            images.append(Image.open(p).convert("RGB"))
        except Exception:
            pass
    if not images:
        return b""
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True,
                   append_images=images[1:], resolution=150)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Live Preview
# ─────────────────────────────────────────────────────────────────────────────

_PREVIEW_TEXT = """\
## Physics — Current & Electricity

OHM'S LAW  ★ Most Important
- V = I * R
  (V=voltage, I=current, R=resistance in Ohm)

## Key Formulas
- Power:  P = V * I = I^2 * R = V^2 / R
- Charge: Q = I * t   (Q in Coulombs)

## Remember!
- Series:   R_total = R1 + R2 + R3
- Parallel: 1/R = 1/R1 + 1/R2 + 1/R3"""


def render_preview(
    paper_style: str = DEFAULT_PAPER,
    font_name: str   = "Caveat",
    ink_color: tuple = INK_COLOR,
    columns: int     = 1,
    font_size: int   = FONT_SIZE,
) -> Image.Image:
    """
    Render a live-preview thumbnail (400 × 566 px, A4 aspect ratio).
    """
    paper_fn = PAPER_STYLES.get(paper_style, _make_lined)
    img      = paper_fn()
    draw     = ImageDraw.Draw(img)
    paper_w, paper_h = img.size

    h2_size   = font_size + 7
    h3_size   = font_size + 3
    pg_size   = max(18, font_size - 14)
    base_font = _load_font(font_name, font_size)
    h2_font   = _load_font(font_name, h2_size)
    h3_font   = _load_font(font_name, h3_size)
    pg_font   = _load_font(font_name, pg_size)

    col_starts, col_w, eff_cols = _compute_columns(paper_style, columns, paper_w)
    max_y = paper_h - MARGIN_TOP - MARGIN_BOTTOM

    ops   = _build_ops(_PREVIEW_TEXT, base_font, font_size, h2_font, h2_size,
                       h3_font, h3_size, col_w, LINE_SPACING)
    pages = _paginate_ops(ops, max_y, eff_cols)

    # Page number
    draw.text((paper_w - MARGIN_RIGHT, 62), "Page 1 of 1",
              font=pg_font, fill=(158,160,178), anchor="rm")

    # Draw first page only
    if pages:
        for ci, col_ops in enumerate(pages[0]):
            x = col_starts[ci] if ci < len(col_starts) else col_starts[-1]
            _draw_column(draw, col_ops, x, col_w,
                         MARGIN_TOP, paper_h - MARGIN_BOTTOM, ink_color)

    # Dashed divider for 2-column
    if eff_cols == 2 and len(col_starts) == 2:
        mid_x = col_starts[0] + col_w + 20
        for dash_y in range(MARGIN_TOP, paper_h - MARGIN_BOTTOM, 18):
            draw.line([(mid_x, dash_y), (mid_x, min(dash_y+9, paper_h-MARGIN_BOTTOM))],
                      fill=(200, 200, 215), width=1)

    return img.resize((400, 566), Image.LANCZOS)


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    SAMPLE = """\
## Current & Electricity — Key Formulas

OHM'S LAW  ★ Most Important
- V = I * R
  (V = voltage in Volts, I = current in Amperes, R = resistance in Ohm)

RESISTIVITY
- R = rho * L / A
  (rho = resistivity in Ohm-m, L = wire length, A = cross-section area)

POWER FORMULAS
- P = V * I  =  I^2 * R  =  V^2 / R    (P in Watts)

CHARGE & CURRENT
- Q = I * t     (Q = charge in Coulombs, t = time in seconds)

## Series vs Parallel

SERIES circuit:
- R_total = R1 + R2 + R3
- Same current through all — I is constant

PARALLEL circuit:
- 1/R_total = 1/R1 + 1/R2 + 1/R3
- Same voltage across all — V is constant

## Remember!
- Voltage divides in series, current divides in parallel
- Short circuit -> R -> 0 -> I very large -> dangerous!
- Open circuit  -> R -> inf -> I = 0
"""
    print("Rendering on all 8 paper styles …\n")
    for style in PAPER_STYLES:
        paths = render_notes(SAMPLE, output_prefix="test",
                             font_name="Caveat", paper_style=style)
        print(f"  {style}: {paths}")
    print("\nDone.")

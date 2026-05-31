"""
app.py — HandScribe v2.0
Multimodal AI Notes Agent · Unified Input · Budget-Aware · Density Control
"""

import io
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image as PILImage

from ai_processor import generate_notes, extract_urls_and_text
from note_renderer import (
    render_notes,
    render_preview,
    export_pdf,
    calculate_budget,
    PAPER_STYLES,
    FONTS,
    FONT_SIZE,
    INK_COLOR,
    DEFAULT_PAPER,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HandScribe v2.0 — AI Handwritten Notes",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@400;600&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg:       #0d1117;
    --bg2:      #161b22;
    --card:     #1a1f2e;
    --card2:    #1e2436;
    --border:   #2d3248;
    --border2:  #3d4268;
    --accent:   #7c6dfa;
    --accent2:  #fa6d8a;
    --accent3:  #6dfacc;
    --text:     #e8eaf0;
    --muted:    #7a7e9a;
    --success:  #43d9ad;
    --warn:     #f0a050;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"]       { background: transparent !important; }
[data-testid="stSidebar"]      { background: var(--bg2) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebarContent"] { padding-top: 1.5rem; }

.hero-wrap  { text-align: center; margin-bottom: 0.4rem; }
.hero-title {
    font-family: 'Caveat', cursive;
    font-size: 3.8rem;
    font-weight: 600;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent2) 55%, var(--accent3) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-block;
    margin-bottom: 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 1.02rem;
    margin-bottom: 2rem;
    letter-spacing: 0.025em;
}
.badge-row { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-bottom: 2rem; }
.badge {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.04em;
}

.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.7rem;
    margin-bottom: 1.2rem;
}
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.5rem;
}

div[data-testid="stButton"] > button,
div[data-testid="stBaseButton-primary"] > button {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.8rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: opacity 0.2s, transform 0.15s !important;
    cursor: pointer !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.87 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stDownloadButton"] > button {
    background: var(--card2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s, background 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--accent) !important;
    background: var(--card) !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(124,109,250,0.18) !important;
}

/* Kill placeholder watermark */
[data-testid="stTextArea"] textarea::placeholder {
    color: #3d4268 !important;
    opacity: 0.6 !important;
}

[data-testid="stSelectbox"] > div > div {
    background: #0d1117 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}

[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.8rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

.reasoning-box {
    background: #080d14;
    border: 1px solid #2a3048;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    color: #8badd4;
    white-space: pre-wrap;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.6;
}

.divider { border-top: 1px solid var(--border); margin: 1.5rem 0; }

.footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.78rem;
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    letter-spacing: 0.04em;
}

.word-counter {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.25rem;
}

.preview-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent3);
    margin-bottom: 0.4rem;
}

.budget-box {
    background: #0e1420;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.78rem;
    color: var(--muted);
    line-height: 1.5;
    margin-top: 0.3rem;
}
.budget-box strong { color: var(--accent3); }

.api-ok   { background: #0e2a20; border: 1px solid var(--success); border-radius: 10px;
             padding: 8px 16px; color: var(--success); font-size: 0.85rem; font-weight: 600;
             display: inline-flex; align-items: center; gap: 8px; }
.api-fail { background: #220e14; border: 1px solid var(--accent2); border-radius: 10px;
             padding: 10px 16px; color: var(--accent2); font-size: 0.88rem; }

/* File chips */
.file-chip {
    background: var(--card2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.8rem;
    color: #9bb8d4;
    display: inline-block;
    margin: 2px 4px 2px 0;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
_DEFAULTS = {
    "generated_notes":  "",
    "agent_reasoning":  "",
    "rendered_paths":   [],
    "history":          [],
    "editor_version":   0,      # bump to force text_area refresh
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Constants ─────────────────────────────────────────────────────────────────
INK_OPTIONS = {
    "Navy Blue":   (15,  30,  80),
    "Black":       (20,  20,  20),
    "Dark Green":  (10,  60,  30),
    "Dark Red":    (90,  10,  10),
    "Purple":      (60,  20, 100),
    "Dark Brown":  (60,  30,  10),
}

MODEL_OPTIONS = {
    "Gemini 2.5 Flash (Fast)": "gemini-2.5-flash",
    "Gemini 2.5 Pro (Best Quality)": "gemini-2.5-pro",
}

# Supported file extensions
SUPPORTED_TYPES = [
    "pdf", "png", "jpg", "jpeg", "webp", "gif",
    "docx", "pptx",
    "txt", "md", "csv", "log",
    "py", "c", "cpp", "h", "hpp", "java", "js", "ts", "jsx", "tsx",
    "html", "css", "json", "xml", "yaml", "yml", "toml",
    "go", "rs", "rb", "php", "sql", "sh", "bat",
    "swift", "kt", "dart", "r", "lua",
]


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:

    api_key   = os.getenv("GEMINI_API_KEY", "")
    key_valid = bool(api_key and api_key != "your_gemini_api_key_here")
    if key_valid:
        masked = api_key[:8] + "•" * max(0, len(api_key) - 12) + api_key[-4:]
        st.markdown(
            f'<div class="api-ok">✅ &nbsp;API key loaded &nbsp;<code>{masked}</code></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="api-fail">🔑 <strong>API Key missing</strong><br>'
            'Add <code>GEMINI_API_KEY=…</code> to your <code>.env</code> file.<br>'
            '<a href="https://aistudio.google.com/app/apikey" target="_blank" '
            'style="color:#7c6dfa;">→ Get a free key</a></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── AI Engine ─────────────────────────────────────────────────────────────
    st.markdown("### 🤖 AI Engine")
    model_label = st.selectbox(
        "Model",
        list(MODEL_OPTIONS.keys()),
        index=0,
        key="sb_model",
        help="Pro follows instructions better but may hit rate limits. Flash is faster and more reliable.",
    )
    selected_model = MODEL_OPTIONS[model_label]

    density_label = st.select_slider(
        "Content Density",
        options=["Compact", "Balanced", "Detailed"],
        value="Balanced",
        key="sb_density",
        help=(
            "Compact = pure cheat sheet (formulas/syntax only, no explanations).\n"
            "Balanced = study notes with tips and context.\n"
            "Detailed = full study guide with examples and explanations."
        ),
    )
    density_value = density_label.lower()

    target_pages = st.slider(
        "Target Pages",
        min_value=1, max_value=6, value=2, step=1,
        key="sb_target_pages",
        help="The AI will fit content to exactly this many pages.",
    )

    st.markdown("---")

    # ── Handwriting ───────────────────────────────────────────────────────────
    st.markdown("### 🖋️ Handwriting")
    font_name = st.selectbox("Font", list(FONTS.keys()), index=0, key="sb_font_name")
    font_size = st.slider("Size", 24, 52, 34, 2, key="sb_font_size")
    ink_label = st.selectbox("Ink Colour", list(INK_OPTIONS.keys()), index=0, key="sb_ink_label")
    selected_ink = INK_OPTIONS[ink_label]

    st.markdown("---")

    # ── Paper & Layout ────────────────────────────────────────────────────────
    st.markdown("### 📄 Paper & Layout")
    paper_style = st.selectbox(
        "Paper Style", list(PAPER_STYLES.keys()), index=0, key="sb_paper_style",
    )
    col_choice = st.radio(
        "Column Layout", ["Single Column", "Two Columns"],
        index=0, horizontal=True, key="sb_col_choice",
    )
    columns = 2 if col_choice == "Two Columns" else 1
    show_page_numbers = st.toggle("Page Numbers", value=True, key="sb_page_numbers")

    st.markdown("---")

    # ── Budget indicator ──────────────────────────────────────────────────────
    _budget = calculate_budget(
        font_name=font_name, font_size=font_size,
        paper_style=paper_style, columns=columns, pages=target_pages,
    )
    st.markdown(
        f'<div class="budget-box">'
        f'📊 <strong>Content Budget</strong><br>'
        f'Pages: {target_pages} · Columns: {columns}<br>'
        f'Max lines: <strong>{_budget["total_lines"]}</strong> · '
        f'Max words: <strong>{_budget["word_budget"]}</strong><br>'
        f'Density: {density_label}'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Live preview ──────────────────────────────────────────────────────────
    st.markdown('<div class="preview-label">🎨 Live Style Preview</div>', unsafe_allow_html=True)
    try:
        preview_pil = render_preview(
            paper_style=paper_style, font_name=font_name,
            ink_color=selected_ink, columns=columns, font_size=font_size,
        )
        preview_buf = io.BytesIO()
        preview_pil.save(preview_buf, format="PNG")
        st.image(preview_buf.getvalue(), width='stretch')
    except Exception as _prev_err:
        st.caption(f"Preview unavailable: {_prev_err}")

    st.markdown("---")

    # ── History ───────────────────────────────────────────────────────────────
    if st.session_state.history:
        with st.expander(f"📚 History ({len(st.session_state.history)} sessions)", expanded=False):
            for session in reversed(st.session_state.history[-6:]):
                st.caption(f"🕐 {session['ts']} — {session['paper_style']} · {session['font_name']}")
                if session.get("paths"):
                    try:
                        thumb = PILImage.open(session["paths"][0]).resize((190, 268))
                        t_buf = io.BytesIO()
                        thumb.save(t_buf, format="PNG")
                        st.image(t_buf.getvalue(), width='stretch')
                    except Exception:
                        st.caption("(thumbnail unavailable)")
                st.markdown("---")

    st.markdown(
        '<div style="color:#4a4e6a;font-size:0.72rem;text-align:center;margin-top:0.5rem;">'
        'HandScribe v2.0 · Gemini AI + Pillow</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="hero-wrap"><div class="hero-title">✍️ HandScribe</div></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;" class="hero-sub">'
    'Multimodal AI Notes Agent &nbsp;·&nbsp; Feed it anything. Get handwritten notes.'
    '</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="badge-row">'
    '<span class="badge">🎬 YouTube</span>'
    '<span class="badge">📄 PDF / DOCX / PPTX</span>'
    '<span class="badge">🖼️ Images</span>'
    '<span class="badge">💻 Code Files</span>'
    '<span class="badge">📝 Text / Prompt</span>'
    '</div>',
    unsafe_allow_html=True,
)

if not key_valid:
    st.error(
        "🔑 **No API key configured.** "
        "Create a `.env` file with `GEMINI_API_KEY=your_key_here`. "
        "[→ Get a free key](https://aistudio.google.com/app/apikey)"
    )

# ── Unified Input ─────────────────────────────────────────────────────────────
st.markdown("### 💬 What notes do you need?")

user_input = st.text_area(
    "prompt",
    placeholder=(
        "Type anything here — prompts, questions, YouTube URLs, or paste text...\n\n"
        "Examples:\n"
        "  Python important syntax for two pages\n"
        "  Physics current and electricity formulas\n"
        "  https://youtube.com/watch?v=dQw4w9 — summarize this lecture\n"
        "  Explain neural networks for my ML exam"
    ),
    height=140,
    key="main_input",
    label_visibility="collapsed",
)

# File attachment
uploaded = st.file_uploader(
    "📎 Attach files (PDF, DOCX, PPTX, images, code, text…)",
    type=SUPPORTED_TYPES,
    accept_multiple_files=True,
    key="file_uploader",
    label_visibility="visible",
)
if uploaded:
    chips = " ".join(
        f'<span class="file-chip">{"📄" if "pdf" in (f.type or "") else "🖼️" if "image" in (f.type or "") else "📁"} {f.name}</span>'
        for f in uploaded
    )
    st.markdown(chips, unsafe_allow_html=True)


# ── Generate ──────────────────────────────────────────────────────────────────
st.markdown("")
_gcol1, _gcol2 = st.columns([1, 3])
with _gcol1:
    generate_clicked = st.button(
        "🚀 Generate Notes",
        width='stretch',
        disabled=not key_valid,
        key="btn_generate",
    )
with _gcol2:
    st.markdown(
        f'<div class="budget-box" style="margin-top:0;">'
        f'🎯 <strong>{_budget["word_budget"]} words</strong> · '
        f'<strong>{_budget["total_lines"]} lines</strong> · '
        f'{target_pages} pg · {density_label} · '
        f'{model_label.split("(")[0].strip()}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Processing ────────────────────────────────────────────────────────────────
if generate_clicked:
    raw_input = (user_input or "").strip()

    # Extract YouTube URLs from the unified input
    _yt_urls, _clean_text = extract_urls_and_text(raw_input)

    # Process uploaded files
    _files_data = []
    if uploaded:
        for _f in uploaded:
            _files_data.append({
                "bytes": _f.read(),
                "mime":  _f.type or "application/octet-stream",
                "name":  _f.name,
            })

    if not _yt_urls and not _files_data and not _clean_text:
        st.error("⚠️ Please provide at least one input: type a prompt, paste a URL, or attach a file.")
    else:
        _summary_parts = []
        if _files_data:
            _summary_parts.append(f"{len(_files_data)} file(s)")
        if _yt_urls:
            _summary_parts.append(f"{len(_yt_urls)} YouTube URL(s)")
        if _clean_text:
            _summary_parts.append("text prompt")

        with st.spinner(
            f"🤖 Agent thinking … ({', '.join(_summary_parts)}) · "
            f"{model_label.split('(')[0].strip()} · {density_label}"
        ):
            try:
                _reasoning, _notes = generate_notes(
                    youtube_urls=_yt_urls,
                    uploaded_files=_files_data,
                    user_text=_clean_text,
                    model_name=selected_model,
                    budget=_budget,
                    density=density_value,
                    columns=columns,
                )

                # ── Bump editor version to force text_area refresh ────────
                st.session_state.editor_version += 1
                st.session_state.generated_notes = _notes
                st.session_state.agent_reasoning  = _reasoning
                st.session_state.rendered_paths   = []
                st.session_state["_just_generated"] = True
                st.rerun()

            except (EnvironmentError, ValueError) as _e:
                st.error(f"❌ {_e}")
                st.stop()
            except RuntimeError as _e:
                err_msg = str(_e)
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    st.error(
                        "⚠️ **Rate limit reached.** The Gemini API quota is temporarily exhausted. "
                        "Try switching to **Flash** model in the sidebar, or wait a minute and retry."
                    )
                else:
                    st.error(f"❌ AI error: {_e}")
                st.stop()
            except Exception as _e:
                st.error(f"❌ Unexpected error: {_e}")
                st.stop()


# ── Success banner (after rerun) ──────────────────────────────────────────────
if st.session_state.pop("_just_generated", False):
    st.success("✅ Notes generated! Review and edit below, then render.")


# ── Agent Reasoning ───────────────────────────────────────────────────────────
if st.session_state.agent_reasoning:
    with st.expander("🧠 How the Agent Thought", expanded=False):
        _raw   = st.session_state.agent_reasoning
        _trunc = _raw[:3500] + ("\n\n…(truncated)" if len(_raw) > 3500 else "")
        st.markdown(
            f'<div class="reasoning-box">{_trunc}</div>',
            unsafe_allow_html=True,
        )


# ── Review & Edit Notes ──────────────────────────────────────────────────────
if st.session_state.generated_notes:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📝 Review & Edit Your Notes")
    st.caption("Edit freely — this is exactly what gets written on the paper.")

    # Dynamic key forces new widget on each generation
    _editor_key = f"notes_editor_v{st.session_state.editor_version}"

    edited_notes = st.text_area(
        "Notes Editor",
        value=st.session_state.generated_notes,
        height=400,
        key=_editor_key,
        label_visibility="collapsed",
    )

    _wc = len(edited_notes.split())
    _word_limit = _budget.get("word_budget", 400)
    _wc_color = "var(--warn)" if _wc > _word_limit else "var(--success)" if _wc > 20 else "var(--muted)"
    st.markdown(
        f'<div class="word-counter">Word count: '
        f'<strong style="color:{_wc_color};">{_wc}</strong>'
        f' / {_word_limit} budget for {target_pages} page(s)</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")
    _rcol1, _rcol2 = st.columns([1, 3])
    with _rcol1:
        render_clicked = st.button(
            "✍️ Render Handwritten Notes",
            width='stretch',
            key="btn_render",
        )
    with _rcol2:
        st.caption(
            f"📄 **{paper_style}** · 🖋 **{font_name}** · "
            f"🎨 **{ink_label}** · "
            f"{'↔️ 2-Col' if columns == 2 else '↕️ 1-Col'} · "
            f"{'🔢 Page numbers' if show_page_numbers else '🚫 No page numbers'}"
        )

    if render_clicked:
        with st.spinner("🖊️ Writing your notes on paper…"):
            try:
                _paths = render_notes(
                    edited_notes,
                    output_prefix="notes",
                    font_name=font_name,
                    font_size=font_size,
                    ink_color=selected_ink,
                    paper_style=paper_style,
                    columns=columns,
                    show_page_numbers=show_page_numbers,
                )
                st.session_state.rendered_paths = _paths
                st.session_state.history.append({
                    "paths":       _paths,
                    "paper_style": paper_style,
                    "font_name":   font_name,
                    "ts":          datetime.now().strftime("%H:%M:%S"),
                })
            except Exception as _e:
                st.error(f"❌ Rendering error: {_e}")
                st.stop()


# ── Output Pages ──────────────────────────────────────────────────────────────
if st.session_state.rendered_paths:
    _paths = st.session_state.rendered_paths
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f"### 🎉 Your Handwritten Notes — {len(_paths)} Page(s)")

    for _i, _path in enumerate(_paths, start=1):
        if not Path(_path).exists():
            continue

        _img_col, _dl_col = st.columns([5, 1])
        with _img_col:
            st.markdown(f"**Page {_i}**")
            st.image(_path, width='stretch')
        with _dl_col:
            st.markdown("<br>", unsafe_allow_html=True)
            with open(_path, "rb") as _f:
                _img_bytes = _f.read()
            st.download_button(
                label=f"⬇️ PNG",
                data=_img_bytes,
                file_name=Path(_path).name,
                mime="image/png",
                key=f"dl_png_{_i}",
            )

        if _i < len(_paths):
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # PDF export
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    _pdf_bytes = export_pdf(_paths)
    if _pdf_bytes:
        st.download_button(
            label="⬇️  Download All Pages as PDF",
            data=_pdf_bytes,
            file_name="handscribe_notes.pdf",
            mime="application/pdf",
            key="dl_pdf",
            width='stretch',
        )
        st.caption(
            f"PDF contains {len(_paths)} page(s) · "
            f"{paper_style} · {font_name} · {ink_label}"
        )


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">'
    '✍️ HandScribe v2.0 &nbsp;·&nbsp; Gemini AI &nbsp;·&nbsp; '
    'Pillow &nbsp;·&nbsp; Streamlit &nbsp;·&nbsp; '
    '<a href="https://aistudio.google.com/app/apikey" target="_blank" '
    'style="color:#7c6dfa;">Get API Key</a>'
    '</div>',
    unsafe_allow_html=True,
)

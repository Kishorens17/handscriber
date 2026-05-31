"""
ai_processor.py — Multimodal AI Agent Brain (HandScribe v2.0)

Architecture:
  - Structured JSON output from Gemini → we control rendering
  - Exact word/line budget injected into prompt
  - Content density control (compact / balanced / detailed)
  - Programmatic truncation safety net
  - Auto-fallback: Pro → Flash on rate limit
  - Extended file types: PDF, images, DOCX, PPTX, code, text
"""

import os
import io
import json
import re
import zipfile
import tempfile
from xml.etree import ElementTree
from dotenv import load_dotenv
from google import genai
from google.genai import types

from transcript import get_transcript

load_dotenv()


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a brilliant teacher who writes handwritten notes for students.
Write like a real human — a teacher explaining clearly to a student.

═══════════════════════════════════════════════════
OUTPUT FORMAT — MANDATORY:

You MUST return ONLY valid JSON, nothing else. No markdown, no explanation.
The JSON schema:

{{
  "title": "Topic — Subtitle",
  "sections": [
    {{
      "heading": "CATEGORY NAME",
      "items": [
        "first item or formula or code line",
        "second item",
        "third item"
      ]
    }}
  ]
}}

Each "item" is a single short line of content. NOT a paragraph.

═══════════════════════════════════════════════════
WRITING STYLE:

  Write like a HUMAN TEACHER, NOT an AI bot.

  GOOD item examples:
    "V = I * R                    (Ohm's Law)"
    "x = 5                        # integer"
    "lst.append(4)                # add to end"
    "Remember: current same in series!"
    "KEY: P = V*I = I^2*R = V^2/R"

  BAD (never do this):
    "Variable assignment is the process of storing a value..."
    "The append method adds an element to the end of..."
    Any sentence longer than ~12 words
    Any explanation of something obvious

  Rules:
    - Each item = 1 short line. Code + brief comment, or formula + unit.
    - NO multi-sentence items. NO paragraphs inside items.
    - For code/syntax: "code_here           # brief comment"
    - For formulas:    "F = m * a           (F=Newtons, m=kg, a=m/s^2)"
    - For concepts:    "KEY: short memorable statement"
    - Plain ASCII only: ^2, *, sqrt(), Ohm, rho, pi, ->, >=

═══════════════════════════════════════════════════
FORMAT DETECTION:

  Programming/syntax → group by category, code + comment per item
  Formulas/equations → formula + units per item
  Lecture/concepts   → short bullet points, key terms highlighted
  Meeting/discussion → decisions, action items
  Tasks/how-to       → numbered steps

═══════════════════════════════════════════════════
PAGE BUDGET:

The user's page budget will be injected below. This is a HARD LIMIT.
You will be told exactly how many items to generate.
Do NOT exceed the item count. If in doubt, generate FEWER items.
Cut less important content rather than exceeding the budget.
"""


# ── Density presets ───────────────────────────────────────────────────────────
DENSITY_INSTRUCTIONS = {
    "compact": (
        "DENSITY: COMPACT — This is a quick-reference cheat sheet.\n"
        "- ONLY key formulas, syntax, or definitions. Nothing else.\n"
        "- Each item: code/formula + max 3-word comment. No explanations.\n"
        "- NO tips, NO examples, NO 'Note:', NO 'Remember:' items.\n"
        "- Maximum number of items possible within budget.\n"
        "- Think: cheat sheet you'd sneak into an exam — pure facts only.\n"
        "- Example item: 'lst.append(x)  # add to end'\n"
        "- Example item: 'V = I * R  (Ohm)'\n"
    ),
    "balanced": (
        "DENSITY: BALANCED — Study notes with helpful context.\n"
        "- Key items with 5-8 word explanations.\n"
        "- Include ALL content from compact mode PLUS:\n"
        "  * Brief tips marked with 'TIP:'\n"
        "  * Common mistakes marked with 'WATCH OUT:'\n"
        "- Cover all core topics, skip only very niche ones.\n"
        "- Example item: 'lst.append(x)  # add item to end of list'\n"
        "- Example item: 'TIP: lists are mutable, tuples are not!'\n"
    ),
    "detailed": (
        "DENSITY: DETAILED — Thorough study guide for deep learning.\n"
        "- Include EVERYTHING from compact and balanced PLUS:\n"
        "  * Clear explanations (1 line each)\n"
        "  * Real-world examples and analogies\n"
        "  * Edge cases and common interview questions\n"
        "  * 'WHY:' items explaining the reasoning behind concepts\n"
        "- Fewer sections but each section has MORE items with depth.\n"
        "- Think: study guide for someone learning from scratch.\n"
        "- Example: 'WHY: lists use [] because they are like containers'\n"
        "- Example: 'EXAMPLE: sorted([3,1,2]) returns [1,2,3]'\n"
    ),
}


# ── Text extraction helpers ──────────────────────────────────────────────────
def _extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a .docx file by parsing its internal XML."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            xml_data = z.read("word/document.xml")
            tree = ElementTree.fromstring(xml_data)
            ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            paragraphs = []
            for para in tree.iter(f"{{{ns}}}p"):
                texts = [node.text for node in para.iter(f"{{{ns}}}t") if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            return "\n".join(paragraphs)
    except Exception as e:
        return f"[Could not extract DOCX text: {e}]"


def _extract_pptx_text(file_bytes: bytes) -> str:
    """Extract text from a .pptx file by parsing its internal XML."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            slides = sorted(
                [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            )
            ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
            all_text = []
            for i, slide_name in enumerate(slides, 1):
                xml_data = z.read(slide_name)
                tree = ElementTree.fromstring(xml_data)
                texts = [node.text for node in tree.iter(f"{{{ns}}}t") if node.text]
                if texts:
                    all_text.append(f"--- Slide {i} ---")
                    all_text.append(" ".join(texts))
            return "\n".join(all_text)
    except Exception as e:
        return f"[Could not extract PPTX text: {e}]"


# Text-based file extensions (read as UTF-8)
TEXT_EXTENSIONS = {
    ".py", ".c", ".cpp", ".h", ".hpp", ".java", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".go", ".rs", ".rb", ".php", ".sql", ".sh", ".bat", ".ps1",
    ".swift", ".kt", ".dart", ".r", ".lua", ".m",
    ".vue", ".svelte", ".txt", ".md", ".csv", ".log",
}


# ── JSON → Text converter ────────────────────────────────────────────────────
def json_to_text(data: dict) -> str:
    """
    Convert structured JSON from the AI into the markdown-ish format
    that the renderer's _build_ops() parser expects.
    """
    lines = []
    title = data.get("title", "Notes")
    lines.append(f"## {title}")
    lines.append("")

    for section in data.get("sections", []):
        heading = section.get("heading", "")
        items   = section.get("items", [])
        if heading:
            lines.append(heading)
        for item in items:
            item = str(item).strip()
            if item:
                if not item.startswith("- ") and not re.match(r'^\d+[.)\s]', item):
                    item = f"- {item}"
                lines.append(item)
        lines.append("")
    return "\n".join(lines).strip()


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from AI response, handling code fences and edge cases."""
    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── YouTube URL detection ─────────────────────────────────────────────────────
_YT_RE = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w\-]+(?:\S*)',
    re.IGNORECASE
)

def extract_urls_and_text(raw: str):
    """Separate YouTube URLs from plain text in user input."""
    urls = _YT_RE.findall(raw)
    text = _YT_RE.sub('', raw).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return urls, text


# ── Main function ─────────────────────────────────────────────────────────────
def generate_notes(
    youtube_urls: list  = None,
    uploaded_files: list = None,
    user_text: str       = "",
    model_name: str      = "gemini-2.5-flash",
    budget: dict         = None,
    density: str         = "balanced",
    columns: int         = 1,
) -> tuple:
    """
    Generate structured study notes from multimodal inputs.

    Returns:
        Tuple of (reasoning_text: str, notes_text: str)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to your .env file.\n"
            "Get a free key at: https://aistudio.google.com/app/apikey"
        )

    youtube_urls   = [u for u in (youtube_urls or []) if u and u.strip()]
    uploaded_files = uploaded_files or []

    if not youtube_urls and not uploaded_files and not (user_text or "").strip():
        raise ValueError("Please provide at least one input.")

    client = genai.Client(api_key=api_key)

    # ── Build budget instruction ──────────────────────────────────────────────
    budget_instruction = ""
    if budget:
        total = budget.get("total_lines", 60)
        words = budget.get("word_budget", 400)
        col_label = "two columns" if columns == 2 else "single column"
        max_items = int(total * 0.80)

        budget_instruction = (
            f"\n═══════════════════════════════════════════════════\n"
            f"YOUR BUDGET FOR THIS REQUEST:\n"
            f"- Layout: {col_label}\n"
            f"- Total content lines available: {total}\n"
            f"- Maximum total items across ALL sections: {max_items}\n"
            f"- Maximum word count: {words}\n"
            f"- HARD RULE: Do NOT generate more than {max_items} items total.\n"
            f"  If you have more content, CUT the less important items.\n"
        )
    else:
        budget_instruction = "\nDEFAULT BUDGET: Keep output under 400 words / ~50 items total.\n"

    # ── Build contents list ───────────────────────────────────────────────────
    density_text = DENSITY_INSTRUCTIONS.get(density, DENSITY_INSTRUCTIONS["balanced"])
    contents = [SYSTEM_PROMPT + budget_instruction + density_text]

    # YouTube transcripts
    for i, url in enumerate(youtube_urls, 1):
        url = url.strip()
        try:
            transcript_text = get_transcript(url)
            contents.append(
                f"\n\n{'='*60}\n"
                f"YOUTUBE VIDEO {i} TRANSCRIPT  |  URL: {url}\n"
                f"{'='*60}\n{transcript_text}"
            )
        except ValueError as e:
            contents.append(f"\n\n[YouTube Video {i} — could not fetch: {e}]")

    # Uploaded files
    api_files_to_delete = []
    tmp_paths_to_clean  = []

    try:
        for f in uploaded_files:
            mime       = f.get("mime", "application/octet-stream")
            file_bytes = f.get("bytes", b"")
            name       = f.get("name", "uploaded_file")
            ext        = os.path.splitext(name)[1].lower()

            if "pdf" in mime.lower():
                # PDF → Gemini Files API (native vision)
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_paths_to_clean.append(tmp.name)
                api_file = client.files.upload(file=tmp_paths_to_clean[-1])
                api_files_to_delete.append(api_file)
                contents.append(f"\n\nUPLOADED PDF: {name}")
                contents.append(api_file)

            elif "image" in mime.lower():
                # Images → inline bytes (native vision)
                contents.append(f"\n\nUPLOADED IMAGE: {name}")
                contents.append(types.Part.from_bytes(data=file_bytes, mime_type=mime))

            elif ext == ".docx":
                text = _extract_docx_text(file_bytes)
                contents.append(
                    f"\n\n{'='*60}\n"
                    f"WORD DOCUMENT: {name}\n"
                    f"{'='*60}\n{text}"
                )

            elif ext == ".pptx":
                text = _extract_pptx_text(file_bytes)
                contents.append(
                    f"\n\n{'='*60}\n"
                    f"POWERPOINT: {name}\n"
                    f"{'='*60}\n{text}"
                )

            elif ext in TEXT_EXTENSIONS:
                # Code / text files → read as UTF-8
                try:
                    text = file_bytes.decode("utf-8", errors="replace")
                except Exception:
                    text = file_bytes.decode("latin-1", errors="replace")
                lang = ext.lstrip(".")
                contents.append(
                    f"\n\n{'='*60}\n"
                    f"FILE ({lang.upper()}): {name}\n"
                    f"{'='*60}\n{text}"
                )

            else:
                # Unknown file type — try text, fallback to skip
                try:
                    text = file_bytes.decode("utf-8", errors="replace")
                    contents.append(
                        f"\n\n{'='*60}\n"
                        f"FILE: {name}\n"
                        f"{'='*60}\n{text}"
                    )
                except Exception:
                    contents.append(f"\n\n[Unsupported file: {name}]")

        # User text
        if user_text and user_text.strip():
            contents.append(
                f"\n\n{'='*60}\n"
                f"USER REQUEST:\n"
                f"{'='*60}\n{user_text.strip()}"
            )

        contents.append(
            "\n\nNow write the notes as valid JSON. "
            "Remember: ONLY output the JSON object, nothing else. "
            "Stay within your item budget."
        )

        # ── Call Gemini (with auto-fallback on rate limit) ────────────────────
        response = _call_gemini_with_fallback(client, model_name, contents)

        # ── Separate reasoning from notes ─────────────────────────────────────
        reasoning_parts, notes_parts = [], []
        for part in response.candidates[0].content.parts:
            if hasattr(part, "thought") and part.thought:
                if part.text:
                    reasoning_parts.append(part.text)
            else:
                if part.text:
                    notes_parts.append(part.text)

        reasoning = "\n".join(reasoning_parts).strip()
        raw_notes = "\n".join(notes_parts).strip()

        if not raw_notes and reasoning:
            raw_notes = reasoning
            reasoning = ""

        # ── Parse JSON → text ─────────────────────────────────────────────────
        parsed = _parse_json_response(raw_notes)

        if parsed and isinstance(parsed, dict) and "sections" in parsed:
            if budget:
                max_items = int(budget.get("total_lines", 60) * 0.80)
                item_count = 0
                trimmed_sections = []
                for sec in parsed.get("sections", []):
                    if item_count >= max_items:
                        break
                    remaining = max_items - item_count
                    items = sec.get("items", [])[:remaining]
                    trimmed_sections.append({"heading": sec.get("heading", ""), "items": items})
                    item_count += len(items)
                parsed["sections"] = trimmed_sections
            notes = json_to_text(parsed)
        else:
            notes = re.sub(r'^```(?:json)?\s*', '', raw_notes, flags=re.MULTILINE)
            notes = re.sub(r'```\s*$', '', notes, flags=re.MULTILINE).strip()

        return reasoning, notes

    except (EnvironmentError, ValueError):
        raise
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    finally:
        for path in tmp_paths_to_clean:
            try: os.unlink(path)
            except Exception: pass
        for api_file in api_files_to_delete:
            try: client.files.delete(name=api_file.name)
            except Exception: pass


def _call_gemini_with_fallback(client, model_name: str, contents: list):
    """Call Gemini with thinking. Auto-fallback Pro → Flash on 429."""
    def _do_call(model):
        try:
            config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=True)
            )
            return client.models.generate_content(
                model=model, contents=contents, config=config,
            )
        except Exception:
            return client.models.generate_content(
                model=model, contents=contents,
            )

    try:
        return _do_call(model_name)
    except Exception as e:
        err_str = str(e)
        if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and "pro" in model_name.lower():
            # Fallback to Flash
            fallback = "gemini-2.5-flash"
            try:
                return _do_call(fallback)
            except Exception as e2:
                raise RuntimeError(
                    f"Pro rate-limited, Flash also failed: {e2}"
                ) from e2
        raise


if __name__ == "__main__":
    print("HandScribe v2.0 — AI Processor Test")
    try:
        reasoning, notes = generate_notes(
            user_text="Give me Python important syntax for two pages",
            budget={"total_lines": 60, "word_budget": 400, "words_per_line": 7, "lines_per_page": 30},
            density="compact",
        )
        print("Notes:\n", notes)
    except Exception as e:
        print(f"Error: {e}")

<div align="center">

<img src="https://img.shields.io/badge/HandScriber-v2.0-7c6dfa?style=for-the-badge&logo=pencil&logoColor=white" />
&nbsp;
<img src="https://img.shields.io/badge/Gemini_2.5-Multimodal_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" />
&nbsp;
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />

# ✍️ HandScriber

### *Feed it anything. Get handwritten notes.*

**HandScriber** is an AI-powered multimodal notes generator that turns any content — YouTube lectures, PDFs, images, code files, or plain text — into beautiful, print-ready handwritten notes rendered on authentic paper styles.

[🚀 Try it Live](#) &nbsp;·&nbsp; [📺 Demo](#) &nbsp;·&nbsp; [🐛 Report Bug](https://github.com/Kishorens17/handscriber/issues)

</div>

---

## ✨ What Makes It Special

> Most note-taking apps just format text. **HandScriber thinks first, then writes** — like a real teacher creating notes for a student.

- 🧠 **Multimodal understanding** — combine YouTube + PDF + image + text in one request
- 📐 **Pixel-accurate rendering** — text wraps perfectly to fill the page (no awkward gaps)
- 🎯 **Budget-aware AI** — tells the AI exactly how many lines fit, enforced programmatically
- 📦 **Structured JSON output** — AI returns data, we control layout (no more AI-garbled formatting)
- ✋ **Human teacher voice** — notes read like a teacher wrote them, not an AI bot

---

## 🎬 Features at a Glance

| Feature | Details |
|---|---|
| **Input Types** | YouTube URLs · PDF · DOCX · PPTX · Images · Code files · Plain text |
| **Paper Styles** | Lined · Grid · Dotted · Blank · Yellow Legal · Graph · Cornell · Professional |
| **Fonts** | Caveat · Patrick Hand · Indie Flower · Architects Daughter |
| **Ink Colours** | Navy Blue · Black · Dark Green · Dark Red · Purple · Dark Brown |
| **Layout** | Single column or two-column |
| **Density** | Compact (cheat sheet) · Balanced (study notes) · Detailed (full guide) |
| **Export** | PNG per page + full PDF bundle |
| **AI Model** | Gemini 2.5 Flash (fast) or Gemini 2.5 Pro (quality) — auto-fallback |

---

## 🖼️ Screenshots

> *Generated with HandScriber — Physics formula sheet, two-column layout, Professional paper*

```
[Screenshot placeholder — add your screenshots here]
```

---

## 🏗️ Architecture

```
User Input (text / URL / file)
        │
        ▼
  AI Processor (Gemini 2.5)
  ┌─────────────────────────┐
  │  1. Budget calculation  │  ← knows exact lines/words that fit
  │  2. Density injection   │  ← compact / balanced / detailed
  │  3. JSON output         │  ← structured {title, sections, items}
  │  4. Truncation guard    │  ← hard cap if AI overshoots
  └─────────────────────────┘
        │
        ▼
  Note Renderer (Pillow)
  ┌─────────────────────────┐
  │  1. Paper generation    │  ← 8 styles, programmatically drawn
  │  2. Font loading        │  ← 4 handwriting fonts (auto-download)
  │  3. Pixel wrapping      │  ← getlength() not char count
  │  4. Heading hierarchy   │  ← bold + underline + spacing
  │  5. Symbol substitution │  ← Ω→Ohm, ρ→rho, π→pi
  │  6. Multi-page + 2-col  │  ← automatic page overflow
  └─────────────────────────┘
        │
        ▼
  Output: PNG pages + PDF
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A free [Gemini API key](https://aistudio.google.com/app/apikey)

### Installation

```bash
# Clone the repo
git clone https://github.com/Kishorens17/handscriber.git
cd handscriber

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set your API key
echo GEMINI_API_KEY=your_key_here > .env

# Run the app
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 💡 Usage Examples

**Formula sheet:**
```
Physics — Current and Electricity important formulas
```

**Syntax cheat sheet (2 pages, compact, 2 columns):**
```
Python important syntax for two pages
```

**From YouTube:**
```
https://youtube.com/watch?v=your_lecture  — summarize for exam
```

**Mixed inputs:**
> Upload a PDF lecture notes + type "focus on the formulas and key definitions" → HandScriber merges both into one unified notes set.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) |
| AI Brain | [Google Gemini 2.5](https://ai.google.dev/) (Flash + Pro) |
| Rendering | [Pillow](https://pillow.readthedocs.io/) |
| YouTube | [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/) |
| Fonts | Google Fonts (Caveat, Patrick Hand, Indie Flower, Architects Daughter) |

---

## 📁 Project Structure

```
handscriber/
├── app.py              # Streamlit web UI
├── ai_processor.py     # AI brain: Gemini API, JSON parsing, file extraction
├── note_renderer.py    # Pillow renderer: paper, fonts, layout, PDF
├── transcript.py       # YouTube transcript fetcher
├── requirements.txt    # Dependencies
├── .env.example        # API key template
└── assets/
    └── fonts/          # Cached handwriting fonts
```

---

## 🗺️ Roadmap

- [x] Multimodal input (YouTube, PDF, images, code)
- [x] Budget-aware AI generation
- [x] 8 paper styles + 4 fonts
- [x] Two-column layout
- [x] PDF export
- [x] Content density control
- [ ] QR code in page header linking to source
- [ ] Vercel deployment
- [ ] More handwriting fonts
- [ ] Offline mode (local LLM)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ✍️ and ☕ by <a href="https://github.com/Kishorens17">Kishorens17</a>
</div>

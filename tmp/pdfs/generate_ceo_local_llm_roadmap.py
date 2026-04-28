from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph


PAGE_W, PAGE_H = landscape(letter)
MARGIN = 28
GAP = 12
OUTPUT = Path("/Users/newuser/Desktop/CEO/output/pdf/ceo_local_llm_roadmap.pdf")


def build_styles():
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle(
            "Eyebrow",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=9,
            textColor=colors.HexColor("#7c5f17"),
        ),
        "title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=21.5,
            leading=22.5,
            textColor=colors.HexColor("#14263b"),
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=11.8,
            textColor=colors.HexColor("#4f5e6d"),
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=11.5,
            textColor=colors.white,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.75,
            leading=10.5,
            textColor=colors.HexColor("#1d2935"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.0,
            leading=8.2,
            textColor=colors.HexColor("#617180"),
        ),
        "inverse": ParagraphStyle(
            "Inverse",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.55,
            leading=10.3,
            textColor=colors.white,
        ),
        "phase_title": ParagraphStyle(
            "PhaseTitle",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.1,
            leading=10.2,
            textColor=colors.HexColor("#132a44"),
        ),
    }


def draw_paragraph(canvas, text, style, x, top_y, width):
    p = Paragraph(text, style)
    _, h = p.wrap(width, 1000)
    p.drawOn(canvas, x, top_y - h)
    return top_y - h


def card(canvas, x, y, w, h, fill, stroke=None, radius=14):
    canvas.setFillColor(fill)
    canvas.setStrokeColor(stroke or fill)
    canvas.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def section_header(canvas, title, x, y, w, fill):
    canvas.setFillColor(fill)
    canvas.roundRect(x, y, w, 22, 8, fill=1, stroke=0)
    canvas.rect(x, y, w, 11, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10.2)
    canvas.drawString(x + 10, y + 6.5, title)


def phase_block(canvas, s, x, top_y, width, number, title, body, badge_fill):
    badge_size = 22
    canvas.setFillColor(badge_fill)
    canvas.circle(x + 11, top_y - 11, 11, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    num_w = stringWidth(str(number), "Helvetica-Bold", 10)
    canvas.drawString(x + 11 - num_w / 2, top_y - 14.5, str(number))

    cursor = draw_paragraph(canvas, f"<b>{title}</b>", s["phase_title"], x + 28, top_y, width - 28)
    cursor -= 2
    cursor = draw_paragraph(canvas, body, s["body"], x + 28, cursor, width - 28)
    return cursor


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    s = build_styles()

    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(letter))
    c.setTitle("CEO Local LLM Roadmap")

    c.setFillColor(colors.HexColor("#f3efe7"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Background accents
    c.setFillColor(colors.HexColor("#efe5cf"))
    c.circle(PAGE_W - 18, PAGE_H - 18, 120, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#dae5df"))
    c.circle(44, 52, 86, fill=1, stroke=0)

    # Header
    header_h = 104
    header_y = PAGE_H - MARGIN - header_h
    card(c, MARGIN, header_y, PAGE_W - 2 * MARGIN, header_h, colors.white, stroke=colors.HexColor("#dbcdb5"))

    c.setFillColor(colors.HexColor("#f0d792"))
    c.roundRect(MARGIN + 16, header_y + header_h - 24, 122, 12, 5, fill=1, stroke=0)
    draw_paragraph(c, "EXECUTION ROADMAP", s["eyebrow"], MARGIN + 22, header_y + header_h - 14, 140)
    draw_paragraph(c, "CEO Local LLM<br/>Roadmap", s["title"], MARGIN + 18, header_y + header_h - 30, 360)
    draw_paragraph(
        c,
        "A one-page plan to move the current CEO app from a hosted-model assistant into a local-first Apple Silicon system with measurable performance gates.",
        s["subtitle"],
        MARGIN + 18,
        header_y + 30,
        420,
    )

    note_x = PAGE_W - MARGIN - 252
    note_y = header_y + 14
    note_w = 232
    note_h = 62
    card(c, note_x, note_y, note_w, note_h, colors.HexColor("#17324b"))
    draw_paragraph(
        c,
        "<b>Checked April 28, 2026:</b> hardware targets are current recommendations. "
        "Software selections below are proposed stack choices, not existing repo state.",
        s["inverse"],
        note_x + 12,
        note_y + note_h - 10,
        note_w - 24,
    )

    # Body columns
    body_top = header_y - 12
    body_h = body_top - MARGIN
    left_w = 290
    mid_w = 200
    right_w = PAGE_W - 2 * MARGIN - left_w - mid_w - GAP * 2
    left_x = MARGIN
    mid_x = left_x + left_w + GAP
    right_x = mid_x + mid_w + GAP

    # Left card: phases
    card(c, left_x, MARGIN, left_w, body_h, colors.white, stroke=colors.HexColor("#dccfb9"))
    section_header(c, "Phases", left_x + 10, body_top - 28, left_w - 20, colors.HexColor("#7f5e1e"))
    cur = body_top - 38
    phases = [
        (
            0,
            "Provider abstraction and instrumentation",
            "Keep the current CEO shell intact: Expo client, FastAPI gateway, WebSocket flow, voice I/O, and tool services. Add a model-provider interface, structured request logs, and basic latency and failure dashboards so Gemini and local backends are swappable.",
            colors.HexColor("#c9901b"),
        ),
        (
            1,
            "Local inference MVP",
            "Stand up a local inference server on Apple Silicon and route chat locally first. Keep hosted fallback only for timeout or failure cases. Benchmark task quality, tool-call reliability, token throughput, and context handling before changing any UI behavior.",
            colors.HexColor("#3f7e56"),
        ),
        (
            2,
            "Memory, retrieval, and eval gates",
            "Add a local memory store for notes, commands, and user preferences. Build a replay set from real CEO conversations and score every model change on task completion, latency, and hallucination rate. Do not scale hardware until evals show the local model is the real bottleneck.",
            colors.HexColor("#4f6f96"),
        ),
        (
            3,
            "Personal tuning and 24/7 operations",
            "Use Apple Silicon tooling for quantization and LoRA tuning, then harden the box with launchd, health checks, auto-restart, backups, and secure remote access. The final gate is simple: local-first service that beats the hosted baseline on your own recurring tasks.",
            colors.HexColor("#7f4e5d"),
        ),
    ]
    for i, (num, title, body, fill) in enumerate(phases):
        cur = phase_block(c, s, left_x + 16, cur, left_w - 32, num, title, body, fill)
        if i < len(phases) - 1:
            cur -= 14

    # Middle column
    mid_top_h = 230
    mid_bottom_h = body_h - mid_top_h - GAP

    card(c, mid_x, MARGIN + mid_bottom_h + GAP, mid_w, mid_top_h, colors.white, stroke=colors.HexColor("#d8ccb7"))
    section_header(c, "Hardware Targets", mid_x + 10, MARGIN + mid_bottom_h + GAP + mid_top_h - 28, mid_w - 20, colors.HexColor("#234d44"))
    cur = MARGIN + mid_bottom_h + GAP + mid_top_h - 38
    hardware_items = [
        "<b>Recommended 24/7 node</b><br/>Mac mini M4 Pro, 64GB unified memory, 1TB or 2TB SSD, optional 10Gb Ethernet. Best desk-resident balance for always-on local serving.",
        "<b>Portable dev box</b><br/>MacBook Pro M5 Pro, 48GB or 64GB unified memory, 1TB or 2TB SSD. Strong fit for development, local evals, and travel.",
        "<b>Stretch tier</b><br/>MacBook Pro M5 Max, 128GB unified memory, 2TB plus SSD. Only justify this if larger quantized models or heavier local tuning become the bottleneck.",
    ]
    for item in hardware_items:
        cur = draw_paragraph(c, item, s["body"], mid_x + 14, cur, mid_w - 28)
        cur -= 7

    card(c, mid_x, MARGIN, mid_w, mid_bottom_h, colors.HexColor("#fcfaf5"), stroke=colors.HexColor("#d8ccb7"))
    section_header(c, "Buying Rules", mid_x + 10, MARGIN + mid_bottom_h - 28, mid_w - 20, colors.HexColor("#7c5f17"))
    cur = MARGIN + mid_bottom_h - 38
    buy_rules = [
        "- Prioritize unified memory before SSD upgrades.",
        "- Use the Mac mini as the serving box; do not make the laptop your only 24/7 node.",
        "- Buy the larger machine only after replay evals show the current model size is the ceiling.",
        "- Keep one hosted fallback during rollout, then shrink cloud dependence deliberately.",
    ]
    for item in buy_rules:
        cur = draw_paragraph(c, item, s["body"], mid_x + 14, cur, mid_w - 28)
        cur -= 5

    # Right column
    right_top_h = 246
    right_bottom_h = body_h - right_top_h - GAP

    card(c, right_x, MARGIN + right_bottom_h + GAP, right_w, right_top_h, colors.white, stroke=colors.HexColor("#d8ccb7"))
    section_header(c, "Stack Choices", right_x + 10, MARGIN + right_bottom_h + GAP + right_top_h - 28, right_w - 20, colors.HexColor("#17324b"))
    cur = MARGIN + right_bottom_h + GAP + right_top_h - 38
    stack_items = [
        "<b>Keep from the repo:</b> Expo client, FastAPI gateway, WebSocket transport, `faster-whisper`, `edge-tts`, and the tool-service pattern.",
        "<b>Primary local serving:</b> `llama.cpp` server for OpenAI-compatible chat and embeddings endpoints.",
        "<b>Fast prototyping option:</b> `Ollama` for quick local swaps through `http://localhost:11434/api`.",
        "<b>Apple Silicon model work:</b> `MLX-LM` for quantization, low-rank tuning, and repeatable packaging.",
        "<b>Local data layer:</b> start with SQLite-backed memory plus file-based embeddings to avoid extra infra in v1.",
        "<b>Safety model:</b> retain the git diff-and-confirm workflow and add permission gates before destructive actions.",
    ]
    for item in stack_items:
        cur = draw_paragraph(c, item, s["body"], right_x + 14, cur, right_w - 28)
        cur -= 5

    card(c, right_x, MARGIN, right_w, right_bottom_h, colors.HexColor("#17324b"))
    section_header(c, "Success Gates", right_x + 10, MARGIN + right_bottom_h - 28, right_w - 20, colors.HexColor("#325c81"))
    cur = MARGIN + right_bottom_h - 38
    success_items = [
        "1. The same CEO UI can switch between hosted and local providers without app changes.",
        "2. More than 80 percent of routine chats are served locally before you remove hosted fallback.",
        "3. Replay evals show the local stack beats the hosted baseline on your own coding and assistant tasks.",
        "4. The node survives reboot, auto-recovers after failure, and can run unattended for 24/7 use.",
    ]
    for item in success_items:
        cur = draw_paragraph(c, item, s["inverse"], right_x + 14, cur, right_w - 28)
        cur -= 5

    footer = (
        "Source basis: current repo files for CEO app architecture; external docs checked April 28, 2026 for hardware and runtime options: "
        "Apple Mac mini (2024) specs, Apple MacBook Pro specs, Ollama API docs, MLX-LM, and llama.cpp server docs."
    )
    draw_paragraph(c, footer, s["small"], MARGIN + 2, 20, PAGE_W - 2 * MARGIN - 4)

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()

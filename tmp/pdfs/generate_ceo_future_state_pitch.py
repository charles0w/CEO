from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph


PAGE_W, PAGE_H = landscape(letter)
MARGIN = 30
GAP = 12
OUTPUT = Path("/Users/newuser/Desktop/CEO/output/pdf/ceo_future_state_pitch_local_llm.pdf")


def styles():
    base = getSampleStyleSheet()
    return {
        "eyebrow": ParagraphStyle(
            "Eyebrow",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=9,
            textColor=colors.HexColor("#ffe4a8"),
            tracking=1.2,
        ),
        "title": ParagraphStyle(
            "Title",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=30,
            textColor=colors.white,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=12.8,
            textColor=colors.HexColor("#d8e4f0"),
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=11,
            textColor=colors.HexColor("#13304d"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.0,
            leading=11.0,
            textColor=colors.HexColor("#1c2733"),
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=8.4,
            textColor=colors.HexColor("#657585"),
        ),
        "inverse": ParagraphStyle(
            "Inverse",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.6,
            leading=10.3,
            textColor=colors.white,
        ),
    }


def draw_paragraph(canvas, text, style, x, top_y, width):
    para = Paragraph(text, style)
    _, height = para.wrap(width, 1000)
    para.drawOn(canvas, x, top_y - height)
    return top_y - height


def card(canvas, x, y, w, h, fill, stroke=None):
    canvas.setFillColor(fill)
    canvas.setStrokeColor(stroke or fill)
    canvas.roundRect(x, y, w, h, 14, fill=1, stroke=1 if stroke else 0)


def section_title(canvas, text, x, y):
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#13304d"))
    canvas.drawString(x, y, text)


def main():
    s = styles()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(letter))
    c.setTitle("CEO Future-State Pitch")

    # Background
    c.setFillColor(colors.HexColor("#081726"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#123051"))
    c.circle(PAGE_W - 80, PAGE_H - 20, 150, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0d2137"))
    c.circle(PAGE_W - 10, PAGE_H - 90, 90, fill=1, stroke=0)

    # Header band
    header_h = 122
    header_y = PAGE_H - MARGIN - header_h
    card(c, MARGIN, header_y, PAGE_W - 2 * MARGIN, header_h, colors.HexColor("#0d2740"))
    c.setFillColor(colors.HexColor("#f2b84b"))
    c.roundRect(MARGIN + 18, header_y + header_h - 24, 96, 12, 5, fill=1, stroke=0)
    draw_paragraph(c, "FUTURE-STATE PITCH", s["eyebrow"], MARGIN + 22, header_y + header_h - 14, 120)
    draw_paragraph(c, "CEO Local AI Platform", s["title"], MARGIN + 18, header_y + header_h - 34, 320)
    draw_paragraph(
        c,
        "An always-on personal AI workstation designed to run locally on Apple Silicon, remove hosted token limits, "
        "and combine strong reasoning, tools, memory, and automation in one system.",
        s["subtitle"],
        MARGIN + 18,
        header_y + 52,
        420,
    )

    # Honesty box
    note_x = PAGE_W - MARGIN - 260
    note_y = header_y + 18
    note_w = 238
    note_h = 82
    card(c, note_x, note_y, note_w, note_h, colors.HexColor("#a33a2b"))
    draw_paragraph(
        c,
        "<b>Important:</b> this page is a product vision. The current repo implements a Gemini-based CEO assistant, "
        "not a finished local LLM stack.",
        s["inverse"],
        note_x + 12,
        note_y + note_h - 10,
        note_w - 24,
    )

    # Body grid
    top = header_y - 12
    body_h = top - MARGIN
    left_w = 228
    mid_w = 250
    right_w = PAGE_W - 2 * MARGIN - left_w - mid_w - GAP * 2
    left_x = MARGIN
    mid_x = left_x + left_w + GAP
    right_x = mid_x + mid_w + GAP

    # Left column
    card(c, left_x, MARGIN, left_w, body_h, colors.white)
    cur = top - 16
    section_title(c, "Who It Is For", left_x + 14, cur)
    cur -= 10
    cur = draw_paragraph(
        c,
        "A power user, founder, or developer who wants one private AI system that is always available, runs from a desk, "
        "and acts more like an operator than a chatbot.",
        s["body"],
        left_x + 14,
        cur,
        left_w - 28,
    )
    cur -= 10
    section_title(c, "Why This Exists", left_x + 14, cur)
    cur -= 10
    left_items = [
        "- No waiting for hosted token resets or usage caps.",
        "- Local uptime on a Mac mini or MacBook Pro that can stay online 24/7.",
        "- Stronger continuity through persistent memory, tools, and personal context.",
        "- One interface for coding, planning, notes, GitHub, and device actions.",
    ]
    for item in left_items:
        cur = draw_paragraph(c, item, s["body"], left_x + 14, cur, left_w - 28)
        cur -= 4

    cur -= 4
    section_title(c, "Current Starting Point", left_x + 14, cur)
    cur -= 10
    draw_paragraph(
        c,
        "Use the existing CEO app as the shell: mobile client, FastAPI backend, WebSocket transport, voice I/O, and tool integrations. "
        "Swap the hosted model layer for a local runtime over time.",
        s["body"],
        left_x + 14,
        cur,
        left_w - 28,
    )

    # Middle column
    card(c, mid_x, MARGIN, mid_w, body_h, colors.HexColor("#f5f8fb"))
    cur = top - 16
    section_title(c, "Target Capabilities", mid_x + 14, cur)
    cur -= 10
    mid_items = [
        "- Fast local inference with a primary model tuned for desktop use.",
        "- A planner/executor layer that can route tasks across coding, research, and automation flows.",
        "- Native tool use for files, git, notes, browser tasks, shell commands, and APIs.",
        "- Long-lived memory across sessions, projects, and personal preferences.",
        "- Always-on voice plus text interaction from phone or desktop.",
        "- Built-in evals to score outputs against speed, accuracy, and task completion.",
        "- Optional cloud escalation only when local capability is insufficient.",
    ]
    for item in mid_items:
        cur = draw_paragraph(c, item, s["body"], mid_x + 14, cur, mid_w - 28)
        cur -= 4

    # Right column, split cards
    right_top_h = 162
    right_bottom_h = body_h - right_top_h - GAP

    card(c, right_x, MARGIN + right_bottom_h + GAP, right_w, right_top_h, colors.white)
    cur = MARGIN + right_bottom_h + GAP + right_top_h - 16
    section_title(c, "Compact Architecture", right_x + 14, cur)
    cur -= 10
    arch_items = [
        "1. Client layer: mobile app, desktop UI, voice input/output.",
        "2. Local gateway: session manager, prompt assembly, auth, and observability.",
        "3. Model runtime: local inference server on Apple Silicon with quantized models.",
        "4. Orchestration: planner, tool router, memory retrieval, and task queue.",
        "5. Data plane: notes, repos, embeddings, logs, and evaluation results.",
    ]
    for item in arch_items:
        cur = draw_paragraph(c, item, s["body"], right_x + 14, cur, right_w - 28)
        cur -= 4

    card(c, right_x, MARGIN, right_w, right_bottom_h, colors.HexColor("#102a45"))
    cur = MARGIN + right_bottom_h - 16
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.white)
    c.drawString(right_x + 14, cur, "How It Would Run")
    cur -= 10
    run_items = [
        "1. Host the backend and model runtime on a Mac mini or MacBook Pro with Apple Silicon.",
        "2. Keep CEO running as a local service so the phone app connects over LAN by default.",
        "3. Store memory, logs, and project state locally first; sync selectively when needed.",
        "4. Use cloud models only as fallback, not as the default execution path.",
    ]
    for item in run_items:
        cur = draw_paragraph(c, item, s["inverse"], right_x + 14, cur, right_w - 28)
        cur -= 4

    footer = (
        "Positioning note: this pitch reflects the requested product direction. Repo evidence today points to a Gemini-based assistant foundation, "
        "which can serve as the first implementation layer for this broader local AI system."
    )
    draw_paragraph(c, footer, s["small"], MARGIN + 2, 22, PAGE_W - 2 * MARGIN - 4)

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()

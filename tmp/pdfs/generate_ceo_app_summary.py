from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph


PAGE_W, PAGE_H = landscape(letter)
MARGIN = 32
GAP = 12
BOX_PADDING = 10
OUTPUT = Path("/Users/newuser/Desktop/CEO/output/pdf/ceo_app_summary_repo_evidence.pdf")


def make_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=26,
            textColor=colors.HexColor("#0f2742"),
            spaceAfter=0,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#5b6b7b"),
        ),
        "section": ParagraphStyle(
            "Section",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=12,
            textColor=colors.white,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.1,
            leading=11.2,
            textColor=colors.HexColor("#1c2733"),
            spaceAfter=0,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.0,
            textColor=colors.HexColor("#5f6d79"),
            spaceAfter=0,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.3,
            textColor=colors.white,
            spaceAfter=0,
        ),
    }


def draw_para(canvas, text, style, x, top_y, width):
    para = Paragraph(text, style)
    _, height = para.wrap(width, 1000)
    para.drawOn(canvas, x, top_y - height)
    return top_y - height


def draw_box(canvas, x, y, width, height, title, title_fill="#0f2742"):
    canvas.setFillColor(colors.white)
    canvas.setStrokeColor(colors.HexColor("#c7d2dd"))
    canvas.roundRect(x, y, width, height, 10, fill=1, stroke=1)

    title_h = 20
    canvas.setFillColor(colors.HexColor(title_fill))
    canvas.roundRect(x, y + height - title_h, width, title_h, 10, fill=1, stroke=0)
    canvas.rect(x, y + height - title_h, width, 10, fill=1, stroke=0)

    return {
        "content_x": x + BOX_PADDING,
        "content_top": y + height - title_h - 8,
        "content_width": width - BOX_PADDING * 2,
    }


def draw_section(canvas, styles, x, y, width, height, title, items, title_fill="#0f2742"):
    content = draw_box(canvas, x, y, width, height, title, title_fill=title_fill)
    title_w = stringWidth(title, "Helvetica-Bold", 10.5)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10.5)
    canvas.drawString(x + 10, y + height - 14, title)

    cursor = content["content_top"]
    for item in items:
        cursor = draw_para(canvas, item, styles["body"], content["content_x"], cursor, content["content_width"])
        cursor -= 4
    return cursor


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()

    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(letter))
    c.setTitle("CEO App Summary (Repo Evidence)")

    c.setFillColor(colors.HexColor("#eef3f7"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Header
    header_h = 82
    header_y = PAGE_H - MARGIN - header_h
    c.setFillColor(colors.white)
    c.roundRect(MARGIN, header_y, PAGE_W - 2 * MARGIN, header_h, 12, fill=1, stroke=0)

    title_x = MARGIN + 18
    title_top = PAGE_H - MARGIN - 16
    draw_para(c, "CEO App Summary", styles["title"], title_x, title_top, 250)
    draw_para(
        c,
        "One-page overview based on repo evidence from README and core backend/mobile files.",
        styles["subtitle"],
        title_x,
        title_top - 28,
        300,
    )

    callout_x = PAGE_W - MARGIN - 340
    callout_y = header_y + 12
    callout_w = 320
    callout_h = 58
    c.setFillColor(colors.HexColor("#832a2a"))
    c.roundRect(callout_x, callout_y, callout_w, callout_h, 10, fill=1, stroke=0)
    callout = (
        "<b>Repo gap:</b> a custom local LLM that outperforms Codex/Claude is "
        "<b>Not found in repo.</b> The codebase shows a Gemini-powered assistant app."
    )
    draw_para(c, callout, styles["callout"], callout_x + 12, callout_y + callout_h - 10, callout_w - 24)

    # Columns
    content_top = header_y - 12
    col_w = (PAGE_W - 2 * MARGIN - GAP) / 2
    left_x = MARGIN
    right_x = left_x + col_w + GAP
    bottom_y = MARGIN
    content_h = content_top - bottom_y

    left_top_h = 150
    left_bottom_h = content_h - left_top_h - GAP

    right_top_h = 198
    right_mid_h = 136
    right_bottom_h = content_h - right_top_h - right_mid_h - GAP * 2

    left_top_y = bottom_y + left_bottom_h + GAP
    right_mid_y = bottom_y + right_bottom_h + GAP
    right_top_y = right_mid_y + right_mid_h + GAP

    draw_section(
        c,
        styles,
        left_x,
        left_top_y,
        col_w,
        left_top_h,
        "What It Is / Who It Is For",
        [
            "CEO is a Jarvis-style personal AI assistant with a FastAPI backend and an Expo mobile/web client for voice or text chat.",
            "Repo evidence shows <b>Gemini 2.0 Flash</b> as the model backend; a self-hosted local model is <b>Not found in repo.</b>",
            "<b>Primary persona:</b> Charles ('Boss'), the named user in the system prompt and assistant copy.",
            "<b>General multi-user product positioning:</b> <b>Not found in repo.</b>",
        ],
        title_fill="#133b5c",
    )

    draw_section(
        c,
        styles,
        left_x,
        bottom_y,
        col_w,
        left_bottom_h,
        "How It Works",
        [
            "1. <b>Client:</b> `ChatScreen` captures typed text or hold-to-record audio; `SettingsScreen` stores the WebSocket URL in AsyncStorage.",
            "2. <b>Transport:</b> `useWebSocket` opens an auto-reconnecting connection and sends JSON messages to FastAPI at `/ws`.",
            "3. <b>Voice path:</b> voice uploads are base64-decoded, transcribed by `VoiceService` with `faster-whisper`, then forwarded as text.",
            "4. <b>LLM path:</b> `GeminiService` sends the message to Gemini with automatic function calling enabled.",
            "5. <b>Tools:</b> Gemini can call `ObsidianService`, `GitHubService`, and `ClaudeCodeService` (including git diff/commit/push helpers).",
            "6. <b>Response path:</b> reply text is converted to MP3 by `edge-tts` and returned with the text payload; REST endpoints also expose `/health`, `/transcribe`, and `/speak`.",
        ],
        title_fill="#0f2742",
    )

    draw_section(
        c,
        styles,
        right_x,
        right_top_y,
        col_w,
        right_top_h,
        "What It Does",
        [
            "- Accepts text chat and push-to-talk voice input from the mobile/web client.",
            "- Auto-reconnects the client WebSocket and supports conversation reset.",
            "- Transcribes speech on CPU with `faster-whisper`.",
            "- Synthesizes spoken replies with `edge-tts`.",
            "- Reads, writes, lists, and searches an Obsidian vault.",
            "- Lists GitHub repos/issues and reads repo files when `GITHUB_TOKEN` is set.",
            "- Runs Claude Code CLI prompts and enforces a git safety gate before commit or push.",
        ],
        title_fill="#18506f",
    )

    draw_section(
        c,
        styles,
        right_x,
        right_mid_y,
        col_w,
        right_mid_h,
        "How To Run",
        [
            "1. <b>Backend:</b> in `backend/`, copy `.env.example` to `.env`, set `GEMINI_API_KEY`, install `ffmpeg`, then run `start.bat`.",
            "2. <b>Mobile/web:</b> in `mobile/`, run `npm install --legacy-peer-deps`, then `npx expo start` or `npx expo start --web`.",
            "3. <b>Connect:</b> in the app Settings screen, set `ws://&lt;desktop-ip&gt;:8000/ws`; remote access uses ngrok.",
            "<b>Minimal prerequisites:</b> Python 3.10+, Node.js 18+, ffmpeg, and a Gemini API key.",
        ],
        title_fill="#1f5f5b",
    )

    draw_section(
        c,
        styles,
        right_x,
        bottom_y,
        col_w,
        right_bottom_h,
        "Not Found In Repo",
        [
            "- A custom local LLM training or inference stack.",
            "- Benchmarks or evidence that this app outperforms Codex or Claude.",
            "- Apple Silicon / Mac mini 24/7 deployment instructions beyond generic local hosting notes.",
        ],
        title_fill="#6c4b1f",
    )

    footer = (
        "Sources used: README.md; backend/main.py; backend/config.py; "
        "backend/services/gemini_service.py; backend/services/voice_service.py; "
        "backend/services/obsidian_service.py; backend/services/github_service.py; "
        "backend/services/claude_code_service.py; mobile/App.tsx; "
        "mobile/src/screens/ChatScreen.tsx; mobile/src/screens/SettingsScreen.tsx; "
        "mobile/src/hooks/useWebSocket.ts."
    )
    draw_para(c, footer, styles["small"], MARGIN + 4, 24, PAGE_W - 2 * MARGIN - 8)

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()

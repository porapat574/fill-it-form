"""
main.py — Flask API for PDF generation (Render.com)
"""

import io
import os
import base64
from flask import Flask, request, jsonify
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__)

# ── Thai Font ──────────────────────────────────────────────────
FONT_FILE = "THSarabun.ttf"  # หรือ Sarabun-Regular.ttf
if os.path.exists(FONT_FILE):
    pdfmetrics.registerFont(TTFont("Thai", FONT_FILE))
else:
    raise FileNotFoundError(f"ไม่พบ font file: {FONT_FILE}")

PAGE_W = 612.0
PAGE_H = 792.0
BLUE   = (0.0, 0.0, 1.0)
BLACK  = (0.0, 0.0, 0.0)
WHITE  = (1.0, 1.0, 1.0)

BLUE_REGIONS = {
    "doc_no":           (441.7, 118, 536.3, 133),
    "fullname_th":      (185.0, 137, 370.0, 152),
    "date":             (420.0, 137, 536.3, 152),
    "fullname_en":      (202.4, 171, 350.0, 186),
    "emp_id":           (430.0, 171, 536.3, 186),
    "workplace":        (183.4, 199, 536.3, 214),
    "department":       (197.5, 226, 536.3, 241),
    "position":         (183.4, 254, 536.3, 269),
    "req_type":         (183.4, 281, 536.3, 296),
    "program":          (197.5, 309, 536.3, 324),
    "detail":           (183.2, 364, 536.3, 390),
    "note":             (114.1, 505, 536.3, 530),
    "sign_requester":   (142.4, 608, 240.0, 623),
    "sign_date":        (155.9, 625, 220.0, 640),
    "sign_approver":    (400.0, 607, 536.3, 622),
    "sign_supervisor":  (127.8, 687, 310.0, 702),
    "sign_recorder":    (385.0, 687, 536.3, 702),
}

def top_to_rl(top, font_size=11):
    return PAGE_H - top - font_size + 2

def fill_pdf(data: dict, template_bytes: bytes) -> bytes:
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    for field, (x0, top, x1, bot) in BLUE_REGIONS.items():
        c.setFillColorRGB(*WHITE)
        c.setStrokeColorRGB(*WHITE)
        rl_y = PAGE_H - bot
        c.rect(x0 - 1, rl_y, (x1 - x0) + 2, (bot - top) + 2, fill=1, stroke=0)

        value = data.get(field, "")
        if not value:
            continue

        c.setFillColorRGB(*BLACK if field.startswith("sign_") else BLUE)
        c.setFont("Thai", 11)
        c.drawString(x0, top_to_rl(top), str(value))

    c.save()
    buf.seek(0)

    template = PdfReader(io.BytesIO(template_bytes))
    overlay  = PdfReader(buf)
    writer   = PdfWriter()
    page     = template.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


@app.route("/fill_it_form", methods=["POST"])
def fill_it_form():
    try:
        body         = request.get_json(force=True)
        data         = body.get("data", {})
        template_b64 = body.get("template_b64", "")

        if not template_b64:
            return jsonify({"ok": False, "error": "ไม่มี template_b64"}), 400

        template_bytes = base64.b64decode(template_b64)
        pdf_bytes      = fill_pdf(data, template_bytes)
        pdf_b64        = base64.b64encode(pdf_bytes).decode("utf-8")

        return jsonify({"ok": True, "pdf_b64": pdf_b64})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "IT Form PDF Generator"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
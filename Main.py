"""
fill_it_form v8.3
"""

import io
import base64
from flask import Flask, request, jsonify
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_FILE = "THSarabun.ttf"
pdfmetrics.registerFont(TTFont("Thai", FONT_FILE))

PAGE_W = 612.0
PAGE_H = 792.0
BLUE  = (0.0, 0.0, 1.0)
BLACK = (0.0, 0.0, 0.0)
WHITE = (1.0, 1.0, 1.0)

FIELDS = {
    "doc_no":          (441.7, 118.0, 536.3, 133.0, 11, BLUE),
    "fullname_th":     (160.0, 143.0, 368.0, 152.0, 11, BLUE),
    "date":            (450.0, 137.0, 536.3, 152.0, 11, BLUE),
    "fullname_en":     (202.4, 171.0, 350.0, 186.0, 11, BLUE),
    "emp_id":          (450.0, 171.0, 536.3, 186.0, 11, BLUE),
    "workplace":       (183.4, 199.0, 536.3, 214.0, 11, BLUE),
    "department":      (197.5, 226.0, 536.3, 241.0, 11, BLUE),
    "position":        (183.4, 254.0, 536.3, 269.0, 11, BLUE),
    "req_type":        (183.4, 281.0, 536.3, 296.0, 11, BLUE),
    "program":         (197.5, 309.0, 536.3, 324.0, 11, BLUE),
    "detail":          (183.2, 364.0, 536.3, 382.0, 11, BLUE),
    "detail2":         ( 57.0, 382.0, 536.3, 400.0, 11, BLUE),
    "note":            (114.1, 505.0, 536.3, 523.0, 11, BLACK),
    "sign_requester":  (134.0, 609.0, 223.0, 626.0, 11, BLACK),
    "sign_date":       (134.0, 626.0, 223.0, 640.0, 10, BLACK),
    "sign_approver":   (395.0, 609.0, 473.0, 626.0, 11, BLACK),
    "sign_supervisor": (132.0, 689.0, 217.0, 706.0, 11, BLACK),
    "sign_recorder":   (396.0, 687.0, 475.0, 704.0, 11, BLACK),
}


def calc_text_y(top, bot, fsize):
    """Vertically center text inside field. Keeps descenders off the bottom underline."""
    field_h = bot - top
    rl_bot  = PAGE_H - bot
    # visual center: ascender ~70% above baseline, descender ~30% below
    # → baseline = midpoint - fsize*0.3
    return rl_bot + field_h / 2 - fsize * 0.3


def fill_pdf(data: dict, template_bytes: bytes) -> bytes:
    data = dict(data)
    data["sign_approver"] = data.get("sign_approver") or "ภาณุ ธีรภานุ"

    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))

    for field, (x0, top, x1, bot, fsize, color) in FIELDS.items():
        value = str(data.get(field, "") or "")

        c.setFillColorRGB(*WHITE)
        c.setStrokeColorRGB(*WHITE)
        rl_bot = PAGE_H - bot
        # เว้น 1pt ล่าง (bottom underline) และ 2pt บน (top border)
        c.rect(x0, rl_bot + 1, x1 - x0, bot - top - 3, fill=1, stroke=0)

        if not value:
            continue

        c.setFillColorRGB(*color)
        c.setFont("Thai", fsize)
        c.drawString(x0 + 1, calc_text_y(top, bot, fsize), value)

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


app = Flask(__name__)

@app.route("/fill_it_form", methods=["POST"])
def handle_fill_it_form():
    try:
        body           = request.get_json(force=True)
        data           = body["data"]
        template_bytes = base64.b64decode(body["template_b64"])
        pdf_bytes      = fill_pdf(data, template_bytes)
        return jsonify({"ok": True, "pdf_b64": base64.b64encode(pdf_bytes).decode()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return "ok", 200

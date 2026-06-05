"""
fill_it_form v8.2
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


def top_to_rl(top, font_size=11):
    return PAGE_H - top - font_size + 2


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
        # ✅ FIX 1: ลด height 2pt — ป้องกัน white rect ทับ border ด้านล่าง
        c.rect(x0, rl_bot, x1 - x0, bot - top - 2, fill=1, stroke=0)

        if not value:
            continue

        c.setFillColorRGB(*color)
        c.setFont("Thai", fsize)
        # ✅ FIX 2: ลด left padding 3→1
        c.drawString(x0 + 1, top_to_rl(top, fsize), value)

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

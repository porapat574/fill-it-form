"""
fill_it_form v8 — ไม่ white-out วงเล็บ template, แก้ fullname_th border
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
    # top 137→140, bot 152→149 — หลีกเส้น border แนวนอน
    "fullname_th":     (185.0, 140.0, 368.0, 149.0, 11, BLUE),
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

    # x0 เลื่อน +12px พ้น '('  /  x1 ถอย -8px ก่อน ')'
    # '(' positions: 122.5, 383.6, 120.4, 384.6
    # ')' positions: 231.8, 481.0, 225.7, 483.1
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

        # white-out เฉพาะพื้นที่ข้อความ ไม่แตะวงเล็บ
        c.setFillColorRGB(*WHITE)
        c.setStrokeColorRGB(*WHITE)
        rl_bot = PAGE_H - bot
        c.rect(x0, rl_bot, x1 - x0, bot - top, fill=1, stroke=0)

        if not value:
            continue

        c.setFillColorRGB(*color)
        c.setFont("Thai", fsize)
        c.drawString(x0 + 3, top_to_rl(top, fsize), value)

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


# ── Flask ────────────────────────────────────────────────────
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


if __name__ == "__main__":
    with open("template.pdf", "rb") as f:
        tmpl = f.read()

    sample = {
        "doc_no":          "IT-TEST-001",
        "fullname_th":     "ปวรวรรณ สิทธิวุฒิ",
        "date":            "1/6/2569",
        "fullname_en":     "Paworawan Sittiwut",
        "emp_id":          "SPCO23",
        "workplace":       "S.P. Auto Corporation Co.,Ltd. (Head Office)",
        "department":      "Accounting",
        "position":        "ผู้จัดการแผนก",
        "req_type":        "ขอใช้สิทธิ์ผู้ดูแลระบบ (Super User / Administrator)",
        "program":         "AccCloud ระบบจัดการคำสั่งซื้อ และการบริการ",
        "detail":          "กำหนดสิทธิ์การใช้งานพนักงานใหม่",
        "detail2":         "",
        "note":            "ภรภัทร ดวงแก้ว / SPCO41 / ขอเปิดสิทธิ์ SPCO SP SPM",
        "sign_requester":  "ปวรวรรณ สิทธิวุฒิ",
        "sign_date":       "1/6/2569",
        "sign_approver":   "",
        "sign_supervisor": "กนกกาญจน คณารัตนดิลก",
        "sign_recorder":   "ภรภัทร ดวงแก้ว",
    }

    result = fill_pdf(sample, tmpl)
    with open("filled_v8.pdf", "wb") as f:
        f.write(result)
    print("✅ filled_v8.pdf")

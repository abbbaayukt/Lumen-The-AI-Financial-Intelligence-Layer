import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def split_name(full_name: str):
    parts = full_name.strip().split()
    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return parts[0], " ".join(parts[1:-1]), parts[-1]

def overlay_page1(data, w, h):
    buf = io.BytesIO()
    can = canvas.Canvas(buf, pagesize=(w, h))
    can.setFont("Helvetica", 9)

    can.setFillColor(colors.white)
    can.rect(275, h - 535.53, 290, 25, fill=1, stroke=0)
    can.rect(392, h - 598.8, 180, 50, fill=1, stroke=0)

    can.setFillColor(colors.black)

    can.drawString(160, h - 211, data["name"])

    can.drawString(200, h - 241, data["dob"])
    can.drawString(350, h - 241, data["aadhaar"])
    can.drawString(50,  h - 241, data["pan"])

    can.drawString(80,  h - 518.7, data["mobile"])
    can.drawString(159, h - 530,  data["email"])
    can.drawString(420, h - 578.8, data["employment"])

    text = can.beginText()
    text.setTextOrigin(300, h - 371)
    for line in data["address"].splitlines():
        text.textLine(line)
    can.drawText(text)

    can.save()
    buf.seek(0)
    return buf

def overlay_page2(data, w, h):
    buf = io.BytesIO()
    can = canvas.Canvas(buf, pagesize=(w, h))
    can.setFont("Helvetica", 9)
    can.setFillColor(colors.black)

    if data["electricity_expenditure"] > 100000:
        can.drawString(470, h - 97, str(data["electricity_expenditure"]))

    if data["employment"] == "Pensioner":
        can.drawString(360, h - 220, str(data["salary_pensioner"]))
    else:
        can.drawString(360, h - 173, str(data["salary_non_pensioner"]))

    if data["entertainment_income"] != 0:
        can.drawString(360, h - 343, str(data["entertainment_income"]))

    if data["income_over_salary"] != 0:
        can.drawString(480, h - 535, str(data["income_over_salary"]))

    can.drawString(480, h - 600, str(data["total_income"]))
    can.drawString(480, h - 160, str(data["gross_salary_B1"]))

    can.save()
    buf.seek(0)
    return buf

def overlay_page3(data, w, h):
    buf = io.BytesIO()
    can = canvas.Canvas(buf, pagesize=(w, h))
    can.setFont("Helvetica", 9)
    can.drawString(133, h - 296, str(data["tax_payable"]))
    can.save()
    buf.seek(0)
    return buf

def apply_overlay(base_page, overlay_stream):
    overlay_reader = PdfReader(overlay_stream)
    overlay_page = overlay_reader.pages[0]
    base_page.merge_page(overlay_page)
    return base_page

def compute_income_details(transactions, employment, salary):
    r = {}

    r["electricity_expenditure"] = abs(sum(
        t["amount"] for t in transactions
        if t.get("category") == "electricity" and t["amount"] < 0
    ))

    if employment.lower() == "pensioner":
        r["salary_pensioner"] = salary
        r["salary_non_pensioner"] = 0
    else:
        r["salary_non_pensioner"] = salary
        r["salary_pensioner"] = 0

    r["income_over_salary"] = sum(
        t["amount"] for t in transactions
        if t["amount"] > 0 and t.get("category") != "salary"
    )

    r["gross_salary_B1"] = r["salary_non_pensioner"] + r["salary_pensioner"]

    r["entertainment_income"] = sum(
        t["amount"] for t in transactions
        if t.get("category") == "entertainment" and t["amount"] > 0
    )

    r["total_income"] = r["gross_salary_B1"] + r["income_over_salary"]

    total = r["total_income"]
    tax = 0

    if total > 1500000:
        tax += (total - 1500000) * 0.30
        total = 1500000
    if total > 1200000:
        tax += (total - 1200000) * 0.20
        total = 1200000
    if total > 900000:
        tax += (total - 900000) * 0.15
        total = 900000
    if total > 600000:
        tax += (total - 600000) * 0.10
        total = 600000
    if total > 300000:
        tax += (total - 300000) * 0.05

    r["tax_payable"] = round(tax, 2)
    return r

def generate_itr_pdf(form_data, transactions, template_path):

    computed = compute_income_details(
        transactions,
        form_data["employment"],
        form_data["salary"]
    )

    data = form_data | computed

    reader = PdfReader(template_path)
    writer = PdfWriter()

    overlay_fns = [overlay_page1, overlay_page2, overlay_page3]

    for i, fn in enumerate(overlay_fns):
        page = reader.pages[i]
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)

        overlay_stream = fn(data, w, h)
        merged_page = apply_overlay(page, overlay_stream)
        writer.add_page(merged_page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out
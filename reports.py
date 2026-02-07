from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generate_customer_receipt(
    output_path,
    shop_name,
    shop_address,
    shop_contact,
    customer,
    month_label,
    deliveries,
    payments,
):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 20 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, y, shop_name)
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Milk Billing Receipt")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    if shop_address:
        c.drawString(20 * mm, y, f"Shop Address: {shop_address}")
        y -= 5 * mm
    if shop_contact:
        c.drawString(20 * mm, y, f"Shop Contact: {shop_contact}")
        y -= 5 * mm

    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Customer: {customer['name']}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Contact: {customer['contact'] or ''}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Address: {customer['address'] or ''}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Month: {month_label}")

    y -= 10 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Deliveries")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "Date")
    c.drawString(45 * mm, y, "Item")
    c.drawString(85 * mm, y, "Qty")
    c.drawString(100 * mm, y, "Price")
    c.drawString(120 * mm, y, "Partner")
    y -= 4 * mm

    total_amount = 0.0
    c.setFont("Helvetica", 9)
    for row in deliveries:
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 9)
        amount = row["quantity"] * row["price"]
        total_amount += amount
        c.drawString(20 * mm, y, row["date"])
        c.drawString(45 * mm, y, row["item_name"])
        c.drawString(85 * mm, y, str(row["quantity"]))
        c.drawString(100 * mm, y, f"{row['price']:.2f}")
        c.drawString(120 * mm, y, row["partner_name"])
        y -= 4 * mm

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Total Charges: {total_amount:.2f}")

    y -= 10 * mm
    c.drawString(20 * mm, y, "Advance Payments")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "Date")
    c.drawString(45 * mm, y, "Amount")
    c.drawString(70 * mm, y, "Notes")
    y -= 4 * mm
    c.setFont("Helvetica", 9)

    total_paid = 0.0
    for row in payments:
        if y < 25 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica", 9)
        total_paid += row["amount"]
        c.drawString(20 * mm, y, row["date"])
        c.drawString(45 * mm, y, f"{row['amount']:.2f}")
        c.drawString(70 * mm, y, row["notes"] or "")
        y -= 4 * mm

    y -= 6 * mm
    dues = total_amount - total_paid
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Total Paid: {total_paid:.2f}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"Dues: {dues:.2f}")

    c.showPage()
    c.save()

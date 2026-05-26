from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

def create_pdf(dn, df):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []

    # HEADER
    elements.append(Table([[f"AFLEVERBON {dn}"]]))

    # ==========================
    # TABLE DATA
    # ==========================
    data = [
        ["ARTIKEL", "AANTAL", "CONSUMENTEENHEID", "OMSCHRIJVING", "PRIJS"]
    ]

    for _, r in df.iterrows():

        qty = int(r["quantity_(bundles)"])
        price = float(r["price per bundle"])
        total = qty * price

        data.append([
            r["SKU"],
            f"{qty} UN",
            total,
            "",  # descrizione
            f"{price:.2f}€"
        ])

    # ==========================
    # TABLE STYLE
    # ==========================
    table = Table(data, colWidths=[100, 80, 100, 180, 60])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer

import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


st.set_page_config(layout="wide")
st.title("📦 Delivery Note Generator - PMI Style")

file = st.file_uploader("Upload IT Excel", type=["xlsx"])
generate = st.button("🚀 Generate")


# ==========================
# PDF CREATOR (PIXEL PERFECT BASE)
# ==========================
def create_pdf(dn, data):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    W, H = A4
    row = data.iloc[0]

    # ==========================
    # HEADER LEFT
    # ==========================
    c.setFont("Helvetica", 8)
    c.drawString(40, H-40, "Philip Morris Wattweg 29,")
    c.drawString(40, H-52, "4622 RA, Bergen Op Zoom,")
    c.drawString(40, H-64, "Netherlands")

    # ==========================
    # TITLE
    # ==========================
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, H-60, "AFLEVERBON")

    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, H-75, str(dn))

    # ==========================
    # RIGHT BOX
    # ==========================
    c.rect(W-150, H-90, 110, 60)

    c.setFont("Helvetica", 8)
    c.drawString(W-140, H-45, f"Lev: {dn}")
    c.drawString(W-140, H-60, "Blad: 1/1")
    c.drawString(W-140, H-75, "Ref:")

    # ==========================
    # BOX 1
    # ==========================
    y = H - 120
    c.rect(40, y, W-80, 40)

    c.setFont("Helvetica", 9)
    c.drawString(50, y+25, "AFZENDLOCATIE")
    c.drawString(220, y+25, "VERVOERDER")
    c.drawString(380, y+25, "ROUTE")

    c.drawString(50, y+10, "Bergen Op Zoom")
    c.drawString(220, y+10, "Speedlink B.V")
    c.drawString(380, y+10, str(dn))

    # ==========================
    # BOX 2
    # ==========================
    y2 = y - 50
    c.rect(40, y2, W-80, 40)

    c.drawString(50, y2+25, "KLANTCODE")
    c.drawString(220, y2+25, "SOORT BESTELLING")
    c.drawString(380, y2+25, "LEVERDATUM")

    c.drawString(50, y2+10, str(row["CLIENT"]))
    c.drawString(220, y2+10, "Delivery")

    # ==========================
    # CUSTOMER BOX
    # ==========================
    y3 = y2 - 90
    box_w = (W-80)/2

    c.rect(40, y3, box_w, 80)
    c.rect(40+box_w, y3, box_w, 80)

    c.setFont("Helvetica", 8)

    c.drawString(45, y3+60, "ONTVANGER VAN GOEDEREN")
    c.drawString(45, y3+45, row["NAME"])
    c.drawString(45, y3+30, row["STRASSE"])
    c.drawString(45, y3+15, f"{row['PC']} {row['CITY']}")

    c.drawString(45+box_w, y3+60, "ONTVANGER VAN DE AFLEVERINGSBON")

    # ==========================
    # TABLE HEADER
    # ==========================
    y4 = y3 - 30

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y4, "ARTIKEL")
    c.drawString(120, y4, "OMSCHRIJVING")
    c.drawString(350, y4, "AANTAL")
    c.drawString(420, y4, "PRIJS")

    # ==========================
    # TABLE ROWS
    # ==========================
    y_row = y4 - 15
    c.setFont("Helvetica", 8)

    page = 1
    total_pages = 1

    for _, r in data.iterrows():

        c.drawString(40, y_row, str(r["SKU"]))
        c.drawString(120, y_row, "")  # descrizione optional
        c.drawString(350, y_row, str(r["quantity_(bundles)"]))
        c.drawString(420, y_row, str(r["price per bundle"]))

        y_row -= 12

        # NUOVA PAGINA
        if y_row < 60:
            c.setFont("Helvetica", 8)
            c.drawString(W-140, 40, f"Blad: {page}")
            c.showPage()
            page += 1

            y_row = H - 60

    # footer ultima pagina
    c.drawString(W-140, 40, f"Blad: {page}")

    c.save()
    buffer.seek(0)

    return buffer


# ==========================
# MAIN
# ==========================
if generate and file:

    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()

    # FIX colonne bundles
    if "quantity_(bundles)" not in df.columns:
        for col in df.columns:
            if "bundles" in col.lower():
                df = df.rename(columns={col: "quantity_(bundles)"})

    grouped = df.groupby("DN")

    for dn, group in grouped:

        st.write(f"Processing DN {dn}")

        pdf = create_pdf(dn, group)

        st.download_button(
            label=f"📄 Download {dn}",
            data=pdf,
            file_name=f"{dn}.pdf"
        )

    st.success("✅ DONE")

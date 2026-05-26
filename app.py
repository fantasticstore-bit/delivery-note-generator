import streamlit as st
import pandas2 import PdfReader, PdfWriterimport pandas as pd


st.title("📦 Delivery Note Generator (TEMPLATE MODE)")

excel_file = st.file_uploader("Upload Excel IT", type=["xlsx"])
template_file = st.file_uploader("Upload PDF Template", type=["pdf"])

generate = st.button("🚀 Generate")


# ==========================
# CREA OVERLAY DATI
# ==========================
def create_overlay(dn, data):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    W, H = A4
    row = data.iloc[0]

    # ==========================
    # 🔥 QUI SONO LE COORDINATE REALI (ALLINEATE AL PDF)
    # ==========================

    c.setFont("Helvetica", 9)

    # DN
    c.drawString(300, 760, str(dn))

    # CLIENTE
    c.drawString(60, 610, row["NAME"])
    c.drawString(60, 595, row["STRASSE"])
    c.drawString(60, 580, f"{row['PC']} {row['CITY']}")

    # CLIENT CODE
    c.drawString(60, 660, str(row["CLIENT"]))

    # ==========================
    # TABELLA
    # ==========================
    y = 430

    for _, r in data.iterrows():

        c.drawString(60, y, str(r["SKU"]))
        c.drawString(340, y, str(r["quantity_(bundles)"]))
        c.drawString(420, y, str(r["price per bundle"]))

        y -= 12

        if y < 50:
            c.showPage()
            y = 780

    c.save()
    buffer.seek(0)

    return buffer


# ==========================
# MERGE TEMPLATE + OVERLAY
# ==========================
def merge_pdf(template, overlay):

    template_reader = PdfReader(template)
    overlay_reader = PdfReader(overlay)

    writer = PdfWriter()

    for i in range(len(template_reader.pages)):

        page = template_reader.pages[i]

        if i < len(overlay_reader.pages):
            page.merge_page(overlay_reader.pages[i])

        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output


# ==========================
# MAIN
# ==========================
if generate and excel_file and template_file:

    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip()

    if "quantity_(bundles)" not in df.columns:
        for col in df.columns:
            if "bundles" in col.lower():
                df = df.rename(columns={col: "quantity_(bundles)"})

    grouped = df.groupby("DN")

    for dn, group in grouped:

        st.write(f"Processing {dn}")

        overlay = create_overlay(dn, group)

        final_pdf = merge_pdf(template_file, overlay)

        st.download_button(
            f"📄 Download {dn}",
            final_pdf,
            file_name=f"{dn}.pdf"
        )

    st.success("✅ DONE")
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

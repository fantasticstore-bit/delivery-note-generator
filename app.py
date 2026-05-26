import streamlit as stimport streamlit asfrom reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter


st.set_page_config(layout="wide")
st.title("📦 Delivery Note Generator - FINAL")

excel_file = st.file_uploader("Upload Excel IT", type=["xlsx"])
template_file = st.file_uploader("Upload PDF Template", type=["pdf"])

generate = st.button("🚀 Generate")


# ======================================
# CREATE OVERLAY (PIXEL + SAP STYLE)
# ======================================
def create_overlay(dn, data):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    W, H = A4
    row = data.iloc[0]

    # FONT (monospace = allineamento perfetto)
    c.setFont("Courier", 9)

    # ==========================
    # HEADER DATA
    # ==========================
    c.drawString(300, 760, str(dn))                # DN centro
    c.drawString(60, 660, str(row["CLIENT"]))      # customer code

    # indirizzo cliente
    c.drawString(60, 610, str(row["NAME"]))
    c.drawString(60, 595, str(row["STRASSE"]))
    c.drawString(60, 580, f"{row['PC']} {row['CITY']}")

    # ==========================
    # TABLE (SAP STYLE)
    # ==========================
    y = 430
    c.setFont("Courier", 8)

    for _, r in data.iterrows():

        # costruzione riga stile PDF
        qty = int(r["quantity_(bundles)"]) if pd.notna(r["quantity_(bundles)"]) else ""
        price = r["price per bundle"] if pd.notna(r["price per bundle"]) else ""

        line = f"{r['SKU']}    {qty:<6}    {price}"

        c.drawString(60, y, line)

        y -= 12

        # ==========================
        # NUOVA PAGINA
        # ==========================
        if y < 60:
            c.showPage()

            c.setFont("Courier", 9)
            c.drawString(300, 760, str(dn))

            c.setFont("Courier", 8)
            y = 430

    c.save()
    buffer.seek(0)

    return buffer


# ======================================
# MERGE TEMPLATE + OVERLAY
# ======================================
def merge_pdf(template_bytes, overlay_bytes):

    template_reader = PdfReader(template_bytes)
    overlay_reader = PdfReader(overlay_bytes)

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


# ======================================
# MAIN
# ======================================
if generate and excel_file is not None and template_file is not None:

    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip()

    # FIX bundles column
    if "quantity_(bundles)" not in df.columns:
        for col in df.columns:
            if "bundles" in col.lower():
                df = df.rename(columns={col: "quantity_(bundles)"})

    # controllo DN
    if "DN" not in df.columns:
        st.error(f"❌ DN non trovato: {list(df.columns)}")
        st.stop()

    grouped = df.groupby("DN")

    for dn, group in grouped:

        st.write(f"Processing DN {dn}")

        overlay_pdf = create_overlay(dn, group)
        final_pdf = merge_pdf(template_file, overlay_pdf)

        st.download_button(
            label=f"📄 Download {dn}",
            data=final_pdf,
            file_name=f"{dn}.pdf"
        )

    st.success("✅ DONE")
``
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas

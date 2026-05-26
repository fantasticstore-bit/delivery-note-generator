import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")
st.title("📦 Delivery Note Generator")

# ==========================
# UPLOAD
# ==========================
orders_file = st.file_uploader("Orders Excel", type=["xlsx"])
tp500_file = st.file_uploader("TP500", type=["xlsx"])
mapping_file = st.file_uploader("Mapping DN → Customer", type=["xlsx"])
sku_file = st.file_uploader("SKU Master", type=["xlsx"])

generate = st.button("🚀 Generate")

# ==========================
# FIND COLUMN
# ==========================
def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

# ==========================
# PDF TEMPLATE PRO
# ==========================
def create_pdf(dn, data):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    data = data.fillna("")
    row = data.iloc[0]

    # ==========================
    # HEADER
    # ==========================
    elements.append(Paragraph("<b>PHILIP MORRIS INTERNATIONAL</b>", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>AFLEVERBON - {dn}</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    # ==========================
    # TOP INFO TABLE
    # ==========================
    info_data = [
        ["AFZENDLOCATIE", "VERVOERDER", "ROUTE"],
        ["Bergen Op Zoom", "Speedlink B.V", dn],
    ]

    info_table = Table(info_data, colWidths=[180, 180, 180])
    info_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "LEFT")
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # ==========================
    # SECOND INFO LINE
    # ==========================
    info2 = [
        ["KLANTCODE", "SOORT BESTELLING", "LEVERDATUM"],
        [row["CustomerID"], "Delivery", ""]
    ]

    table2 = Table(info2, colWidths=[180, 180, 180])
    table2.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))

    elements.append(table2)
    elements.append(Spacer(1, 20))

    # ==========================
    # CUSTOMER BLOCK
    # ==========================
    customer_left = f"""
    <b>{row.get("Descr.", "")}</b><br/>
    {row.get("Adress 2", "")}<br/>
    {row.get("Cp", "")}
    """

    customer_data = [
        ["ONTVANGER VAN GOEDEREN", "ONTVANGER VAN DE AFLEVERINGSBON"],
        [customer_left, customer_left]
    ]

    cust_table = Table(customer_data, colWidths=[270, 270])
    cust_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))

    elements.append(cust_table)
    elements.append(Spacer(1, 20))

    # ==========================
    # TOTAL SECTION
    # ==========================
    totals = [
        ["TOTAAL DOZEN", "0", "BRUTOGEWICHT", "0 KG"]
    ]

    totals_table = Table(totals, colWidths=[135, 135, 135, 135])
    totals_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # ==========================
    # ITEMS TABLE
    # ==========================
    table_data = [["ARTIKEL", "AANTAL", "OMSCHRIJVING"]]

    for _, r in data.iterrows():
        table_data.append([
            r.get("SKU", ""),
            r.get("QTY", ""),
            r.get("DESCRIPTION", "")
        ])

    items_table = Table(table_data, colWidths=[120, 80, 340])

    items_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))

    elements.append(items_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================
# MAIN
# ==========================
if generate and orders_file and tp500_file and mapping_file and sku_file:

    st.info("Processing...")

    df_orders = pd.read_excel(orders_file)
    df_map = pd.read_excel(mapping_file)
    df_tp500 = pd.read_excel(tp500_file)
    df_sku = pd.read_excel(sku_file)

    for df in [df_orders, df_map, df_tp500, df_sku]:
        df.columns = df.columns.str.strip()

    # ORDERS
    if "quantity_(bundles)" in df_orders.columns:
        df_orders = df_orders.rename(columns={"quantity_(bundles)": "QTY"})

    df_orders["DN"] = df_orders["DN"].astype(str)

    # MAPPING
    dn_col = find_column(df_map, ["dn"])
    cust_col = find_column(df_map, ["customer"])

    df_map = df_map.rename(columns={
        dn_col: "DN",
        cust_col: "CustomerID"
    })

    df_map["DN"] = df_map["DN"].astype(str)

    df = df_orders.merge(df_map, on="DN", how="left")

    # TP500
    cust_tp = find_column(df_tp500, ["customer"])
    df_tp500 = df_tp500.rename(columns={cust_tp: "CustomerID"})

    df["CustomerID"] = df["CustomerID"].astype(str).str.zfill(10)
    df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str).str.zfill(10)

    df = df.merge(df_tp500, on="CustomerID", how="left")

    # SKU
    if "SKU" in df_sku.columns:
        df = df.merge(df_sku, on="SKU", how="left")

    df = df.fillna("")

    # GROUP
    grouped = df.groupby("DN")

    for dn, group in grouped:

        pdf = create_pdf(dn, group)

        st.download_button(
            f"📄 Download {dn}",
            data=pdf,
            file_name=f"{dn}.pdf"
        )

    st.success("✅ DONE!")

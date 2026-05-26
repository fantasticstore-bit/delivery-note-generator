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
# FIND COLUMN SAFE
# ==========================
def find_column(df, keys):
    for col in df.columns:
        for k in keys:
            if k.lower() in col.lower():
                return col
    return None

# ==========================
# PDF CREATION (PRO)
# ==========================
def create_pdf(dn, data):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []
    data = data.fillna("")
    row = data.iloc[0]

    # HEADER
    elements.append(Paragraph("<b>PHILIP MORRIS INTERNATIONAL</b>", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>AFLEVERBON - {dn}</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    # BOX 1
    table1 = Table([
        ["AFZENDLOCATIE", "VERVOERDER", "ROUTE"],
        ["Bergen Op Zoom", "Speedlink B.V", dn]
    ], colWidths=[180, 180, 180])

    table1.setStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(table1)
    elements.append(Spacer(1, 10))

    # BOX 2
    table2 = Table([
        ["KLANTCODE", "SOORT BESTELLING", "LEVERDATUM"],
        [row["CustomerID"], "Delivery", ""]
    ], colWidths=[180, 180, 180])

    table2.setStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(table2)
    elements.append(Spacer(1, 15))

    # CUSTOMER BLOCK
    customer = f"{row.get('Descr.', '')}<br/>{row.get('Adress 2','')} {row.get('Cp','')}"

    cust_table = Table([
        ["ONTVANGER VAN GOEDEREN", "ONTVANGER VAN DE AFLEVERINGSBON"],
        [customer, customer]
    ], colWidths=[270, 270])

    cust_table.setStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(cust_table)
    elements.append(Spacer(1, 20))

    # ITEMS
    table_data = [["ARTIKEL", "AANTAL", "OMSCHRIJVING"]]

    for _, r in data.iterrows():
        table_data.append([
            r.get("SKU", ""),
            r.get("QTY", ""),
            r.get("DESCRIPTION", "")
        ])

    items = Table(table_data, colWidths=[120, 80, 340])
    items.setStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ])

    elements.append(items)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==========================
# MAIN LOGIC
# ==========================
if generate and orders_file and tp500_file and mapping_file and sku_file:

    st.info("Processing...")

    # LOAD
    df_orders = pd.read_excel(orders_file)
    df_map = pd.read_excel(mapping_file)
    df_tp500 = pd.read_excel(tp500_file)
    df_sku = pd.read_excel(sku_file)

    # CLEAN COLS
    for df in [df_orders, df_map, df_tp500, df_sku]:
        df.columns = df.columns.str.strip()

    # ==========================
    # ORDERS FIX
    # ==========================
    if "quantity_(bundles)" in df_orders.columns:
        df_orders = df_orders.rename(columns={"quantity_(bundles)": "QTY"})

    if "DN" not in df_orders.columns:
        st.error("❌ DN NON trovata in orders")
        st.stop()

    df_orders["DN"] = df_orders["DN"].astype(str)

    # ==========================
    # MAPPING FIX
    # ==========================
    dn_col = find_column(df_map, ["dn"])
    cust_col = find_column(df_map, ["customer"])

    if dn_col is None or cust_col is None:
        st.error(f"❌ Mapping sbagliato: {list(df_map.columns)}")
        st.stop()

    df_map = df_map.rename(columns={dn_col: "DN", cust_col: "CustomerID"})
    df_map = df_map[["DN", "CustomerID"]]
    df_map["DN"] = df_map["DN"].astype(str)

    # ==========================
    # MERGE 1 (SAFE)
    # ==========================
    df = pd.merge(df_orders, df_map, on="DN", how="left")

    if "DN" not in df.columns:
        st.error("❌ DN perso dopo merge mapping")
        st.stop()

    # ==========================
    # TP500 FIX
    # ==========================
    cust_tp = find_column(df_tp500, ["customer"])
    if cust_tp is None:
        st.error("❌ TP500 sbagliato")
        st.stop()

    df_tp500 = df_tp500.rename(columns={cust_tp: "CustomerID"})

    # FIX FORMATO
    df["CustomerID"] = df["CustomerID"].astype(str).str.strip().str.zfill(10)
    df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str).str.strip().str.zfill(10)

    # ==========================
    # MERGE 2 (SAFE)
    # ==========================
    df = pd.merge(df, df_tp500, on="CustomerID", how="left")

    if "DN" not in df.columns:
        st.error("❌ DN perso dopo merge TP500")
        st.stop()

    # ==========================
    # SKU
    # ==========================
    if "SKU" in df_sku.columns:
        df = pd.merge(df, df_sku, on="SKU", how="left")

    df = df.fillna("")

    # ==========================
    # GROUP
    # ==========================
    if "DN" not in df.columns:
        st.error(f"❌ DN finale mancante: {list(df.columns)}")
        st.stop()

    grouped = df.groupby("DN")

    # ==========================
    # GENERATE
    # ==========================
    for dn, group in grouped:

        st.write(f"Processing {dn}")

        pdf = create_pdf(dn, group)

        st.download_button(
            label=f"📄 Download {dn}",
            data=pdf,
            file_name=f"{dn}.pdf"
        )

    st.success("✅ DONE!")

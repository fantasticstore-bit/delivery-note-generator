import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

st.set_page_config(layout="wide")
st.title("📦 Delivery Note Generator")

# ==========================
# UPLOAD FILES
# ==========================
orders_file = st.file_uploader("Orders Excel", type=["xlsx"])
tp500_file = st.file_uploader("TP500", type=["xlsx"])
mapping_file = st.file_uploader("Mapping DN → Customer", type=["xlsx"])
sku_file = st.file_uploader("SKU Master", type=["xlsx"])

generate = st.button("🚀 Generate")

# ==========================
# FUNZIONE TROVA COLONNE
# ==========================
def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

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

    # CLEAN COLUMN NAMES
    for df in [df_orders, df_map, df_tp500, df_sku]:
        df.columns = df.columns.str.strip()

    # ==========================
    # ORDERS FIX
    # ==========================
    if "quantity_(bundles)" in df_orders.columns:
        df_orders = df_orders.rename(columns={"quantity_(bundles)": "QTY"})

    df_orders = df_orders[df_orders["DN"].notna()]
    df_orders = df_orders[df_orders["SKU"].notna()]

    df_orders["DN"] = df_orders["DN"].astype(str)

    # ==========================
    # MAPPING AUTO DETECT
    # ==========================
    dn_col_map = find_column(df_map, ["dn"])
    cust_col_map = find_column(df_map, ["customer"])

    if dn_col_map is None or cust_col_map is None:
        st.error("❌ Mapping file sbagliato")
        st.stop()

    df_map = df_map.rename(columns={
        dn_col_map: "DN",
        cust_col_map: "CustomerID"
    })

    df_map["DN"] = df_map["DN"].astype(str)

    # ==========================
    # MERGE 1
    # ==========================
    df = df_orders.merge(df_map[["DN", "CustomerID"]], on="DN", how="left")

    if df["CustomerID"].isna().all():
        st.error("❌ Mapping non funziona (CustomerID vuoto)")
        st.stop()

    # ==========================
    # TP500 AUTO DETECT
    # ==========================
    cust_col_tp = find_column(df_tp500, ["customer"])

    if cust_col_tp is None:
        st.error("❌ TP500 non valido")
        st.stop()

    df_tp500 = df_tp500.rename(columns={cust_col_tp: "CustomerID"})
    df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str)

    # ==========================
    # MERGE 2 CUSTOMER
    # ==========================
    df = df.merge(df_tp500, on="CustomerID", how="left")

    # ==========================
    # MERGE 3 SKU
    # ==========================
    if "SKU" in df_sku.columns:
        df = df.merge(df_sku, on="SKU", how="left")

    # ==========================
    # OUTPUT
    # ==========================
    os.makedirs("output", exist_ok=True)

    grouped = df.groupby("DN")
    progress = st.progress(0)

    # ==========================
    # PDF FUNCTION
    # ==========================
    def create_pdf(dn, data):
        c = canvas.Canvas(f"output/{dn}.pdf", pagesize=A4)

        # HEADER
        c.drawString(40, 800, "PHILIP MORRIS")
        c.drawString(40, 780, f"DELIVERY NOTE - {dn}")

        # CUSTOMER
        row = data.iloc[0]
        name = str(row.get("Descr.", ""))
        city = str(row.get("Adress 2", ""))
        cap = str(row.get("Cp", ""))
        cust = str(row.get("CustomerID", ""))

        c.drawString(40, 750, f"Customer: {cust}")
        c.drawString(40, 735, name)
        c.drawString(40, 720, f"{cap} {city}")

        # TABLE
        y = 680
        c.drawString(40, y, "SKU")
        c.drawString(150, y, "Description")
        c.drawString(350, y, "Qty")

        y -= 20

        for _, row in data.iterrows():
            c.drawString(40, y, str(row.get("SKU", "")))
            c.drawString(150, y, str(row.get("DESCRIPTION", ""))[:30])
            c.drawString(350, y, str(row.get("QTY", "")))

            y -= 15

            if y < 50:
                c.showPage()
                y = 800

        c.save()

    # ==========================
    # LOOP
    # ==========================
    total = len(grouped)

    for i, (dn, group) in enumerate(grouped):
        create_pdf(dn, group)
        progress.progress((i + 1) / total)

    st.success("✅ DONE!")

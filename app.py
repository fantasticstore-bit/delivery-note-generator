import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

st.set_page_config(layout="wide")

st.title("📦 Delivery Note Generator")

# ==========================
# UPLOAD
# ==========================
orders_file = st.file_uploader("Orders Excel", type=["xlsx"])
tp500_file = st.file_uploader("TP500 (Customers)", type=["xlsx"])
mapping_file = st.file_uploader("DN → Customer Mapping", type=["xlsx"])
sku_file = st.file_uploader("SKU Master", type=["xlsx"])

generate = st.button("🚀 Generate Delivery Notes")

# ==========================
# START
# ==========================
if generate and orders_file and tp500_file and mapping_file and sku_file:

    st.info("Processing files...")

    # ==========================
    # LOAD
    # ==========================
    df_orders = pd.read_excel(orders_file)
    df_tp500 = pd.read_excel(tp500_file)
    df_map = pd.read_excel(mapping_file)
    df_sku = pd.read_excel(sku_file)

    # ==========================
    # CLEAN COLUMN NAMES
    # ==========================
    df_orders.columns = df_orders.columns.str.strip()
    df_tp500.columns = df_tp500.columns.str.strip()
    df_map.columns = df_map.columns.str.strip()
    df_sku.columns = df_sku.columns.str.strip()

    # ==========================
    # DEBUG
    # ==========================
    st.write("📊 Orders cols:", df_orders.columns)
    st.write("📊 Mapping cols:", df_map.columns)
    st.write("📊 TP500 cols:", df_tp500.columns)

    # ==========================
    # RENAME ORDERS
    # ==========================
    df_orders = df_orders.rename(columns={
        "quantity_(bundles)": "QTY"
    })

    # CLEAN DATA
    df_orders = df_orders[df_orders["SKU"].notna()]
    df_orders = df_orders[df_orders["DN"].notna()]

    # ==========================
    # FIX TYPES (CRITICO)
    # ==========================
    df_orders["DN"] = df_orders["DN"].astype(str)
    df_map["DN"] = df_map["DN"].astype(str)

    # ==========================
    # NORMALIZE MAPPING
    # ==========================
    df_map = df_map.rename(columns={
        "Customer Id": "CustomerID",
        "customerid": "CustomerID",
        "customer_id": "CustomerID"
    })

    # ==========================
    # MERGE 1 (ORDERS + MAP)
    # ==========================
    df = df_orders.merge(df_map, on="DN", how="left")

    st.write("📊 After mapping:", df.columns)

    if "CustomerID" not in df.columns:
        st.error(f"❌ CustomerID non trovato! Colonne: {list(df.columns)}")
        st.stop()

    # ==========================
    # FIX TP500
    # ==========================
    df_tp500 = df_tp500.rename(columns={
        "Customer Id": "CustomerID"
    })

    df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str)

    # ==========================
    # MERGE 2 (CLIENTI)
    # ==========================
    df = df.merge(df_tp500, on="CustomerID", how="left")

    # ==========================
    # MERGE 3 (SKU)
    # ==========================
    df = df.merge(df_sku, on="SKU", how="left")

    # ==========================
    # OUTPUT
    # ==========================
    os.makedirs("output", exist_ok=True)

    grouped = df.groupby("DN")
    progress = st.progress(0)

    # ==========================
    # PDF CREATOR
    # ==========================
    def create_pdf(dn, data):
        file_path = f"output/{dn}.pdf"
        c = canvas.Canvas(file_path, pagesize=A4)

        # HEADER
        c.drawString(40, 800, "PHILIP MORRIS")
        c.drawString(40, 780, f"DELIVERY NOTE - {dn}")

        # CUSTOMER
        customer = str(data.iloc[0].get("Descr.", ""))
        city = str(data.iloc[0].get("Adress 2", ""))
        cap = str(data.iloc[0].get("Cp", ""))
        cust_id = str(data.iloc[0].get("CustomerID", ""))

        c.drawString(40, 750, f"Customer ID: {cust_id}")
        c.drawString(40, 735, customer)
        c.drawString(40, 720, f"{cap} {city}")

        # TABLE HEADER
        y = 680
        c.drawString(40, y, "SKU")
        c.drawString(150, y, "Description")
        c.drawString(350, y, "Qty")
        c.drawString(420, y, "Price")

        y -= 20

        for _, row in data.iterrows():
            desc = str(row.get("DESCRIPTION", ""))[:30]
            price = str(row.get("PRICE", ""))

            c.drawString(40, y, str(row.get("SKU", "")))
            c.drawString(150, y, desc)
            c.drawString(350, y, str(row.get("QTY", "")))
            c.drawString(420, y, price)

            y -= 15

            if y < 50:
                c.showPage()
                y = 800

        c.save()

    # ==========================
    # GENERATE
    # ==========================
    total = len(grouped)

    for i, (dn, group) in enumerate(grouped):
        create_pdf(dn, group)
        progress.progress((i + 1) / total)

    st.success("✅ Delivery Notes Generated!")

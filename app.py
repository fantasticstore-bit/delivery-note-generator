import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os

st.set_page_config(layout="wide")

st.title("📦 Delivery Note Generator")

st.sidebar.header("Input files")

orders_file = st.file_uploader("Orders Excel", type=["xlsx"])
tp500_file = st.file_uploader("TP500 (Customers)", type=["xlsx"])
mapping_file = st.file_uploader("DN → Customer ID Mapping", type=["xlsx"])
sku_file = st.file_uploader("SKU Master", type=["xlsx"])

generate = st.button("🚀 Generate Delivery Notes")

if generate and orders_file and tp500_file and mapping_file and sku_file:

    st.info("Processing...")

    df_orders = pd.read_excel(orders_file)
    df_tp500 = pd.read_excel(tp500_file)
    df_map = pd.read_excel(mapping_file)
    df_sku = pd.read_excel(sku_file)

    df_orders = df_orders.rename(columns={
        "DN": "DN",
        "SKU": "SKU",
        "quantity_(bundles)": "QTY"
    })

    df_orders = df_orders[df_orders["SKU"] != "Total"]
    df_orders = df_orders[df_orders["DN"].notna()]

    # merge dati
    df = df_orders.merge(df_map, on="DN", how="left")
    df = df.merge(df_tp500, left_on="CustomerID", right_on="Customer Id", how="left")
    df = df.merge(df_sku, on="SKU", how="left")

    os.makedirs("output", exist_ok=True)

    grouped = df.groupby("DN")
    progress = st.progress(0)

    def create_pdf(dn, data):
        c = canvas.Canvas(f"output/{dn}.pdf", pagesize=A4)

        # HEADER
        c.drawString(40, 800, "PHILIP MORRIS")
        c.drawString(40, 780, f"AFLEVERBON - {dn}")

        # CUSTOMER
        customer = str(data.iloc[0]["Descr."])
        city = str(data.iloc[0]["Adress 2"])
        cap = str(data.iloc[0]["Cp"])
        cust_id = str(data.iloc[0]["CustomerID"])

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
            c.drawString(40, y, str(row["SKU"]))
            desc = str(row.get("DESCRIPTION", ""))[:30]
            price = str(row.get("PRICE", ""))

            c.drawString(150, y, desc)
            c.drawString(350, y, str(row["QTY"]))
            c.drawString(420, y, price)

            y -= 15

            if y < 50:
                c.showPage()
                y = 800

        c.save()

    for i, (dn, group) in enumerate(grouped):
        create_pdf(dn, group)
        progress.progress((i + 1) / len(grouped))

    st.success("✅ Done!")
``

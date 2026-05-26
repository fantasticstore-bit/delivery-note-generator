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
# START
# ==========================
if generate and orders_file and tp500_file and mapping_file and sku_file:

    st.info("Processing...")

    # LOAD FILES
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


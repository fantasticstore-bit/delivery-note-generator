import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

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
# TROVA COLONNE
# ==========================
def find_column(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None


# ==========================
# PDF CREATOR (IN MEMORY !!!)
# ==========================
def create_pdf(dn, data):

    data = data.fillna("")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # HEADER
    c.drawString(40, 800, "PHILIP MORRIS")
    c.drawString(40, 780, f"DELIVERY NOTE - {dn}")

    row = data.iloc[0]

    customer = str(row.get("Descr.", ""))
    city = str(row.get("Adress 2", ""))
    cap = str(row.get("Cp", ""))
    cust_id = str(row.get("CustomerID", ""))

    c.drawString(40, 750, f"Customer: {cust_id}")
    c.drawString(40, 735, customer)
    c.drawString(40, 720, f"{cap} {city}")

    # TABLE
    y = 680
    c.drawString(40, y, "SKU")
    c.drawString(150, y, "Description")
    c.drawString(350, y, "Qty")

    y -= 20

    # 🔥 LIMITE righe per evitare freeze
    for _, r in data.head(50).iterrows():

        c.drawString(40, y, str(r.get("SKU", "")))
        c.drawString(150, y, str(r.get("DESCRIPTION", ""))[:30])
        c.drawString(350, y, str(r.get("QTY", "")))

        y -= 15

        if y < 50:
            c.showPage()
            y = 800

    c.save()

    buffer.seek(0)
    return buffer


# ==========================
# MAIN
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
    # ORDERS
    # ==========================
    if "quantity_(bundles)" in df_orders.columns:
        df_orders = df_orders.rename(columns={"quantity_(bundles)": "QTY"})

    df_orders = df_orders[df_orders["DN"].notna()]
    df_orders["DN"] = df_orders["DN"].astype(str)

    # ==========================
    # MAPPING
    # ==========================
    dn_col = find_column(df_map, ["dn"])
    cust_col = find_column(df_map, ["customer"])

    df_map = df_map.rename(columns={
        dn_col: "DN",
        cust_col: "CustomerID"
    })

    df_map["DN"] = df_map["DN"].astype(str)

    df = df_orders.merge(df_map, on="DN", how="left")

    # ==========================
    # TP500
    # ==========================
    cust_tp = find_column(df_tp500, ["customer"])

    df_tp500 = df_tp500.rename(columns={cust_tp: "CustomerID"})

    # 💣 FIX CRITICO
    df["CustomerID"] = df["CustomerID"].astype(str).str.strip().str.zfill(10)
    df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str).str.strip().str.zfill(10)

    df = df.merge(df_tp500, on="CustomerID", how="left")

    # ==========================
    # SKU
    # ==========================
    if "SKU" in df_sku.columns:
        df = df.merge(df_sku, on="SKU", how="left")

    df = df.fillna("")

    # ==========================
    # GROUP + GENERATE
    # ==========================
    grouped = df.groupby("DN")
    progress = st.progress(0)

    total = len(grouped)

    st.write(f"Total DN: {total}")

    # 💣 GENERA UNO ALLA VOLTA (NO FREEZE)
    for i, (dn, group) in enumerate(grouped):

        st.write(f"Processing {dn}")

        try:
            pdf_file = create_pdf(dn, group)

            st.download_button(
                label=f"📄 Download {dn}",
                data=pdf_file,
                file_name=f"{dn}.pdf"
            )

        except Exception as e:
            st.error(f"Errore su {dn}: {e}")

        progress.progress((i + 1) / total)

    st.success("✅ DONE!")

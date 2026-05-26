# ==========================
# TROVA COLONNE IN AUTOMATICO
# ==========================

def find_column(df, possible_names):
    for col in df.columns:
        for name in possible_names:
            if name.lower() in col.lower():
                return col
    return None

# trova colonne nel mapping
dn_col_map = find_column(df_map, ["dn"])
cust_col_map = find_column(df_map, ["customer"])

# debug
st.write("Mapping DN column:", dn_col_map)
st.write("Mapping Customer column:", cust_col_map)

if dn_col_map is None or cust_col_map is None:
    st.error("❌ Mapping file NON corretto. Devono esserci colonne tipo DN e CustomerID")
    st.stop()

# rinomina mapping
df_map = df_map.rename(columns={
    dn_col_map: "DN",
    cust_col_map: "CustomerID"
})

# ==========================
# FIX TYPES
# ==========================
df_orders["DN"] = df_orders["DN"].astype(str)
df_map["DN"] = df_map["DN"].astype(str)

# ==========================
# MERGE 1
# ==========================
df = df_orders.merge(df_map[["DN", "CustomerID"]], on="DN", how="left")

st.write("After mapping:", df.columns)

# controllo
if df["CustomerID"].isna().all():
    st.error("❌ Mapping NON funziona: nessun CustomerID trovato")
    st.stop()

# ==========================
# TP500 FIX
# ==========================
cust_col_tp = find_column(df_tp500, ["customer"])

if cust_col_tp is None:
    st.error("❌ TP500 non contiene CustomerID")
    st.stop()

df_tp500 = df_tp500.rename(columns={cust_col_tp: "CustomerID"})
df_tp500["CustomerID"] = df_tp500["CustomerID"].astype(str)

# ==========================
# MERGE 2
# ==========================
df = df.merge(df_tp500, on="CustomerID", how="left")


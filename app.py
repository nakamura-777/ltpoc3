import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="キャッシュ生産性アプリ", layout="wide")

st.sidebar.title("データアップロードと入力")

uploaded_product_master = st.sidebar.file_uploader("製品マスターCSVをアップロード", type="csv")
uploaded_data = st.sidebar.file_uploader("生産出荷データCSVをアップロード", type="csv")

product_master = pd.DataFrame()
if uploaded_product_master:
    try:
        product_master = pd.read_csv(uploaded_product_master, encoding="utf-8")
        st.sidebar.success("製品マスター読み込み成功")
    except Exception as e:
        st.sidebar.error(f"製品マスター読み込みエラー: {e}")

input_data = pd.DataFrame()
if uploaded_data:
    try:
        input_data = pd.read_csv(uploaded_data, encoding="utf-8")
        st.sidebar.success("生産出荷データ読み込み成功")
    except Exception as e:
        st.sidebar.error(f"生産出荷データ読み込みエラー: {e}")

st.sidebar.markdown("---")

with st.expander("📋 手動入力", expanded=False):
    with st.form("manual_input"):
        col1, col2, col3 = st.columns(3)
        with col1:
            product_name = st.text_input("品名")
            sale_price = st.number_input("売上単価", min_value=0.0)
            material_cost = st.number_input("材料費", min_value=0.0)
        with col2:
            outsourcing_cost = st.number_input("外注費", min_value=0.0)
            start_date = st.date_input("生産開始日")
            ship_date = st.date_input("出荷日")
        with col3:
            quantity = st.number_input("出荷数", min_value=1)
        submit = st.form_submit_button("追加")

        if submit:
            days = max((ship_date - start_date).days, 1)
            throughput = sale_price - material_cost - outsourcing_cost
            tplt = throughput / days
            new_row = pd.DataFrame([{
                "品名": product_name,
                "売上単価": sale_price,
                "材料費": material_cost,
                "外注費": outsourcing_cost,
                "生産開始日": start_date,
                "出荷日": ship_date,
                "出荷数": quantity,
                "スループット": throughput,
                "リードタイム": days,
                "TP/LT": tplt
            }])
            input_data = pd.concat([input_data, new_row], ignore_index=True)

if not input_data.empty:
    try:
        input_data["スループット"] = input_data["売上単価"] - input_data["材料費"] - input_data["外注費"]
        input_data["リードタイム"] = (pd.to_datetime(input_data["出荷日"]) - pd.to_datetime(input_data["生産開始日"])).dt.days.clip(lower=1)
        input_data["TP/LT"] = input_data["スループット"] / input_data["リードタイム"]
        input_data["出荷数"] = pd.to_numeric(input_data["出荷数"], errors="coerce")

        st.subheader("📈 グラフ表示")
        fig = px.scatter(input_data, x="TP/LT", y="スループット", color="品名",
                         size="出荷数", hover_data=["品名", "スループット", "TP/LT"])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 集計結果")
        st.dataframe(input_data)

        csv = input_data.to_csv(index=False).encode("utf-8")
        st.download_button("📥 集計結果CSVをダウンロード", data=csv, file_name="キャッシュ生産性_集計結果.csv", mime="text/csv")
    except Exception as e:
        st.error(f"データ処理エラー: {e}")

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import StringIO

st.set_page_config(layout="wide", page_title="キャッシュ生産性アプリ 完全版")

st.sidebar.title("操作メニュー")

# セッション状態の初期化
if "manual_input_data" not in st.session_state:
    st.session_state.manual_input_data = pd.DataFrame()

if "deleted_indices" not in st.session_state:
    st.session_state.deleted_indices = []

# 製品マスターのアップロード
st.sidebar.subheader("製品マスター登録")
product_master_file = st.sidebar.file_uploader("製品マスターCSVをアップロード", key="master")
if product_master_file:
    st.session_state.product_master_df = pd.read_csv(product_master_file)
    st.success("製品マスターを読み込みました。")

# 生産データのアップロード
st.sidebar.subheader("生産データ登録")
uploaded_input = st.sidebar.file_uploader("生産データCSVをアップロード", key="input")

# 手動入力フォーム（折り畳み）
with st.expander("📋 手動入力フォーム", expanded=True):
    with st.form(key="manual_form"):
        if "product_master_df" in st.session_state:
            product_options = st.session_state.product_master_df["品名"].tolist()
        else:
            product_options = []
        selected_product = st.selectbox("品名（既存マスター）", options=[""] + product_options)
        manual_product = st.text_input("品名（新規入力）")
        final_product = manual_product if manual_product else selected_product

        col1, col2, col3 = st.columns(3)
        with col1:
            production_date = st.date_input("生産開始日")
        with col2:
            shipment_date = st.date_input("出荷日")
        with col3:
            quantity = st.number_input("出荷数", min_value=1)

        col4, col5, col6 = st.columns(3)
        with col4:
            sales_price = st.number_input("売上単価", min_value=0.0)
        with col5:
            material_cost = st.number_input("材料費", min_value=0.0)
        with col6:
            subcontract_cost = st.number_input("外注費", min_value=0.0)

        submitted = st.form_submit_button("追加")
        if submitted and final_product:
            new_row = pd.DataFrame([{
                "品名": final_product,
                "生産開始日": production_date,
                "出荷日": shipment_date,
                "出荷数": quantity,
                "売上単価": sales_price,
                "材料費": material_cost,
                "外注費": subcontract_cost
            }])
            st.session_state.manual_input_data = pd.concat([st.session_state.manual_input_data, new_row], ignore_index=True)
            st.success("データを追加しました。")

# 入力データを読み込み・結合
input_df = pd.DataFrame()
if uploaded_input:
    try:
        input_df = pd.read_csv(uploaded_input, encoding="utf-8")
    except Exception:
        input_df = pd.read_csv(uploaded_input, encoding="shift-jis")

if not input_df.empty:
    input_df["データ種別"] = "CSV"
if not st.session_state.manual_input_data.empty:
    manual_df = st.session_state.manual_input_data.copy()
    manual_df["データ種別"] = "手動入力"
    input_df = pd.concat([input_df, manual_df], ignore_index=True)

# データ処理
if not input_df.empty:
    input_df["生産開始日"] = pd.to_datetime(input_df["生産開始日"], errors="coerce")
    input_df["出荷日"] = pd.to_datetime(input_df["出荷日"], errors="coerce")
    input_df["リードタイム"] = (input_df["出荷日"] - input_df["生産開始日"]).dt.days.clip(lower=1)
    input_df["スループット"] = input_df["売上単価"] - input_df["材料費"] - input_df["外注費"]
    input_df["TP/LT"] = input_df["スループット"] / input_df["リードタイム"]

    st.subheader("📊 バブルチャート")
    fig = px.scatter(
        input_df, x="TP/LT", y="スループット", color="品名", size="出荷数",
        hover_data=["品名", "スループット", "TP/LT", "リードタイム", "データ種別"]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 製品別の統計情報")
    summary = input_df.groupby("品名").agg({
        "スループット": ["mean", "max", "min", "std"],
        "TP/LT": ["mean", "max", "min", "std"]
    }).round(2)
    summary.columns = ['_'.join(col) for col in summary.columns]
    st.dataframe(summary)

    st.download_button("📥 結果CSVをダウンロード", input_df.to_csv(index=False).encode("utf-8"), "分析結果.csv", "text/csv")

    st.subheader("🗂️ 登録済みデータ")
    show_df = input_df.copy()
    show_df["生産開始日"] = show_df["生産開始日"].dt.strftime("%Y-%m-%d")
    show_df["出荷日"] = show_df["出荷日"].dt.strftime("%Y-%m-%d")
    st.dataframe(show_df)

    st.subheader("🗑️ 手動データ削除")
    delete_index = st.number_input("削除したい手動データのインデックスを入力（0～）", min_value=0, step=1)
    if st.button("削除"):
        if delete_index < len(st.session_state.manual_input_data):
            st.session_state.manual_input_data.drop(delete_index, inplace=True)
            st.session_state.manual_input_data.reset_index(drop=True, inplace=True)
            st.success(f"{delete_index} 行目を削除しました。")
        else:
            st.warning("指定されたインデックスが存在しません。")
else:
    st.info("CSVまたは手動入力でデータを追加してください。")

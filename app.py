
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="キャッシュ生産性アプリ v17", layout="wide")

st.title("キャッシュ生産性アプリ v17")

# 製品マスターの読み込み
product_master_file = st.file_uploader("製品マスターCSVをアップロード", type="csv", key="master")
if product_master_file:
    try:
        product_master_df = pd.read_csv(product_master_file, encoding="utf-8")
        st.session_state["product_master_df"] = product_master_df
        st.success("製品マスター読み込み成功")
    except Exception as e:
        st.error(f"製品マスターの読み込みに失敗しました: {e}")
else:
    st.info("製品マスターをアップロードしてください。")

# 生産データファイルアップロード
uploaded_file = st.file_uploader("生産出荷データCSVをアップロード", type="csv", key="input")

# 手動入力
st.subheader("🔧 手動入力")

product_names = st.session_state["product_master_df"]["品名"].tolist() if "product_master_df" in st.session_state else []
selected_product = st.selectbox("品名を選択（その他を選ぶと手動入力）", options=["その他"] + product_names)
custom_product = ""
if selected_product == "その他":
    custom_product = st.text_input("品名（手入力）")
final_product_name = custom_product if selected_product == "その他" else selected_product

manual_data = {
    "品名": final_product_name,
    "売上単価": st.number_input("売上単価", min_value=0.0, format="%.2f"),
    "材料費": st.number_input("材料費", min_value=0.0, format="%.2f"),
    "外注費": st.number_input("外注費", min_value=0.0, format="%.2f"),
    "出荷数": st.number_input("出荷数", min_value=0, step=1),
    "生産開始日": st.date_input("生産開始日"),
    "出荷日": st.date_input("出荷日")
}

submit = st.button("このデータを追加")
if submit:
    st.session_state["manual_df"] = pd.DataFrame([manual_data])

# アップロードされたCSVデータ読み込み
input_df = pd.DataFrame()
if uploaded_file:
    try:
        input_df = pd.read_csv(uploaded_file, encoding="utf-8")
        st.success("生産出荷データ読み込み成功")
    except Exception as e:
        st.error(f"生産出荷データの読み込みに失敗しました: {e}")

# 手動データの追加
if "manual_df" in st.session_state:
    input_df = pd.concat([input_df, st.session_state["manual_df"]], ignore_index=True)

if not input_df.empty:
    try:
        input_df["売上単価"] = pd.to_numeric(input_df["売上単価"], errors="coerce")
        input_df["材料費"] = pd.to_numeric(input_df["材料費"], errors="coerce")
        input_df["外注費"] = pd.to_numeric(input_df["外注費"], errors="coerce")
        input_df["出荷数"] = pd.to_numeric(input_df["出荷数"], errors="coerce")

        input_df["スループット"] = input_df["売上単価"] - input_df["材料費"] - input_df["外注費"]

        input_df["生産開始日"] = pd.to_datetime(input_df["生産開始日"])
        input_df["出荷日"] = pd.to_datetime(input_df["出荷日"])
        input_df["リードタイム"] = (input_df["出荷日"] - input_df["生産開始日"]).dt.days
        input_df["リードタイム"] = input_df["リードタイム"].apply(lambda x: max(x, 1))

        input_df["TP/LT"] = input_df["スループット"] / input_df["リードタイム"]

        st.subheader("📊 分析結果（TP/LT）")
        st.dataframe(input_df)

        avg_tp = input_df["スループット"].mean()
        avg_tpl = input_df["TP/LT"].mean()

        st.markdown(f"**平均スループット:** ¥{avg_tp:,.0f}　　**平均TP/LT:** ¥{avg_tpl:,.0f}")
        st.markdown(f"**製品数:** {len(input_df)} 件")

        fig = px.scatter(input_df, x="TP/LT", y="スループット", color="品名",
                         size="出荷数", hover_data=["品名", "スループット", "TP/LT"])
        st.plotly_chart(fig, use_container_width=True)

        csv = input_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 結果CSVをダウンロード", data=csv, file_name="キャッシュ生産性_結果.csv", mime="text/csv")

    except Exception as e:
        st.error(f"データ処理エラー: {e}")

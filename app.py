
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.sidebar.title("キャッシュ生産性アプリ")
menu = st.sidebar.radio("メニュー", ["CSVアップロード", "手動入力", "結果表示"])

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file, encoding="utf-8")
    df["出荷日"] = pd.to_datetime(df["出荷日"], errors='coerce')
    df["生産開始日"] = pd.to_datetime(df["生産開始日"], errors='coerce')
    df["リードタイム"] = (df["出荷日"] - df["生産開始日"]).dt.days.clip(lower=1)
    df["スループット"] = df["売上単価"] - df["材料費"] - df["外注費"]
    df["TP/LT"] = df["スループット"] / df["リードタイム"]
    return df

if menu == "CSVアップロード":
    st.header("📤 CSVアップロード")
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file:
        try:
            df = load_data(uploaded_file)
            st.success("CSVを読み込みました。")
            st.dataframe(df)

            with st.expander("📊 製品別統計データ", expanded=True):
                summary = df.groupby("品名").agg(
                    スループット平均=("スループット", "mean"),
                    スループット最大=("スループット", "max"),
                    スループット最小=("スループット", "min"),
                    スループット標準偏差=("スループット", "std"),
                    TP_LT平均=("TP/LT", "mean"),
                    TP_LT最大=("TP/LT", "max"),
                    TP_LT最小=("TP/LT", "min"),
                    TP_LT標準偏差=("TP/LT", "std"),
                ).reset_index()
                st.dataframe(summary)

            st.header("📈 キャッシュ生産性バブルチャート")
            fig = px.scatter(
                df,
                x="TP/LT",
                y="スループット",
                size="出荷数",
                color="品名",
                hover_data=["品名", "スループット", "TP/LT", "出荷数"],
                title="製品別キャッシュ生産性"
            )
            st.plotly_chart(fig, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("結果CSVをダウンロード", csv, "結果データ.csv", "text/csv")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

elif menu == "手動入力":
    st.header("📝 手動入力（1件）")
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            品名 = st.text_input("品名")
            売上単価 = st.number_input("売上単価", step=1.0)
            材料費 = st.number_input("材料費", step=1.0)
            外注費 = st.number_input("外注費", step=1.0)
        with col2:
            出荷数 = st.number_input("出荷数", step=1)
            生産開始日 = st.date_input("生産開始日")
            出荷日 = st.date_input("出荷日")

        submitted = st.form_submit_button("計算する")
        if submitted:
            リードタイム = max((出荷日 - 生産開始日).days, 1)
            スループット = 売上単価 - 材料費 - 外注費
            TP_LT = スループット / リードタイム

            st.success("計算結果：")
            st.write(f"スループット: {スループット:.2f}")
            st.write(f"TP/LT: {TP_LT:.2f}")

elif menu == "結果表示":
    st.header("📌 アップロードまたは入力データをご利用ください")

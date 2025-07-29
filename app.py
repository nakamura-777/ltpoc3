
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.sidebar.title("キャッシュ生産性アプリ")
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except:
        df = pd.read_csv(uploaded_file, encoding="shift_jis")

    st.subheader("入力データ")
    st.dataframe(df)

    if {"品名", "売上単価", "材料費", "外注費", "出荷数", "生産開始日", "出荷日"}.issubset(df.columns):
        df["スループット"] = df["売上単価"] - df["材料費"] - df["外注費"]
        df["生産開始日"] = pd.to_datetime(df["生産開始日"], errors="coerce")
        df["出荷日"] = pd.to_datetime(df["出荷日"], errors="coerce")
        df["リードタイム"] = (df["出荷日"] - df["生産開始日"]).dt.days.clip(lower=1)
        df["TP/LT"] = df["スループット"] / df["リードタイム"]

        st.subheader("集計統計情報")
        stats = df.groupby("品名")[["スループット", "TP/LT"]].agg(["mean", "max", "min", "std"])
        st.dataframe(stats)

        st.subheader("バブルチャート")
        fig = px.scatter(
            df,
            x="TP/LT",
            y="スループット",
            color="品名",
            size="出荷数",
            hover_data=["品名", "スループット", "TP/LT"]
        )
        st.plotly_chart(fig, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("CSVダウンロード", csv, "集計結果.csv", "text/csv")

    else:
        st.warning("必要な列が含まれていません。")
else:
    st.info("左のサイドバーからCSVファイルをアップロードしてください。")

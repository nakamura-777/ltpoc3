
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("キャッシュ生産性分析アプリ")

# サイドバー
with st.sidebar:
    st.header("操作パネル")
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding="shift-jis")

        # 日付変換
        df["生産開始日"] = pd.to_datetime(df["生産開始日"], errors="coerce")
        df["出荷日"] = pd.to_datetime(df["出荷日"], errors="coerce")
        df["リードタイム"] = (df["出荷日"] - df["生産開始日"]).dt.days.clip(lower=1)

        df["スループット"] = df["売上単価"] - df["材料費"] - df["外注費"]
        df["TP/LT"] = df["スループット"] / df["リードタイム"]

        st.subheader("アップロードデータ")
        st.dataframe(df)

        # 統計情報
        st.subheader("製品別統計情報")
        stats_df = df.groupby("品名")[["スループット", "TP/LT"]].agg(["mean", "max", "min", "std"])
        st.dataframe(stats_df)

        # グラフ
        st.subheader("キャッシュ生産性バブルチャート")
        fig = px.scatter(df, x="TP/LT", y="スループット", color="品名", size="出荷数",
                         hover_data=["品名", "スループット", "TP/LT", "リードタイム"])
        st.plotly_chart(fig, use_container_width=True)

        # ダウンロード
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("結果をCSVでダウンロード", csv, "result.csv", "text/csv")

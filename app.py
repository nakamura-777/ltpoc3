
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("キャッシュ生産性アプリ 完全版")

if "manual_data" not in st.session_state:
    st.session_state.manual_data = pd.DataFrame(columns=["品名", "売上単価", "材料費", "外注費", "出荷数", "生産開始日", "出荷日"])

# サイドバー：メニュー
menu = st.sidebar.radio("メニューを選択", ["データアップロード", "手動入力", "グラフと統計"])

# データアップロード画面
if menu == "データアップロード":
    uploaded_file = st.file_uploader("生産出荷データ CSV をアップロード", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        except:
            df = pd.read_csv(uploaded_file, encoding="shift_jis")

        df["生産開始日"] = pd.to_datetime(df["生産開始日"], errors="coerce")
        df["出荷日"] = pd.to_datetime(df["出荷日"], errors="coerce")
        df["リードタイム"] = (df["出荷日"] - df["生産開始日"]).dt.days.clip(lower=1)
        df["スループット"] = df["売上単価"] - df["材料費"] - df["外注費"]
        df["TP/LT"] = df["スループット"] / df["リードタイム"]

        # 手動入力と結合
        full_df = pd.concat([df, st.session_state.manual_data], ignore_index=True)

        st.session_state["data"] = full_df
        st.success("データを読み込みました。")

# 手動入力画面
elif menu == "手動入力":
    with st.form("manual_form"):
        col1, col2 = st.columns(2)
        with col1:
            品名 = st.text_input("品名")
            売上単価 = st.number_input("売上単価", min_value=0.0)
            材料費 = st.number_input("材料費", min_value=0.0)
            外注費 = st.number_input("外注費", min_value=0.0)
            出荷数 = st.number_input("出荷数", min_value=0)
        with col2:
            生産開始日 = st.date_input("生産開始日")
            出荷日 = st.date_input("出荷日")

        submitted = st.form_submit_button("データを追加")
        if submitted:
            リードタイム = max((出荷日 - 生産開始日).days, 1)
            スループット = 売上単価 - 材料費 - 外注費
            TP_LT = スループット / リードタイム

            new_row = pd.DataFrame([{
                "品名": 品名,
                "売上単価": 売上単価,
                "材料費": 材料費,
                "外注費": 外注費,
                "出荷数": 出荷数,
                "生産開始日": pd.to_datetime(生産開始日),
                "出荷日": pd.to_datetime(出荷日),
                "リードタイム": リードタイム,
                "スループット": スループット,
                "TP/LT": TP_LT
            }])
            st.session_state.manual_data = pd.concat([st.session_state.manual_data, new_row], ignore_index=True)
            st.success("データを追加しました。")

    if not st.session_state.manual_data.empty:
        st.write("現在の手動入力データ")
        st.dataframe(st.session_state.manual_data)

        if st.button("❌ 全て削除"):
            st.session_state.manual_data = pd.DataFrame(columns=st.session_state.manual_data.columns)
            st.success("手動入力データを削除しました。")

# グラフ・統計画面
elif menu == "グラフと統計":
    if "data" in st.session_state:
        df = st.session_state["data"]
        st.subheader("バブルチャート（TP/LT vs スループット）")
        fig = px.scatter(df, x="TP/LT", y="スループット", color="品名",
                         size="出荷数", hover_data=["品名", "スループット", "TP/LT"])
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("品名別統計情報")
        stats = df.groupby("品名")[["スループット", "TP/LT"]].agg(["mean", "max", "min", "std"]).round(2)
        stats.columns = ['_'.join(col) for col in stats.columns]
        st.dataframe(stats)
    else:
        st.warning("データが読み込まれていません。")

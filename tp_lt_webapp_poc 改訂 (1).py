import streamlit as st
import pandas as pd
from datetime import date
import io
import plotly.express as px

st.set_page_config(page_title="キャッシュ生産性計算ツール", layout="centered")
st.title("💰 キャッシュ生産性 (TP / LT) 計算ツール")

# データ保存用セッション
if "records" not in st.session_state:
    st.session_state.records = []

with st.form("product_form"):
    st.subheader("📥 製品データ入力")
    col1, col2 = st.columns(2)

    with col1:
        product_name = st.text_input("製品名", value="")
        purchase_date = st.date_input("材料購入日", value=date.today())
        sales = st.number_input("売上金額（円）", min_value=0, step=1000)

    with col2:
        shipment_date = st.date_input("出荷日", value=date.today())
        material_cost = st.number_input("材料費（円）", min_value=0, step=1000)
        outsourcing_cost = st.number_input("外注費（円）", min_value=0, step=1000)

    submitted = st.form_submit_button("追加")

    if submitted:
        if shipment_date < purchase_date:
            st.error("⚠ 出荷日は材料購入日以降にしてください。")
        elif sales < (material_cost + outsourcing_cost):
            st.error("⚠ 売上金額がコスト合計を下回っています。")
        else:
            lt = (shipment_date - purchase_date).days
            tp = sales - material_cost - outsourcing_cost
            tp_per_lt = tp / lt if lt > 0 else 0

            st.session_state.records.append({
                "製品名": product_name,
                "材料購入日": purchase_date,
                "出荷日": shipment_date,
                "売上": sales,
                "材料費": material_cost,
                "外注費": outsourcing_cost,
                "LT（日数)": lt,
                "TP（スループット）": tp,
                "TP/LT（キャッシュ生産性）": round(tp_per_lt, 2)
            })
            st.success("✅ データが追加されました！")

# 表示
if st.session_state.records:
    st.subheader("📊 登録済データとキャッシュ生産性")
    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 TP/LTの高い製品ランキング")
    sorted_df = df.sort_values("TP/LT（キャッシュ生産性）", ascending=False).reset_index(drop=True)
    st.dataframe(sorted_df)

    # グラフ表示
    st.markdown("### 📊 TP/LT バーグラフ")
    fig = px.bar(sorted_df, x="製品名", y="TP/LT（キャッシュ生産性）", color="TP/LT（キャッシュ生産性）",
                 labels={"TP/LT（キャッシュ生産性）": "キャッシュ生産性 (TP/LT)"}, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # CSVエクスポート
    st.markdown("### 📤 データをCSVでダウンロード")
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(label="CSVをダウンロード", data=csv, file_name="cash_productivity.csv", mime="text/csv")

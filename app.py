import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="究極ご飯ダッシュボード", layout="wide")

st.title("🍽️ 究極のご飯レシピダッシュボード 🍱")

uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("data/recipes.csv")

st.sidebar.header("フィルターオプション")

categories = st.sidebar.multiselect(
    "カテゴリー選択",
    options=df["カテゴリー"].unique(),
    default=list(df["カテゴリー"].unique())
)

cal_min, cal_max = st.sidebar.slider(
    "カロリー範囲 (kcal)",
    int(df["カロリー"].min()), int(df["カロリー"].max()),
    (int(df["カロリー"].min()), int(df["カロリー"].max()))
)

search_query = st.sidebar.text_input("料理名検索")

filtered_df = df[
    (df["カテゴリー"].isin(categories)) &
    (df["カロリー"].between(cal_min, cal_max)) &
    (df["料理名"].str.contains(search_query, case=False, na=False))
]

st.subheader(f"🍛 {len(filtered_df)} 件のレシピが見つかりました！")

# レシピカード表示
for _, row in filtered_df.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(row["画像URL"], width=120)
        with cols[1]:
            st.markdown(f"### {row['料理名']} ({row['カテゴリー']})")
            st.write(f"カロリー: {row['カロリー']} kcal, たんぱく質: {row['たんぱく質']} g, 脂質: {row['脂質']} g, 糖質: {row['糖質']} g")

# トップ3高たんぱく質レシピ
st.subheader("🏆 高たんぱく質ランキング")
top_protein = filtered_df.sort_values(by="たんぱく質", ascending=False).head(3)
st.dataframe(top_protein[["料理名", "たんぱく質"]])

# 栄養素サマリー
st.subheader("📊 栄養素グラフ")

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(filtered_df, x="料理名", y=["たんぱく質", "脂質", "糖質"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    cat_counts = filtered_df["カテゴリー"].value_counts()
    fig2 = px.pie(values=cat_counts, names=cat_counts.index, title="カテゴリー割合")
    st.plotly_chart(fig2, use_container_width=True)

# 健康指標付きコメント
avg_calories = filtered_df["カロリー"].mean()
if avg_calories < 600:
    st.success("このフィルタ結果は低カロリーです！🎉")
elif avg_calories < 750:
    st.info("このフィルタ結果は適正カロリーです！👍")
else:
    st.warning("カロリー高めです！食べすぎ注意⚠️")

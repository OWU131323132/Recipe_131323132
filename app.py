import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="究極ご飯ダッシュボード", layout="wide")

st.title("🍽️ 究極のご飯レシピダッシュボード 🍱")

# CSVアップロード or 既存ファイル読み込み
uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロード（未指定時は100件サンプル）", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("data/recipes_100.csv")  # 今回の100件CSVのパスに置き換えてください

st.sidebar.header("フィルターオプション")

# カテゴリー選択
categories = st.sidebar.multiselect(
    "カテゴリー選択",
    options=df["カテゴリー"].unique(),
    default=list(df["カテゴリー"].unique())
)

# カロリー範囲スライダー
cal_min, cal_max = st.sidebar.slider(
    "カロリー範囲 (kcal)",
    int(df["カロリー"].min()), int(df["カロリー"].max()),
    (int(df["カロリー"].min()), int(df["カロリー"].max()))
)

# 料理名検索テキスト
search_query = st.sidebar.text_input("料理名検索")

# ソート選択
sort_option = st.sidebar.selectbox(
    "並び替え",
    options=[
        "なし",
        "たんぱく質（降順）",
        "カロリー（昇順）",
        "糖質（降順）"
    ]
)

# フィルター適用
filtered_df = df[
    (df["カテゴリー"].isin(categories)) &
    (df["カロリー"].between(cal_min, cal_max)) &
    (df["料理名"].str.contains(search_query, case=False, na=False))
]

# ソート適用
if sort_option == "たんぱく質（降順）":
    filtered_df = filtered_df.sort_values(by="たんぱく質", ascending=False)
elif sort_option == "カロリー（昇順）":
    filtered_df = filtered_df.sort_values(by="カロリー", ascending=True)
elif sort_option == "糖質（降順）":
    filtered_df = filtered_df.sort_values(by="糖質", ascending=False)

st.subheader(f"🍛 {len(filtered_df)} 件のレシピが見つかりました！")

# お気に入り保存用セッションステート
if "favorites" not in st.session_state:
    st.session_state["favorites"] = []

# レシピカード表示（お気に入りボタン付き）
for idx, row in filtered_df.iterrows():
    with st.container():
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.image(row["画像URL"], width=120)
        with cols[1]:
            st.markdown(f"### {row['料理名']} ({row['カテゴリー']})")
            st.write(f"カロリー: {row['カロリー']} kcal  |  たんぱく質: {row['たんぱく質']} g  |  脂質: {row['脂質']} g  |  糖質: {row['糖質']} g")
        with cols[2]:
            if st.button("⭐ お気に入りに追加", key=f"fav_{idx}"):
                if row["料理名"] not in st.session_state["favorites"]:
                    st.session_state["favorites"].append(row["料理名"])
                    st.success(f"「{row['料理名']}」をお気に入りに追加しました！")

# お気に入り一覧表示
if st.session_state["favorites"]:
    st.subheader("💖 お気に入りレシピ")
    for fav in st.session_state["favorites"]:
        st.write(f"- {fav}")

# 栄養素トップ3ランキング
st.subheader("🏆 高たんぱく質トップ3")
top_protein = filtered_df.sort_values(by="たんぱく質", ascending=False).head(3)
st.table(top_protein[["料理名", "たんぱく質"]])

# 栄養素グラフ
st.subheader("📊 栄養素グラフ")

col1, col2 = st.columns(2)

with col1:
    if not filtered_df.empty:
        fig = px.bar(
            filtered_df,
            x="料理名",
            y=["たんぱく質", "脂質", "糖質"],
            barmode="group",
            title="栄養素比較"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("該当データなし")

with col2:
    if not filtered_df.empty:
        cat_counts = filtered_df["カテゴリー"].value_counts()
        fig2 = px.pie(
            values=cat_counts,
            names=cat_counts.index,
            title="カテゴリー割合"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("該当データなし")

# 健康指標コメント
if not filtered_df.empty:
    avg_calories = filtered_df["カロリー"].mean()
    if avg_calories < 600:
        st.success("このフィルター結果は低カロリーです！🎉")
    elif avg_calories < 750:
        st.info("このフィルター結果は適正カロリーです！👍")
    else:
        st.warning("カロリー高めです！食べすぎ注意⚠️")
else:
    st.info("フィルター結果に該当するレシピがありません。条件を変えてみてください。")

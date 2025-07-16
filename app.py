import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("ご飯レシピ ダッシュボード 🍚")

# データ読み込み
df = pd.read_csv("data/recipes.csv")

st.sidebar.header("フィルターオプション")

# カテゴリーフィルター
categories = st.sidebar.multiselect(
    "カテゴリー選択",
    options=df["カテゴリー"].unique(),
    default=df["カテゴリー"].unique()
)

# カロリー範囲フィルター
cal_min, cal_max = st.sidebar.slider(
    "カロリー範囲選択",
    int(df["カロリー"].min()), int(df["カロリー"].max()),
    (int(df["カロリー"].min()), int(df["カロリー"].max()))
)

# フィルター適用
filtered_df = df[
    (df["カテゴリー"].isin(categories)) &
    (df["カロリー"] >= cal_min) &
    (df["カロリー"] <= cal_max)
]

st.subheader(f"フィルター結果：{len(filtered_df)}件のレシピ")

st.dataframe(filtered_df)

# 栄養素平均表示
st.subheader("栄養素の平均値 (フィルタ後)")
mean_values = filtered_df[["カロリー", "たんぱく質", "脂質", "糖質"]].mean()
st.write(mean_values)

# 可視化：栄養素の合計グラフ
st.subheader("栄養素の合計グラフ")

fig, ax = plt.subplots()
mean_values.plot(kind='bar', ax=ax)
ax.set_ylabel("量 (g または kcal)")
st.pyplot(fig)

# 可視化：カテゴリー割合
st.subheader("カテゴリー分布")

category_counts = filtered_df["カテゴリー"].value_counts()
fig2, ax2 = plt.subplots()
ax2.pie(category_counts, labels=category_counts.index, autopct="%1.1f%%")
ax2.axis('equal')
st.pyplot(fig2)

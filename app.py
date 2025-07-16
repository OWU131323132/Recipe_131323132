import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_data():
    # ここは実際のファイルパスに合わせてください
    return pd.read_csv("data/recipes.csv")

def filter_data(df, selected_cats, nutrient_ranges):
    # 栄養素範囲でフィルター
    cond = df["カテゴリー"].isin(selected_cats)
    for nut, (minv, maxv) in nutrient_ranges.items():
        cond &= (df[nut] >= minv) & (df[nut] <= maxv)
    return df[cond]

def show_recipe_cards(df):
    for _, row in df.iterrows():
        with st.expander(row["料理名"]):
            cols = st.columns([1, 2])
            with cols[0]:
                st.image(row["画像URL"], use_container_width=True)  # ←修正箇所
            with cols[1]:
                nutri_text = "\n".join(
                    [f"**{col}**: {row[col]}" for col in df.columns if col not in ["料理名", "カテゴリー", "画像URL"]]
                )
                st.markdown(f"**カテゴリー:** {row['カテゴリー']}")
                st.markdown(nutri_text)

def plot_radar(df, selected_recipes):
    # 選択したレシピの栄養素レーダーチャート比較
    if selected_recipes:
        nutri_cols = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
        fig = go.Figure()
        for recipe in selected_recipes:
            d = df[df["料理名"] == recipe].iloc[0]
            fig.add_trace(go.Scatterpolar(
                r=[d[n] for n in nutri_cols],
                theta=nutri_cols,
                fill='toself',
                name=recipe
            ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("レシピを選択すると栄養素比較グラフを表示します。")

def main():
    st.set_page_config(page_title="栄養素豊富レシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    df = load_data()

    st.sidebar.header("フィルター")
    categories = df["カテゴリー"].unique().tolist()
    selected_cats = st.sidebar.multiselect("カテゴリー選択", categories, default=categories)

    # 栄養素のフィルターUIを動的に作成
    nutrient_cols = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
    nutrient_ranges = {}
    for col in nutrient_cols:
        min_val, max_val = int(df[col].min()), int(df[col].max())
        nutrient_ranges[col] = st.sidebar.slider(f"{col}範囲", min_val, max_val, (min_val, max_val))

    filtered_df = filter_data(df, selected_cats, nutrient_ranges)

    st.subheader(f"検索結果：{len(filtered_df)}件")
    show_recipe_cards(filtered_df)

    st.sidebar.header("ランキング表示")
    ranking_type = st.sidebar.selectbox("ランキング軸選択", ["カロリー低い順", "たんぱく質多い順", "脂質バランス良い順", "ビタミン豊富順"])

    if ranking_type == "カロリー低い順":
        rank_df = df.sort_values("カロリー")
    elif ranking_type == "たんぱく質多い順":
        rank_df = df.sort_values("たんぱく質", ascending=False)
    elif ranking_type == "脂質バランス良い順":
        # 脂質と糖質の合計が少なめ、たんぱく質が多いのを優先例
        rank_df = df.assign(脂糖合計=df["脂質"] + df["糖質"]).sort_values(["脂糖合計", "たんぱく質"])
    else:  # ビタミン豊富順
        rank_df = df.assign(ビタミン合計=df["ビタミンA"] + df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)

    st.subheader(f"{ranking_type} トップ5")
    st.table(rank_df[["料理名", "カテゴリー", "カロリー", "たんぱく質", "脂質", "糖質"]].head(5))

    # 栄養素比較レーダーチャート
    selected_recipes = st.multiselect("比較したいレシピを選択", filtered_df["料理名"].tolist())
    plot_radar(df, selected_recipes)

if __name__ == "__main__":
    main()

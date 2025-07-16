import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_data():
    return pd.read_csv("data/recipes.csv")

def filter_data(df, selected_cats, nutrient_ranges):
    cond = df["カテゴリー"].isin(selected_cats)
    for nut, (minv, maxv) in nutrient_ranges.items():
        cond &= (df[nut] >= minv) & (df[nut] <= maxv)
    return df[cond]

def show_recipe_cards_grid(df, cards_per_row=3, favorites=[], food_log=[]):
    rows = (len(df) + cards_per_row - 1) // cards_per_row
    for row_i in range(rows):
        cols = st.columns(cards_per_row)
        for col_i in range(cards_per_row):
            idx = row_i * cards_per_row + col_i
            if idx >= len(df):
                break
            row = df.iloc[idx]
            with cols[col_i]:
                with st.expander(row["料理名"]):
                    st.image(row["画像URL"], use_container_width=True)

                    st.markdown(f"**カテゴリー:** {row['カテゴリー']}")

                    # 栄養素グラフ表示
                    nutrients = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
                    fig = px.bar(
                        x=nutrients,
                        y=[row[n] for n in nutrients],
                        labels={"x": "栄養素", "y": "量"},
                        title="栄養素グラフ"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # 食事記録ボタン
                    if st.button(f"🍽️ 食べた！ {row['料理名']}", key=f"log_{idx}"):
                        food_log.append(row["料理名"])
                        st.session_state["food_log"] = food_log.copy()
                        st.success("食事記録に追加！")

                    # お気に入りボタン
                    if st.button(f"⭐ お気に入り {row['料理名']}", key=f"fav_{idx}"):
                        favorites.append(row["料理名"])
                        st.session_state["favorites"] = favorites.copy()
                        st.success("お気に入りに追加！")

def plot_radar(df, selected_recipes):
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

def plot_food_log_summary(df, food_log):
    if food_log:
        st.subheader("🍱 今日の食事記録：")
        st.write(food_log)

        log_df = df[df["料理名"].isin(food_log)]
        summary = log_df[["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]].sum()
        st.write("**合計栄養素**", summary)

        fig = px.bar(
            x=summary.index,
            y=summary.values,
            labels={"x": "栄養素", "y": "合計量"},
            title="今日の食事合計栄養素"
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="栄養素豊富レシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    df = load_data()

    if "favorites" not in st.session_state:
        st.session_state["favorites"] = []
    if "food_log" not in st.session_state:
        st.session_state["food_log"] = []

    favorites = st.session_state["favorites"]
    food_log = st.session_state["food_log"]

    st.sidebar.header("フィルター")
    categories = df["カテゴリー"].unique().tolist()
    selected_cats = st.sidebar.multiselect("カテゴリー選択", categories, default=categories)

    nutrient_cols = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
    nutrient_ranges = {}
    for col in nutrient_cols:
        min_val, max_val = int(df[col].min()), int(df[col].max())
        nutrient_ranges[col] = st.sidebar.slider(f"{col}範囲", min_val, max_val, (min_val, max_val))

    filtered_df = filter_data(df, selected_cats, nutrient_ranges)

    st.subheader(f"検索結果：{len(filtered_df)}件")
    show_recipe_cards_grid(filtered_df, favorites=favorites, food_log=food_log)

    st.sidebar.header("ランキング表示")
    ranking_type = st.sidebar.selectbox("ランキング軸選択", ["カロリー低い順", "たんぱく質多い順", "脂質バランス良い順", "ビタミン豊富順"])

    # フィルター後のランキングデータ
    rank_df = filtered_df.copy()

    if ranking_type == "カロリー低い順":
        rank_df = rank_df.sort_values("カロリー")
        highlight_col = "カロリー"
    elif ranking_type == "たんぱく質多い順":
        rank_df = rank_df.sort_values("たんぱく質", ascending=False)
        highlight_col = "たんぱく質"
    elif ranking_type == "脂質バランス良い順":
        rank_df = rank_df.assign(脂糖合計=rank_df["脂質"] + rank_df["糖質"]).sort_values(["脂糖合計", "たんぱく質"])
        highlight_col = "脂質"
    else:
        rank_df = rank_df.assign(ビタミン合計=rank_df["ビタミンA"] + rank_df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)
        highlight_col = "ビタミンA"

    st.subheader(f"{ranking_type} トップ5")

    show_cols = ["料理名", "カテゴリー"] + nutrient_cols
    rank_display_df = rank_df[show_cols].head(5)

    # DataFrameのスタイル適用
    st.dataframe(
        rank_display_df.style.applymap(
            lambda v: "background-color: #e0f7fa;" if v == rank_display_df[highlight_col].max() or v == rank_display_df[highlight_col].min() else "",
            subset=[highlight_col]
        ),
        use_container_width=True
    )

    st.subheader("レーダーチャート")
    selected_recipes = st.multiselect("比較したいレシピを選択", filtered_df["料理名"].tolist())
    plot_radar(df, selected_recipes)

    plot_food_log_summary(df, food_log)

    st.sidebar.header("お気に入り一覧")
    if favorites:
        st.sidebar.write(favorites)
    else:
        st.sidebar.write("お気に入りなし")

    if st.sidebar.button("お気に入り全消し"):
        st.session_state["favorites"] = []
        st.experimental_rerun()

    if st.sidebar.button("食事記録全消し"):
        st.session_state["food_log"] = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()

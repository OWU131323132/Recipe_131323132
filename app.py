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

def show_recipe_cards_grid(df, cards_per_row=3):
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
                    nutrient_cols = [col for col in df.columns if col not in ["料理名", "カテゴリー", "画像URL"]]
                    nutri_data = {col: row[col] for col in nutrient_cols}
                    fig = px.pie(values=list(nutri_data.values()), names=nutrient_cols, title="栄養素割合")
                    st.plotly_chart(fig, use_container_width=True)
                    if st.button(f"この料理を食事記録に追加", key=f"add_{idx}"):
                        if "meal_log" not in st.session_state:
                            st.session_state.meal_log = []
                        st.session_state.meal_log.append(row)
                    if st.button(f"お気に入りに追加", key=f"fav_{idx}"):
                        if "favorites" not in st.session_state:
                            st.session_state.favorites = []
                        st.session_state.favorites.append(row)

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

def show_meal_log():
    if "meal_log" not in st.session_state or len(st.session_state.meal_log) == 0:
        st.info("食事記録はまだありません。")
        return
    st.subheader("一日の食事記録")
    log_df = pd.DataFrame(st.session_state.meal_log)
    st.dataframe(log_df[["料理名", "カテゴリー"] + [col for col in log_df.columns if col not in ["料理名", "カテゴリー", "画像URL"]]], use_container_width=True)
    total_nutrients = log_df.drop(columns=["料理名", "カテゴリー", "画像URL"]).sum()
    fig = px.bar(total_nutrients, x=total_nutrients.index, y=total_nutrients.values, labels={'x':'栄養素', 'y':'合計量'}, title="一日の栄養素合計")
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="栄養素豊富レシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    df = load_data()

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
    show_recipe_cards_grid(filtered_df, cards_per_row=3)

    st.sidebar.header("ランキング表示")
    ranking_type = st.sidebar.selectbox("ランキング軸選択", ["カロリー低い順", "たんぱく質多い順", "脂質バランス良い順", "ビタミン豊富順"])

    if ranking_type == "カロリー低い順":
        rank_df = filtered_df.sort_values("カロリー")
    elif ranking_type == "たんぱく質多い順":
        rank_df = filtered_df.sort_values("たんぱく質", ascending=False)
    elif ranking_type == "脂質バランス良い順":
        rank_df = filtered_df.assign(脂糖合計=filtered_df["脂質"] + filtered_df["糖質"]).sort_values(["脂糖合計", "たんぱく質"])
    else:
        rank_df = filtered_df.assign(ビタミン合計=filtered_df["ビタミンA"] + filtered_df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)

    st.subheader(f"{ranking_type} トップ5")
    highlight_col = "カロリー" if "カロリー" in ranking_type else "たんぱく質" if "たんぱく質" in ranking_type else "脂糖合計" if "脂質" in ranking_type else "ビタミン合計"
    show_cols = ["料理名", "カテゴリー"] + ([highlight_col] if highlight_col in rank_df.columns else []) + nutrient_cols
    st.dataframe(rank_df[show_cols].head(5), use_container_width=True)

    selected_recipes = st.multiselect("比較したいレシピを選択", filtered_df["料理名"].tolist())
    plot_radar(df, selected_recipes)

    st.markdown("---")
    show_meal_log()

    st.markdown("---")
    if "favorites" in st.session_state and st.session_state.favorites:
        st.subheader("お気に入りレシピ")
        fav_df = pd.DataFrame(st.session_state.favorites)
        st.dataframe(fav_df[["料理名", "カテゴリー"] + nutrient_cols], use_container_width=True)

if __name__ == "__main__":
    main()

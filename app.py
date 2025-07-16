import streamlit as st
import pandas as pd
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
                    nutri_text = "\n".join(
                        [f"**{col}**: {row[col]}" for col in df.columns if col not in ["料理名", "カテゴリー", "画像URL"]]
                    )
                    st.markdown(f"**カテゴリー:** {row['カテゴリー']}")
                    st.markdown(nutri_text)

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

def highlight_column(s, target_col):
    return ['background-color: lightgray' if col == target_col else '' for col in s.index]

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

    sort_col = None
    rank_df = filtered_df.copy()
    if ranking_type == "カロリー低い順":
        sort_col = "カロリー"
        rank_df = rank_df.sort_values("カロリー")
    elif ranking_type == "たんぱく質多い順":
        sort_col = "たんぱく質"
        rank_df = rank_df.sort_values("たんぱく質", ascending=False)
    elif ranking_type == "脂質バランス良い順":
        sort_col = "脂糖合計"
        rank_df = rank_df.assign(脂糖合計=rank_df["脂質"] + rank_df["糖質"]).sort_values(["脂糖合計", "たんぱく質"])
    else:  # ビタミン豊富順
        sort_col = "ビタミン合計"
        rank_df = rank_df.assign(ビタミン合計=rank_df["ビタミンA"] + rank_df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)

    st.subheader(f"{ranking_type} トップ5")

    display_cols = ["料理名", "カテゴリー", "カロリー", "たんぱく質", "脂質", "糖質"]
    if sort_col not in display_cols:
        display_cols.append(sort_col)

    styled_df = rank_df[display_cols].head(5).style.apply(highlight_column, axis=1, target_col=sort_col)
    st.dataframe(styled_df, use_container_width=True)

    selected_recipes = st.multiselect("比較したいレシピを選択", filtered_df["料理名"].tolist())
    plot_radar(df, selected_recipes)

if __name__ == "__main__":
    main()

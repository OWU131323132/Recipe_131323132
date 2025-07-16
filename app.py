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
                    if st.button(f"🍽️ 食べた ( {row['料理名']} )", key=row["料理名"]):
                        st.session_state.food_log.append(row["料理名"])

def plot_food_log_summary(df, food_log):
    if not food_log:
        st.info("まだ食事記録がありません。")
        return

    st.subheader("🍱 今日の食事記録グラフ")

    nutrients = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]

    log_df = df[df["料理名"].isin(food_log)]
    stacked_data = {nutrient: [] for nutrient in nutrients}
    labels = []

    for _, row in log_df.iterrows():
        labels.append(row["料理名"])
        for nutrient in nutrients:
            stacked_data[nutrient].append(row[nutrient])

    blue_colors = ["#1f77b4", "#3b8ec2", "#5ca0d3", "#7db1e5", "#9ec3f7", "#bdd6fb"]

    fig = go.Figure()

    for i, recipe in enumerate(labels):
        color = blue_colors[i % len(blue_colors)]
        fig.add_trace(go.Bar(
            name=recipe,
            x=nutrients,
            y=[stacked_data[nutrient][i] for nutrient in nutrients],
            marker_color=color,
        ))

    target_values = {
        "カロリー": 2000,
        "たんぱく質": 60,
        "脂質": 65,
        "糖質": 300,
        "食物繊維": 20,
        "ビタミンA": 800,
        "ビタミンC": 100,
        "鉄分": 10,
        "カルシウム": 650,
    }

    bar_width = 0.8

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color="red", dash="solid"),
        name="一日目安ライン"
    ))

    for i, nutrient in enumerate(nutrients):
        y = target_values[nutrient]
        x0 = i - bar_width / 2
        x1 = i + bar_width / 2
        fig.add_shape(
            type="line",
            x0=x0, x1=x1,
            y0=y, y1=y,
            line=dict(color="red", dash="solid"),
            yref='y',
            xref='x'
        )

    fig.update_layout(
        barmode='stack',
        yaxis_title="摂取量",
        legend_title="凡例",
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="栄養素たっぷりレシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    if "food_log" not in st.session_state:
        st.session_state.food_log = []

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
    show_recipe_cards_grid(filtered_df)

    st.sidebar.header("ランキング表示")
    ranking_type = st.sidebar.selectbox("ランキング軸選択", ["カロリー低い順", "たんぱく質多い順", "脂質少ない順", "ビタミン豊富順"])

    if ranking_type == "カロリー低い順":
        rank_df = filtered_df.sort_values("カロリー")
        show_cols = ["料理名", "カテゴリー", "カロリー", "たんぱく質", "脂質", "ビタミンA"]
    elif ranking_type == "たんぱく質多い順":
        rank_df = filtered_df.sort_values("たんぱく質", ascending=False)
        show_cols = ["料理名", "カテゴリー", "たんぱく質", "カロリー", "脂質", "ビタミンA"]
    elif ranking_type == "脂質少ない順":
        rank_df = filtered_df.sort_values("脂質")
        show_cols = ["料理名", "カテゴリー", "脂質", "カロリー", "たんぱく質", "ビタミンA"]
    else:  # ビタミン豊富順
        rank_df = filtered_df.assign(ビタミン合計=filtered_df["ビタミンA"] + filtered_df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)
        show_cols = ["料理名", "カテゴリー", "ビタミン合計", "カロリー", "たんぱく質", "脂質"]

    st.subheader(f"{ranking_type} トップ5")
    st.dataframe(rank_df[show_cols].head(5), use_container_width=True)

    st.subheader("🍽️ 食事記録")
    plot_food_log_summary(df, st.session_state.food_log)

if __name__ == "__main__":
    main()

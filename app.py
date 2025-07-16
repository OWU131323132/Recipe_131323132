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

def show_recipe_cards_grid(df, cards_per_row=3, food_log=[]):
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

                    nutrients = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維",
                                 "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
                    values = [row[n] for n in nutrients]
                    fig = go.Figure(data=[go.Bar(x=nutrients, y=values)])
                    fig.update_layout(title="栄養素グラフ", yaxis_title="量")
                    st.plotly_chart(fig, use_container_width=True)

                    if st.button(f"🍽️ 食べた！ {row['料理名']}", key=f"log_{idx}"):
                        food_log.append(row["料理名"])
                        st.session_state["food_log"] = food_log.copy()
                        st.experimental_rerun()

def plot_food_log_summary(df, food_log):
    if not food_log:
        st.info("まだ食事記録がありません。")
        return
    
    st.subheader("🍱 今日の食事記録グラフ")

    nutrients = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維",
                 "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]

    log_df = df[df["料理名"].isin(food_log)]
    stacked_data = {nutrient: [] for nutrient in nutrients}
    labels = []

    for _, row in log_df.iterrows():
        labels.append(row["料理名"])
        for nutrient in nutrients:
            stacked_data[nutrient].append(row[nutrient])

    fig = go.Figure()
    for i, recipe in enumerate(labels):
        fig.add_trace(go.Bar(
            name=recipe,
            x=nutrients,
            y=[stacked_data[nutrient][i] for nutrient in nutrients]
        ))

    # 横方向の目安摂取量ライン
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

    for nutrient in nutrients:
        fig.add_shape(
            type="line",
            x0=-0.5, x1=len(nutrients)-0.5,
            y0=target_values[nutrient], y1=target_values[nutrient],
            line=dict(color="red", dash="dash"),
            yref='y',
            xref='x'
        )

    fig.update_layout(
        barmode='stack',
        title="積み上げ栄養素グラフ + 目安摂取量ライン",
        yaxis_title="摂取量",
        legend_title="食べた料理"
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="栄養素レシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    df = load_data()

    if "food_log" not in st.session_state:
        st.session_state["food_log"] = []
    food_log = st.session_state["food_log"]

    st.sidebar.header("フィルター")
    categories = df["カテゴリー"].unique().tolist()
    selected_cats = st.sidebar.multiselect("カテゴリー選択", categories, default=categories)

    nutrient_cols = ["カロリー", "たんぱく質", "脂質", "糖質",
                     "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
    nutrient_ranges = {}
    for col in nutrient_cols:
        min_val, max_val = int(df[col].min()), int(df[col].max())
        nutrient_ranges[col] = st.sidebar.slider(f"{col} 範囲", min_val, max_val, (min_val, max_val))

    filtered_df = filter_data(df, selected_cats, nutrient_ranges)

    st.subheader(f"検索結果：{len(filtered_df)}件")
    show_recipe_cards_grid(filtered_df, food_log=food_log)

    st.subheader("食事記録まとめ")
    plot_food_log_summary(df, food_log)

    if st.sidebar.button("食事記録クリア"):
        st.session_state["food_log"] = []
        st.toast("食事記録をクリアしました！")
        st.experimental_rerun()

if __name__ == "__main__":
    main()

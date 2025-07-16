import streamlit as st
import pandas as pd
import plotly.graph_objects as go

@st.cache_data
def load_data():
    # 実際のファイルパスに合わせてください
    return pd.read_csv("data/recipes.csv")

def filter_data(df, selected_cats, nutrient_ranges):
    cond = df["カテゴリー"].isin(selected_cats)
    for nut, (minv, maxv) in nutrient_ranges.items():
        cond &= (df[nut] >= minv) & (df[nut] <= maxv)
    return df[cond]

def show_recipe_cards_grid(df, food_log=None, cards_per_row=3):
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
                    if food_log is not None:
                        if st.button(f"食べた！ ({row['料理名']})", key=f"eat_{idx}"):
                            # 食べたボタンが押されたらセッションステートにセット
                            st.session_state["add_food"] = True
                            st.session_state["add_food_name"] = row["料理名"]

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

def plot_food_log_graph(df, food_log):
    if not food_log:
        st.info("食事記録はまだありません。")
        return

    # 集計
    log_df = df[df["料理名"].isin(food_log)]
    nutri_cols = ["カロリー", "たんぱく質", "脂質", "糖質", "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]

    # 積み上げ用データを作成
    stack_data = pd.DataFrame(0, index=nutri_cols, columns=food_log)
    for food in food_log:
        d = log_df[log_df["料理名"] == food].iloc[0]
        for nut in nutri_cols:
            stack_data.at[nut, food] += d[nut]

    # 1日の目安摂取量（例として設定）
    daily_targets = {
        "カロリー": 2000,
        "たんぱく質": 50,
        "脂質": 60,
        "糖質": 300,
        "食物繊維": 20,
        "ビタミンA": 900,
        "ビタミンC": 100,
        "鉄分": 15,
        "カルシウム": 650,
    }

    fig = go.Figure()

    # 積み上げ棒グラフ
    for food in food_log:
        fig.add_trace(go.Bar(
            name=food,
            y=nutri_cols,
            x=stack_data[food],
            orientation='h',
            hovertemplate='%{y}: %{x}<extra>'+food+'</extra>'
        ))

    # 目安摂取量ライン（横線）
    for nut in nutri_cols:
        fig.add_shape(
            type="line",
            x0=daily_targets[nut], y0=nut,
            x1=daily_targets[nut], y1=nut,
            xref='x', yref='y',
            line=dict(color='red', width=2, dash='dash'),
        )

    fig.update_layout(
        barmode='stack',
        title='食事記録の栄養素積み上げと1日の目安摂取量（赤線）',
        xaxis_title='栄養素量',
        yaxis_title='栄養素',
        yaxis=dict(autorange="reversed"),
        legend_title_text='食べた料理',
        height=600,
        margin=dict(l=120, r=20, t=50, b=50)
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.set_page_config(page_title="栄養素豊富レシピダッシュボード", layout="wide")
    st.title("🥗 栄養素たっぷりレシピダッシュボード")

    df = load_data()

    # セッションステート初期化
    if "food_log" not in st.session_state:
        st.session_state["food_log"] = []
    if "add_food" not in st.session_state:
        st.session_state["add_food"] = False
    if "add_food_name" not in st.session_state:
        st.session_state["add_food_name"] = None
    if "clear_log" not in st.session_state:
        st.session_state["clear_log"] = False
    if "clear_message" not in st.session_state:
        st.session_state["clear_message"] = False

    # 食べた追加処理
    if st.session_state["add_food"]:
        food_name = st.session_state["add_food_name"]
        if food_name is not None:
            st.session_state["food_log"].append(food_name)
        st.session_state["add_food"] = False
        st.session_state["add_food_name"] = None
        st.experimental_rerun()

    # 食事記録クリア処理
    if st.session_state["clear_log"]:
        st.session_state["food_log"] = []
        st.session_state["clear_log"] = False
        st.session_state["clear_message"] = True
        st.experimental_rerun()

    # フィルターUI
    st.sidebar.header("フィルター")
    categories = df["カテゴリー"].unique().tolist()
    selected_cats = st.sidebar.multiselect("カテゴリー選択", categories, default=categories)

    nutrient_cols = ["カロリー", "たんぱく質", "脂質", "糖質",
                     "食物繊維", "ビタミンA", "ビタミンC", "鉄分", "カルシウム"]
    nutrient_ranges = {}
    for col in nutrient_cols:
        min_val, max_val = int(df[col].min()), int(df[col].max())
        nutrient_ranges[col] = st.sidebar.slider(f"{col}範囲", min_val, max_val, (min_val, max_val))

    filtered_df = filter_data(df, selected_cats, nutrient_ranges)

    st.subheader(f"検索結果：{len(filtered_df)}件")
    show_recipe_cards_grid(filtered_df, food_log=st.session_state["food_log"], cards_per_row=3)

    # ランキング表示
    st.sidebar.header("ランキング表示")
    ranking_type = st.sidebar.selectbox("ランキング軸選択", ["カロリー低い順", "たんぱく質多い順", "脂質バランス良い順", "ビタミン豊富順"])

    # フィルター済みデータのみでランキング計算
    if ranking_type == "カロリー低い順":
        rank_df = filtered_df.sort_values("カロリー")
        rank_col = "カロリー"
    elif ranking_type == "たんぱく質多い順":
        rank_df = filtered_df.sort_values("たんぱく質", ascending=False)
        rank_col = "たんぱく質"
    elif ranking_type == "脂質バランス良い順":
        rank_df = filtered_df.assign(脂糖合計=filtered_df["脂質"] + filtered_df["糖質"]).sort_values(["脂糖合計", "たんぱく質"])
        rank_col = "脂糖合計"
    else:  # ビタミン豊富順
        rank_df = filtered_df.assign(ビタミン合計=filtered_df["ビタミンA"] + filtered_df["ビタミンC"]).sort_values("ビタミン合計", ascending=False)
        rank_col = "ビタミン合計"

    st.subheader(f"{ranking_type} トップ5")

    # 色付きヘッダー用のDataFrame作成
    display_cols = ["料理名", "カテゴリー", "カロリー", "たんぱく質", "脂質", "糖質"]
    rank_display_df = rank_df[display_cols].head(5).copy()

    # pandasのstyleでハイライト
    def highlight_rank_col(col):
        if col.name == rank_col:
            return ['background-color: #cce5ff'] * len(col)
        return [''] * len(col)

    st.dataframe(rank_display_df.style.apply(highlight_rank_col, axis=0), use_container_width=True)

    # 食事記録グラフとクリアボタン
    st.subheader("🍽️ 食事記録（栄養素積み上げグラフ）")
    plot_food_log_graph(df, st.session_state["food_log"])

    if st.button("食事記録クリア"):
        st.session_state["clear_log"] = True
        st.experimental_rerun()

    # 食事記録クリアメッセージを数秒だけ表示
    if st.session_state.get("clear_message", False):
        st.success("食事記録をクリアしました！")
        # 3秒後に消すために簡単に実装（ボタン押し直しで消える）
        # より良くするならst_autorefreshなど検討
        st.session_state["clear_message"] = False

    # 栄養素比較レーダーチャート
    selected_recipes = st.multiselect("比較したいレシピを選択", filtered_df["料理名"].tolist())
    plot_radar(df, selected_recipes)

if __name__ == "__main__":
    main()

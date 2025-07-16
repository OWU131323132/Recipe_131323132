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

    # 青系グラデーションの色を用意
    blue_colors = [
        "#1f77b4",  # 青
        "#3b8ec2",
        "#5ca0d3",
        "#7db1e5",
        "#9ec3f7",
        "#bdd6fb",
        "#dbe9fd",
        "#eaf5fe",
        "#f5fbff"
    ]

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

    # 目安ラインの凡例用に1本だけ透明バーで作成（表示しないけど凡例は表示）
    fig.add_trace(go.Bar(
        x=[nutrients[0]],
        y=[target_values[nutrients[0]]],
        name="一日目安ライン",
        marker_color="red",
        opacity=0,
        showlegend=True,
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
        title="積み上げ栄養素グラフ + 目安摂取量ライン",
        yaxis_title="摂取量",
        legend_title="食べた料理",
        margin=dict(r=100)
    )

    st.plotly_chart(fig, use_container_width=True)

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from model import (
    calc_user_score,
    difficulty_label,
    simulate_population,
    get_pass_probability
)

# =====================================
# page
# =====================================

st.set_page_config(
    page_title="横浜保活診断",
    layout="wide"
)

# =====================================
# Google Analytics
# =====================================

st.components.v1.html(
    """
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-R5KBMRYVBE"></script>

    <script>
      window.dataLayer = window.dataLayer || [];

      function gtag(){
        dataLayer.push(arguments);
      }

      gtag('js', new Date());

      gtag('config', 'G-R5KBMRYVBE');
    </script>
    """,
    height=0
)

# =====================================
# title
# =====================================

st.markdown("## 👶 横浜保活診断")

st.caption("横浜市公開データをもとに保育園難易度を分析")

st.info("👈 左上の「>」を押すと条件入力できます")

# =====================================
# load
# =====================================

ward_df = pd.read_csv("data/ward_difficulty.csv")
nursery_df = pd.read_csv("data/nursery_difficulty.csv")
monthly_df = pd.read_csv("data/nursery_monthly.csv")

# =====================================
# sidebar
# =====================================

st.sidebar.header("診断条件")

ward = st.sidebar.selectbox(
    "区",
    sorted(ward_df["区"].dropna().unique())
)

age = st.sidebar.selectbox(
    "年齢",
    ["0歳", "1歳", "2歳", "3歳", "4歳", "5歳"]
)

search_text = st.sidebar.text_input(
    "保育園名で検索",
    placeholder="例: スターチャイルド"
)

# =====================================
# nursery filter
# =====================================

filtered_df = nursery_df[
    (nursery_df["区"] == ward)
    &
    (nursery_df["年齢"] == age)
].copy()

if search_text:

    filtered_df = filtered_df[
        filtered_df["園名"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

nursery_options = ["指定なし"] + sorted(
    filtered_df["園名"].dropna().unique().tolist()
)

nursery = st.sidebar.selectbox(
    "保育園",
    nursery_options
)

# =====================================
# work
# =====================================

work_status = st.sidebar.selectbox(
    "就労状況",
    [
        "既に就労中",
        "育休復職予定",
        "出産・育児",
        "介護・看護",
        "就学",
        "求職中"
    ]
)

employment_type = st.sidebar.selectbox(
    "月間就労時間",
    [
        "月160時間以上",
        "月140〜160時間",
        "月120〜140時間",
        "月100〜120時間",
        "月64〜100時間",
        "月64時間未満"
    ]
)

income = st.sidebar.selectbox(
    "世帯年収",
    [
        "〜400万",
        "400〜600万",
        "600〜800万",
        "800〜1000万",
        "1000万〜"
    ]
)

# =====================================
# options
# =====================================

has_sibling = st.sidebar.checkbox("兄弟姉妹が在園中")
single_parent = st.sidebar.checkbox("ひとり親")

with st.sidebar.expander("詳細条件（同点調整）"):

    ninkaigai = st.checkbox("認可外保育利用")
    nursery_worker = st.checkbox("保育士")
    grandparent_near = st.checkbox("祖父母が近居")
    saturday_work = st.checkbox("土曜勤務あり")
    night_shift = st.checkbox("夜勤あり")
    six_day_work = st.checkbox("週6勤務")
    self_employed = st.checkbox("自営業")

# =====================================
# score
# =====================================

user_score = calc_user_score(
    work_status,
    employment_type,
    has_sibling,
    single_parent,
    ninkaigai,
    nursery_worker,
    grandparent_near,
    saturday_work,
    night_shift,
    six_day_work,
    self_employed
)

ward_row = ward_df[
    ward_df["区"] == ward
].iloc[0]

ward_score = float(
    ward_row["難易度スコア"]
)

# =====================================
# nursery
# =====================================

nursery_score = ward_score
accepted = 100
waiting = 100
pass_ratio_actual = 0.5

if nursery != "指定なし":

    nursery_row = nursery_df[
        (nursery_df["園名"] == nursery)
        &
        (nursery_df["年齢"] == age)
    ]

    if len(nursery_row) > 0:

        nursery_row = nursery_row.iloc[0]

        nursery_score = float(
            nursery_row["難易度スコア"]
        )

        accepted = float(
            nursery_row["受入可能数"]
        )

        waiting = float(
            nursery_row["待機人数"]
        )

        pass_ratio_actual = float(
            nursery_row["通過率"]
        )

# =====================================
# simulation
# =====================================

scores = simulate_population(age, ward)

threshold, pass_prob, pass_ratio = (
    get_pass_probability(
        scores,
        user_score,
        accepted,
        waiting,
        income
    )
)

# =====================================
# hensachi
# =====================================

score_mean = np.mean(scores)
score_std = np.std(scores)

hensachi_scores = (
    (scores - score_mean)
    / score_std
) * 10 + 50

user_hensachi = (
    (user_score - score_mean)
    / score_std
) * 10 + 50

threshold_hensachi = (
    (threshold - score_mean)
    / score_std
) * 10 + 50

# =====================================
# current target
# =====================================

target_text = f"📍 {ward} / {age}"

if nursery != "指定なし":
    target_text += f"　🏫 {nursery}"

st.info(target_text)

# =====================================
# result
# =====================================

st.markdown("### 📊 診断結果")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "あなたの偏差値",
        f"{user_hensachi:.1f}"
    )

with c2:
    st.metric(
        "推定必要偏差値",
        f"{threshold_hensachi:.1f}"
    )

with c3:
    st.metric(
        "推定通過確率",
        f"{pass_prob*100:.1f}%"
    )

# =====================================
# labels
# =====================================

st.subheader(
    difficulty_label(nursery_score)
)

st.write(f"区平均難易度: {ward_score:.2f}")

if nursery != "指定なし":

    st.write(f"園難易度: {nursery_score:.2f}")
    st.write(f"実データ通過率: {pass_ratio_actual:.1%}")

# =====================================
# histogram
# =====================================

st.subheader("📉 スコア分布")

st.caption(
    "※ 偏差値50が横浜保活の平均的な目安です"
)

hist_df = pd.DataFrame({
    "偏差値": hensachi_scores
})

fig = px.histogram(
    hist_df,
    x="偏差値",
    nbins=25,
    height=350
)

fig.add_vline(
    x=user_hensachi,
    line_color="red",
    annotation_text="あなた"
)

fig.add_vline(
    x=threshold_hensachi,
    line_color="green",
    annotation_text="必要ライン"
)

fig.update_layout(
    xaxis_title="偏差値",
    yaxis_title="人数",
    margin=dict(l=10, r=10, t=10, b=10)
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "staticPlot": True
    }
)

# =====================================
# monthly
# =====================================

with st.expander("📈 月次推移を見る"):

    st.caption(
        "※ スマホでは横スクロールできます"
    )

    if nursery != "指定なし":

        monthly_plot = monthly_df[
            (monthly_df["園名"] == nursery)
            &
            (monthly_df["年齢"] == age)
        ].copy()

        if len(monthly_plot) > 0:

            if "月" in monthly_plot.columns:

                monthly_plot = monthly_plot.sort_values("月")

                target_cols = []

                for c in [
                    "待機人数",
                    "受入可能数",
                    "入所児童数"
                ]:
                    if c in monthly_plot.columns:
                        target_cols.append(c)

                if len(target_cols) > 0:

                    plot_df = monthly_plot.melt(
                        id_vars=["月"],
                        value_vars=target_cols,
                        var_name="指標",
                        value_name="人数"
                    )

                    trend_fig = px.line(
                        plot_df,
                        x="月",
                        y="人数",
                        color="指標",
                        markers=True,
                        height=400
                    )

                    trend_fig.update_layout(
                        margin=dict(
                            l=10,
                            r=10,
                            t=10,
                            b=10
                        )
                    )

                    st.plotly_chart(
                        trend_fig,
                        use_container_width=True,
                        config={
                            "displayModeBar": False,
                            "scrollZoom": True
                        }
                    )

# =====================================
# vacancy
# =====================================

st.subheader("🟡 最新データで空き枠がある園")

vacancy_df = nursery_df[
    (nursery_df["区"] == ward)
    &
    (nursery_df["年齢"] == age)
    &
    (nursery_df["受入可能数"] > 0)
].copy()

vacancy_df = vacancy_df.sort_values(
    "受入可能数",
    ascending=False
)

if len(vacancy_df) > 0:

    st.dataframe(

        vacancy_df[[
            "園名",
            "受入可能数",
            "待機人数",
            "通過率"
        ]],

        use_container_width=True

    )

# =====================================
# easy
# =====================================

st.subheader("🟢 比較的入りやすい園")

recommend_df = nursery_df[
    (nursery_df["区"] == ward)
    &
    (nursery_df["年齢"] == age)
].copy()

recommend_df = recommend_df.sort_values(
    ["難易度スコア", "通過率"],
    ascending=[True, False]
)

recommend_df = recommend_df[[
    "園名",
    "難易度スコア",
    "通過率",
    "待機人数",
    "受入可能数"
]].head(10)

st.dataframe(
    recommend_df,
    use_container_width=True
)


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
    self_employed,
    income
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

st.markdown(f"""
<div style="
display:flex;
gap:8px;
margin-bottom:12px;
">

<div style="
flex:1;
background:#0f172a;
padding:8px 4px;
border-radius:10px;
text-align:center;
">
<div style="
font-size:20px;
font-weight:700;
color:white;
line-height:1.1;
">
{user_hensachi:.1f}
</div>
<div style="
font-size:11px;
color:#94a3b8;
margin-top:2px;
">
あなたの偏差値
</div>
</div>

<div style="
flex:1;
background:#0f172a;
padding:8px 4px;
border-radius:10px;
text-align:center;
">
<div style="
font-size:20px;
font-weight:700;
color:white;
line-height:1.1;
">
{threshold_hensachi:.1f}
</div>
<div style="
font-size:11px;
color:#94a3b8;
margin-top:2px;
">
推定必要偏差値
</div>
</div>

<div style="
flex:1;
background:#0f172a;
padding:8px 4px;
border-radius:10px;
text-align:center;
">
<div style="
font-size:20px;
font-weight:700;
color:white;
line-height:1.1;
">
{pass_prob*100:.0f}%
</div>
<div style="
font-size:11px;
color:#94a3b8;
margin-top:2px;
">
推定通過率
</div>
</div>

</div>
""", unsafe_allow_html=True)

# =====================================
# admission timing
# =====================================

timing_rates = {}

if nursery != "指定なし":

    timing_df = monthly_df[
        (monthly_df["園名"] == nursery)
        &
        (monthly_df["年齢"] == age)
    ].copy()

    if len(timing_df) > 0:

        def get_month(v):

            try:
                return int(str(v).split(".")[1])
            except:
                return None

        timing_df["_month"] = (
            timing_df["月"].apply(get_month)
        )

        timing_map = {
            "🌸4月": [4],
            "🌱5-6月": [5, 6],
            "☀️7-9月": [7, 8, 9],
            "🍂10-12月": [10, 11, 12],
            "❄️1-3月": [1, 2, 3],
        }

        for label, months in timing_map.items():

            tmp = timing_df[
                timing_df["_month"].isin(months)
            ]

            if len(tmp) == 0:
                continue

            accepted_sum = (
                tmp["受入可能数"]
                .fillna(0)
                .sum()
            )

            waiting_sum = (
                tmp["待機人数"]
                .fillna(0)
                .sum()
            )

            season_base_rate = accepted_sum / max(
                accepted_sum + waiting_sum,
                1
            )

            timing_rates[label] = season_base_rate

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



if len(timing_rates) > 0:

    st.markdown("### 🗓 入園時期別の募集傾向")

    def rate_label(rate):

        if rate >= 0.6:
            return "🟢 募集が多い"

        elif rate >= 0.3:
            return "🟡 やや多い"

        elif rate >= 0.15:
            return "🟠 普通"

        elif rate >= 0.05:
            return "🔴 少ない"

        else:
            return "⚫ ほぼなし"

    items = list(timing_rates.items())

    for i in range(0, len(items), 2):

        cols = st.columns(2)

        for j in range(2):

            if i + j >= len(items):
                continue

            label, rate = items[i + j]

            with cols[j]:

                st.markdown(
                    f"""
<div style="
background:#0f172a;
padding:12px;
border-radius:10px;
text-align:center;
margin-bottom:10px;
">
<div style="
font-size:16px;
font-weight:700;
color:white;
margin-bottom:6px;
">
{label}
</div>

<div style="
font-size:14px;
color:#cbd5e1;
margin-bottom:6px;
">
{rate_label(rate)}
</div>

<div style="
font-size:22px;
font-weight:700;
color:white;
">
{rate:.0%}
</div>
</div>
""",
                    unsafe_allow_html=True
                )

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

        period = st.selectbox(
            "表示期間",
            [
                "直近12ヶ月",
                "令和8年度",
                "令和7年度",
                "令和6年度",
                "全期間"
            ],
            key="period_select"
        )

        def parse_reiwa_month(x):

            x = str(x)

            parts = x.split(".")

            try:
                year = int(parts[0].replace("R", ""))

                month = int(parts[1])

                return year, month

            except:
                return None, None

        ym = monthly_plot["月"].apply(parse_reiwa_month)

        monthly_plot["_year"] = ym.apply(lambda x: x[0])
        monthly_plot["_month"] = ym.apply(lambda x: x[1])

        if period == "直近12ヶ月":
            monthly_plot = monthly_plot.sort_values(
                ["_year", "_month"]
            ).tail(12)

        elif period == "令和8年度":

            monthly_plot = monthly_plot[
                (
                    (monthly_plot["_year"] == 8)
                    &
                    (monthly_plot["_month"] >= 4)
                )
                |
                (
                    (monthly_plot["_year"] == 9)
                    &
                    (monthly_plot["_month"] <= 3)
                )
            ]

        elif period == "令和7年度":

            monthly_plot = monthly_plot[
                (
                    (monthly_plot["_year"] == 7)
                    &
                    (monthly_plot["_month"] >= 4)
                )
                |
                (
                    (monthly_plot["_year"] == 8)
                    &
                    (monthly_plot["_month"] <= 3)
                )
            ]

        elif period == "令和6年度":

            monthly_plot = monthly_plot[
                (
                    (monthly_plot["_year"] == 6)
                    &
                    (monthly_plot["_month"] >= 4)
                )
                |
                (
                    (monthly_plot["_year"] == 7)
                    &
                    (monthly_plot["_month"] <= 3)
                )
            ]

        monthly_plot = monthly_plot.sort_values(
            ["_year", "_month"]
        )

        if len(monthly_plot) > 0:

            if "月" in monthly_plot.columns:



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
                        height=400,
                        color_discrete_map={
                            "待機人数": "#1f77b4",
                            "受入可能数": "#6ec1ff",
                            "入所児童数": "#ff4b4b"
                        },
                    )

                    tick_vals = monthly_plot["月"][::3]

                    trend_fig.update_layout(
                        
                        height=320,
                        margin=dict(
                            l=10,
                            r=10,
                            t=10,
                            b=120
                        ),
                        legend=dict(
                            orientation="v",
                            yanchor="top",
                            y=-0.35,
                            xanchor="center",
                            x=0.5,
                            font=dict(size=10)
                        ),
                        xaxis=dict(
                            tickmode="array",
                            tickvals=tick_vals
                        )
                    )

                    st.plotly_chart(
                        trend_fig,
                        use_container_width=True,
                        config={
                            "displayModeBar": False,
                            "staticPlot": True
                        }
                    )


# =====================================
# vacancy
# =====================================

st.subheader("🟡 直近で募集実績がある園")

vacancy_rows = []

target_monthly = monthly_df[
    (monthly_df["年齢"] == age)
].copy()

for nursery_name in sorted(
    target_monthly["園名"].dropna().unique()
):

    tmp = target_monthly[
        target_monthly["園名"] == nursery_name
    ].copy()

    if len(tmp) == 0:
        continue

    def parse_month(v):

        try:
            parts = str(v).split(".")
            y = int(parts[0].replace("R",""))
            m = int(parts[1])
            return y * 100 + m
        except:
            return -1

    tmp["_sort"] = tmp["月"].apply(parse_month)

    latest = tmp.sort_values("_sort").tail(1)

    latest_accept = float(
        latest["受入可能数"].iloc[0]
    )

    if latest_accept <= 0:
        continue

    vacancy_rows.append({
        "園名": nursery_name,
        "最新受入枠": round(latest_accept,1),
        "平均受入枠": round(
            tmp["受入可能数"].mean(),
            1
        ),
        "最新待機": round(
            float(latest["待機人数"].iloc[0]),
            1
        ),
        "平均待機": round(
            tmp["待機人数"].mean(),
            1
        ),
        "通過率": round(
            tmp["通過率"].mean(),
            3
        )
    })

vacancy_df = pd.DataFrame(vacancy_rows)

if len(vacancy_df) > 0:

    vacancy_df = vacancy_df.sort_values(
        ["最新受入枠","平均受入枠"],
        ascending=False
    )

    st.dataframe(
        vacancy_df,
        use_container_width=True,
        hide_index=True
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


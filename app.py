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

st.info("👈 左上の「>>」を押して条件入力すると、診断を開始できます")

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

admission_season = st.sidebar.selectbox(
    "入園時期",
    [
        "通年",
        "🌸4月",
        "🌱5-6月",
        "☀️7-9月",
        "🍂10-12月",
        "❄️1-3月"
    ]
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

ward_nursery_df = nursery_df[
    (nursery_df["区"] == ward)
    &
    (nursery_df["年齢"] == age)
].copy()

ward_nursery_names = (
    ward_nursery_df["園名"]
    .dropna()
    .unique()
    .tolist()
)

# 区だけ指定した場合の通年初期値
# 区内の園の受入可能数・待機人数を合算する
if len(ward_nursery_df) > 0:

    accepted = float(
        ward_nursery_df["受入可能数"]
        .fillna(0)
        .sum()
    )

    waiting = float(
        ward_nursery_df["待機人数"]
        .fillna(0)
        .sum()
    )

    pass_ratio_actual = (
        accepted /
        max(
            accepted + waiting,
            1
        )
    )

else:

    accepted = 100
    waiting = 100
    pass_ratio_actual = 0.5


season_map = {
    "🌸4月": [4],
    "🌱5-6月": [5, 6],
    "☀️7-9月": [7, 8, 9],
    "🍂10-12月": [10, 11, 12],
    "❄️1-3月": [1, 2, 3],
}


def _get_month(v):

    try:
        return int(str(v).split(".")[1])
    except:
        return None


def _aggregate_monthly_metrics(target_nursery, target_season):

    # 園指定あり：その園だけ
    if target_nursery != "指定なし":

        base_df = monthly_df[
            (monthly_df["園名"] == target_nursery)
            &
            (monthly_df["年齢"] == age)
        ].copy()

    # 園指定なし：選択中の区にある園をまとめる
    else:

        base_df = monthly_df[
            (monthly_df["園名"].isin(ward_nursery_names))
            &
            (monthly_df["年齢"] == age)
        ].copy()

    if len(base_df) == 0:
        return None

    base_df["_month"] = (
        base_df["月"].apply(_get_month)
    )

    if target_season != "通年":

        base_df = base_df[
            base_df["_month"].isin(
                season_map[target_season]
            )
        ]

    if len(base_df) == 0:
        return None

    # 区だけ指定の場合は、月ごとに区内全園を合算してから平均する
    if target_nursery == "指定なし":

        monthly_sum = (
            base_df
            .groupby("月", as_index=False)[
                [
                    "受入可能数",
                    "待機人数"
                ]
            ]
            .sum()
        )

        accepted_avg = float(
            monthly_sum["受入可能数"]
            .fillna(0)
            .mean()
        )

        waiting_avg = float(
            monthly_sum["待機人数"]
            .fillna(0)
            .mean()
        )

        recruit_months = int(
            monthly_sum["受入可能数"]
            .fillna(0)
            .gt(0)
            .sum()
        )

        observed_months = int(
            len(monthly_sum)
        )

    # 園指定ありの場合は、その園の月次データを平均する
    else:

        accepted_avg = float(
            base_df["受入可能数"]
            .fillna(0)
            .mean()
        )

        waiting_avg = float(
            base_df["待機人数"]
            .fillna(0)
            .mean()
        )

        recruit_months = int(
            base_df["受入可能数"]
            .fillna(0)
            .gt(0)
            .sum()
        )

        observed_months = int(
            len(base_df)
        )

    vacancy_rate = (
        recruit_months /
        max(
            observed_months,
            1
        )
    )

    pass_ratio_actual_tmp = (
        accepted_avg /
        max(
            accepted_avg + waiting_avg,
            1
        )
    )

    return {
        "accepted_avg": accepted_avg,
        "waiting_avg": waiting_avg,
        "pass_ratio_actual": pass_ratio_actual_tmp,
        "recruit_months": recruit_months,
        "observed_months": observed_months,
        "vacancy_rate": vacancy_rate,
    }


# 園指定ありの場合は、まず園単体の通年データを使う
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


# 入園時期が通年以外なら、
# 園指定ありでも区のみ指定でも、月次データから季節別に上書きする
if admission_season != "通年":

    selected_season_metrics = _aggregate_monthly_metrics(
        nursery,
        admission_season
    )

    if selected_season_metrics is not None:

        accepted = selected_season_metrics["accepted_avg"]
        waiting = selected_season_metrics["waiting_avg"]
        pass_ratio_actual = selected_season_metrics[
            "pass_ratio_actual"
        ]

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

target_text = (
    f"📍 {ward} / {age} / {admission_season}"
)

if nursery != "指定なし":
    target_text += f"　🏫 {nursery}"

st.info(target_text)

# =====================================
# assumption note
# =====================================

if nursery == "指定なし":

    st.caption(
        "※ 保育園を指定しない場合は、選択した区内で複数の園を申請した場合の"
        "平均的な目安として推定しています。"
        "この診断では、現実的な申請数の目安として5〜8園程度を想定しています。"
        "1園だけに絞る場合や、人気園だけを希望する場合は、実際の通過率が低くなる可能性があります。"
    )

else:

    st.caption(
        "※ 保育園を指定した場合は、その園の過去データをもとに、"
        "必要偏差値と推定通過率を計算しています。"
    )

with st.expander("推定の前提について"):

    st.markdown(
        """
- **保育園を指定しない場合**
  選択した区内で、複数の園を申請した場合の平均的な目安として推定しています。

- **想定している申請数**
  現実的な保活の目安として、**5〜8園程度**の申請を想定しています。

- **注意点**
  実際の結果は、申請する園の組み合わせ、希望順位、兄弟加点、同点調整、年度ごとの募集状況によって変わります。
  特に、1園だけに絞る場合や人気園中心で申請する場合は、表示より厳しくなる可能性があります。
        """
    )


# =====================================
# result
# =====================================

st.markdown("### 📊 診断結果")

if admission_season != "通年":
    st.caption(
        f"{admission_season}の募集実績をもとに難易度を推定しています"
    )

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

season_results = {}

for label in season_map.keys():

    metrics = _aggregate_monthly_metrics(
        nursery,
        label
    )

    if metrics is None:
        continue

    threshold_s, pass_prob_s, pass_ratio_s = (
        get_pass_probability(
            scores,
            user_score,
            metrics["accepted_avg"],
            metrics["waiting_avg"],
            income
        )
    )

    threshold_hensachi_s = (
        (
            threshold_s - score_mean
        )
        / max(score_std, 0.01)
    ) * 10 + 50

    season_results[label] = {
        "threshold_hensachi": threshold_hensachi_s,
        "pass_prob": pass_prob_s,
        "accepted_avg": metrics["accepted_avg"],
        "waiting_avg": metrics["waiting_avg"],
        "recruit_months": metrics["recruit_months"],
        "observed_months": metrics["observed_months"],
        "vacancy_rate": metrics["vacancy_rate"],
    }

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



if len(season_results) > 0:

    st.markdown("### 🗓 入園時期別のボーダー・推定通過率")

    if nursery == "指定なし":

        st.caption(
            "※ 区内の園の月次データを合算し、入園時期ごとの必要偏差値と推定通過率を計算しています。"
        )

    else:

        st.caption(
            "※ 選択した園の月次データから、入園時期ごとの必要偏差値と推定通過率を計算しています。"
        )

    st.caption(
        "※ 空き枠発生率は、過去の月次データで受入可能数が1人以上あった月の割合です。"
        "実際の入園を保証するものではありません。"
    )

    items = list(season_results.items())

    for i in range(0, len(items), 2):

        cols = st.columns(2)

        for j in range(2):

            if i + j >= len(items):
                continue

            label, data = items[i + j]

            is_selected = (
                admission_season == label
            )

            border_color = (
                "#38bdf8"
                if is_selected
                else "transparent"
            )

            badge = (
                "選択中"
                if is_selected
                else ""
            )

            with cols[j]:

                st.markdown(
                    f"""
<div style="
background:#0f172a;
border:2px solid {border_color};
padding:12px;
border-radius:10px;
text-align:center;
margin-bottom:10px;
">

<div style="
font-size:15px;
font-weight:700;
color:white;
margin-bottom:4px;
">
{label} {badge}
</div>

<div style="
font-size:11px;
color:#94a3b8;
margin-bottom:2px;
">
推定必要偏差値
</div>

<div style="
font-size:26px;
font-weight:700;
color:white;
line-height:1.1;
margin-bottom:8px;
">
{data['threshold_hensachi']:.1f}
</div>

<div style="
font-size:11px;
color:#94a3b8;
margin-bottom:2px;
">
推定通過率
</div>

<div style="
font-size:20px;
font-weight:700;
color:white;
line-height:1.1;
margin-bottom:8px;
">
{data['pass_prob'] * 100:.0f}%
</div>

<div style="
font-size:11px;
color:#cbd5e1;
line-height:1.5;
">
平均受入 {data['accepted_avg']:.1f}人 /
平均待機 {data['waiting_avg']:.1f}人<br>
空き枠発生率 {data['vacancy_rate'] * 100:.0f}%<br>
<span style="font-size:10px;color:#94a3b8;">
過去{data['observed_months']}か月中{data['recruit_months']}か月で空きあり
</span>
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

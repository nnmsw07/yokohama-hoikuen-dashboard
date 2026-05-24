import urllib.parse

import folium
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_folium import st_folium

from model import (
    calc_user_score,
    difficulty_label,
    simulate_population,
    get_pass_probability
)

# =====================================
# page config
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
    height=0,
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
    height=0,
)

# =====================================
# title
# =====================================


st.markdown(
    "## 👶 横浜保活ダッシュボード"
)


st.caption(
    "横浜市公開データをもとに保育園難易度を分析"
)

st.info(
    "👈 左上の「>」を押すと条件入力できます"
)

# =====================================
# load data
# =====================================

ward_df = pd.read_csv(
    "data/ward_difficulty.csv"
)

nursery_df = pd.read_csv(
    "data/nursery_difficulty.csv"
)

monthly_df = pd.read_csv(
    "data/nursery_monthly.csv"
)

# =====================================
# geo
# =====================================

try:

    geo_df = pd.read_csv(
        "data/nursery_geo.csv"
    )

except:

    geo_df = None

# =====================================
# sidebar
# =====================================

st.sidebar.header("診断条件")

# =====================================
# ward
# =====================================

ward = st.sidebar.selectbox(

    "区",

    sorted(
        ward_df["区"].dropna().unique()
    )

)

# =====================================
# age
# =====================================

age = st.sidebar.selectbox(

    "年齢",

    [
        "0歳",
        "1歳",
        "2歳",
        "3歳",
        "4歳",
        "5歳"
    ]

)

# =====================================
# nursery source
# =====================================

ward_nurseries = nursery_df[
    (nursery_df["区"] == ward)
    &
    (nursery_df["年齢"] == age)
].copy()

# =====================================
# easy mode
# =====================================

st.sidebar.markdown("---")

show_easy_only = st.sidebar.checkbox(
    "入りやすい園を優先表示"
)

if show_easy_only:

    ward_nurseries = ward_nurseries.sort_values(

        ["難易度スコア", "通過率"],

        ascending=[True, False]

    )

else:

    ward_nurseries = ward_nurseries.sort_values(
        "園名"
    )

# =====================================
# search
# =====================================

search_text = st.sidebar.text_input(

    "保育園名で検索",

    placeholder="例: スターチャイルド"

)

if search_text:

    filtered_nurseries = ward_nurseries[

        ward_nurseries["園名"]
        .str.contains(
            search_text,
            case=False,
            na=False
        )

    ]

else:

    filtered_nurseries = ward_nurseries

# =====================================
# nursery select
# =====================================

nursery_options = [

    "指定なし"

] + filtered_nurseries[
    "園名"
].dropna().unique().tolist()

nursery_options = nursery_options[:100]

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
        "求職中"
    ]

)

# =====================================
# employment
# =====================================

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

# =====================================
# income
# =====================================

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

has_sibling = st.sidebar.checkbox(
    "兄弟姉妹が在園中"
)

single_parent = st.sidebar.checkbox(
    "ひとり親"
)

ninkaigai = st.sidebar.checkbox(
    "認可外保育利用"
)

nursery_worker = st.sidebar.checkbox(
    "保育士"
)

grandparents_nearby = st.sidebar.checkbox(
    "祖父母が近居"
)

saturday_work = st.sidebar.checkbox(
    "土曜勤務あり"
)

night_shift = st.sidebar.checkbox(
    "夜勤あり"
)

six_day_work = st.sidebar.checkbox(
    "週6勤務"
)

self_employed = st.sidebar.checkbox(
    "自営業"
)

# =====================================
# user score
# =====================================

user_score = calc_user_score(

    work_status,
    employment_type,

    has_sibling,
    single_parent,
    ninkaigai,

    nursery_worker,
    grandparents_nearby,
    saturday_work,
    night_shift,
    six_day_work,
    self_employed

)

# =====================================
# ward score
# =====================================

ward_row = ward_df[
    ward_df["区"] == ward
].iloc[0]

ward_score = float(
    ward_row["難易度スコア"]
)

# =====================================
# nursery score
# =====================================

if nursery != "指定なし":

    nursery_row = nursery_df[

        (nursery_df["園名"] == nursery)
        &
        (nursery_df["年齢"] == age)

    ]

    if len(nursery_row) > 0:

        nursery_score = float(
            nursery_row.iloc[0]["難易度スコア"]
        )

        accepted = float(
            nursery_row.iloc[0]["受入可能数"]
        )

        waiting = float(
            nursery_row.iloc[0]["待機人数"]
        )

        pass_ratio_actual = float(
            nursery_row.iloc[0]["通過率"]
        )

    else:

        nursery_score = ward_score

        accepted = 100
        waiting = 100
        pass_ratio_actual = 0.5

else:

    nursery_score = ward_score

    accepted = 100
    waiting = 100
    pass_ratio_actual = 0.5

# =====================================
# simulation
# =====================================

scores = simulate_population(
    age,
    ward
)

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
# result
# =====================================


st.markdown(
    "### 📊 診断結果"
)


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "あなたの指数",
        f"{user_score:.1f}"
    )

with col2:

    st.metric(
        "推定必要ライン",
        f"{threshold:.1f}"
    )

with col3:

    st.metric(
        "推定通過確率",
        f"{pass_prob * 100:.1f}%"
    )

# =====================================
# assumptions
# =====================================

if nursery == "指定なし":

    st.info(
        """
【この通過率について】

保育園を指定しない場合、

「同じ区で複数園（5〜10園程度）へ申請した場合に、
どこか1園へ通過できる確率」

を想定して計算しています。

以下を加味して推定しています：

・年齢別待機人数
・年齢別受入人数
・横浜市ランク近似
・複数園申請による待機人数重複
・実際の横浜保活の通過傾向

実際の横浜市選考では：

・兄弟加点
・転園
・辞退
・年度途中変動

なども影響するため、
参考値としてご利用ください。
"""
    )

else:

    st.info(
        """
【この通過率について】

この保育園を第一希望〜上位希望として
申請した場合を想定しています。

以下を加味して推定しています：

・年齢別待機人数
・年齢別受入人数
・横浜市ランク近似
・複数園申請による待機人数重複
・実際の横浜保活の通過傾向

実際の横浜市選考では：

・兄弟加点
・転園
・辞退
・年度途中変動

なども影響するため、
参考値としてご利用ください。
"""
    )

# =====================================
# labels
# =====================================

st.subheader(
    difficulty_label(nursery_score)
)

st.write(
    f"区平均難易度: {ward_score:.2f}"
)

if nursery != "指定なし":

    st.write(
        f"園難易度: {nursery_score:.2f}"
    )

    st.write(
        f"実データ通過率: {pass_ratio_actual:.1%}"
    )

# =====================================
# histogram
# =====================================

st.subheader("📉 スコア分布を見る")

hist_df = pd.DataFrame({
    "score": scores
})

fig = px.histogram(

    hist_df,

    x="score",

    nbins=40

)

fig.add_vline(

    x=user_score,

    line_color="red",

    annotation_text="あなた"

)

fig.add_vline(

    x=threshold,

    line_color="green",

    annotation_text="必要ライン"

)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================
# monthly trend
# =====================================

st.subheader("📈 月次推移")

if nursery != "指定なし":

    monthly_plot = monthly_df[

        (monthly_df["園名"] == nursery)
        &
        (monthly_df["年齢"] == age)

    ].copy()

    if len(monthly_plot) > 0:

        # =============================
        # sort
        # =============================

        monthly_plot = monthly_plot.sort_values(
            "月"
        )

        # =============================
        # columns check
        # =============================

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
                markers=True

            )

            st.plotly_chart(

                trend_fig,

                use_container_width=True

            )

        else:

            st.warning(
                "月次列が見つかりません"
            )

    else:

        st.info(
            "月次データがありません"
        )

# =====================================
# easy ranking
# =====================================

st.subheader("🟢 比較的入りやすい園")

st.caption(
    "※ 令和6年度〜令和8年度の月次データ平均をもとに算出"
)

st.caption(
    "※ 令和6年度〜令和8年度の月次データ平均をもとに算出"
)

recommend_df = nursery_df[
    nursery_df["区"] == ward
].copy()

recommend_df = recommend_df[
    recommend_df["年齢"] == age
]

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

# =====================================
# footer
# =====================================

st.divider()

st.caption(
    "ご意見・不具合報告はThreadsまたはXのDMへお願いします。"
)

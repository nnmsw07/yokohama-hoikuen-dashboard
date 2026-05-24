import os

import pandas as pd

import plotly.express as px

OUTPUT_DIR = (
    "docs/nurseries"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

nursery_df = pd.read_csv(
    "data/nursery_difficulty.csv"
)

yearly_df = pd.read_csv(
    "data/nursery_yearly.csv"
)

monthly_df = pd.read_csv(
    "data/nursery_monthly.csv"
)

for _, row in nursery_df.iterrows():

    nursery_name = row["園名"]

    yearly = yearly_df[
        yearly_df["園名"]
        == nursery_name
    ]

    monthly = monthly_df[
        monthly_df["園名"]
        == nursery_name
    ]

    # =================================
    # yearly graph
    # =================================

    fig_year = px.line(

        yearly,

        x="年度",

        y="難易度スコア",

        markers=True,

        title="年度別難易度推移"
    )

    year_html = fig_year.to_html(
        full_html=False,
        include_plotlyjs="cdn"
    )

    # =================================
    # monthly graph
    # =================================

    fig_month = px.line(

        monthly,

        x="月",

        y="合計",

        color="年度",

        markers=True,

        title="月別待機人数推移"
    )

    month_html = fig_month.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    html = f"""
    <html>

    <head>
        <meta charset='utf-8'>
        <title>{nursery_name}</title>
    </head>

    <body>

    <h1>{nursery_name}</h1>

    <p>
    区:
    {row['区']}
    </p>

    <p>
    難易度:
    {row['難易度スコア']:.2f}
    </p>

    <h2>
    年度別難易度推移
    </h2>

    {year_html}

    <h2>
    月別待機人数推移
    </h2>

    {month_html}

    </body>

    </html>
    """

    slug = nursery_name.replace(
        " ",
        "-"
    )

    path = os.path.join(
        OUTPUT_DIR,
        f"{slug}.html"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

print(
    "generated nursery pages"
)

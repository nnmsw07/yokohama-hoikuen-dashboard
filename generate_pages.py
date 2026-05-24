import pandas as pd
import os
import re

# =====================================
# データ読み込み
# =====================================

df = pd.read_csv(
    "data/nursery_difficulty.csv",
    encoding="utf-8-sig"
)

# =====================================
# 出力先
# =====================================

OUTPUT_DIR = "docs/nurseries"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

# =====================================
# 難易度カラー
# =====================================

def difficulty_color(label):

    if label == "激戦":
        return "#ff6b6b"

    elif label == "普通":
        return "#f7b731"

    else:
        return "#2ecc71"

# =====================================
# HTMLテンプレート
# =====================================

template = """
<!DOCTYPE html>
<html lang="ja">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{title}</title>

<meta name="description"
content="{description}">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:type"
content="website">

<style>

body {{
    font-family: sans-serif;
    max-width: 760px;
    margin: auto;
    padding: 20px;
    background: #fafafa;
}}

.card {{
    background: white;
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 20px;
}}

.badge {{
    display: inline-block;
    padding: 8px 14px;
    border-radius: 999px;
    color: white;
    background: {difficulty_color};
    font-weight: bold;
}}

.small {{
    color: #888;
    font-size: 13px;
}}

</style>

</head>

<body>

<h1>{name} の入りやすさ</h1>

<p>
{ward}にある {name} の
保育園難易度をデータから分析しています。
</p>

<div class="card">

<h2>推定難易度</h2>

<div class="badge">
{difficulty}
</div>

<p>
難易度スコア:
<strong>{score:.2f}</strong>
</p>

</div>

<div class="card">

<h2>待機人数</h2>

<ul>
<li>0歳: {age0}</li>
<li>1歳: {age1}</li>
<li>2歳: {age2}</li>
<li>合計: {total}</li>
</ul>

</div>

<div class="card">

<h2>分析コメント</h2>

<p>
{name} は {ward} の中でも
<strong>{difficulty}</strong>
と推定されます。
</p>

<p>
特に1歳クラスは
希望者が集中しやすく、
年度による変動にも注意が必要です。
</p>

</div>

<p class="small">
※横浜市公開データを元にした推定です
</p>

</body>
</html>
"""

# =====================================
# sitemap
# =====================================

sitemap_urls = []

# =====================================
# ページ生成
# =====================================

for _, row in df.iterrows():

    slug = re.sub(
        r"[^a-zA-Z0-9ぁ-んァ-ヶ一-龥]",
        "-",
        str(row["園名"])
    )

    filename = (
        f"{OUTPUT_DIR}/{slug}.html"
    )

    title = (
        f"{row['園名']}の入りやすさ｜"
        f"{row['区']} 保育園データ"
    )

    description = (
        f"{row['園名']}の"
        f"推定難易度・待機人数・"
        f"入りやすさを掲載"
    )

    html = template.format(
        title=title,
        description=description,
        name=row["園名"],
        ward=row["区"],
        difficulty=row["難易度"],
        difficulty_color=difficulty_color(
            row["難易度"]
        ),
        score=row["難易度スコア"],
        age0=row["0歳"],
        age1=row["1歳"],
        age2=row["2歳"],
        total=row["合計"]
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html)

    sitemap_urls.append(
        f"https://YOUR_DOMAIN/nurseries/{slug}.html"
    )

# =====================================
# sitemap.xml
# =====================================

sitemap = [
    '<?xml version="1.0" encoding="UTF-8"?>'
]

sitemap.append(
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
)

for url in sitemap_urls:

    sitemap.append(
        f"<url><loc>{url}</loc></url>"
    )

sitemap.append("</urlset>")

with open(
    "docs/sitemap.xml",
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(sitemap))

print("ページ生成完了")

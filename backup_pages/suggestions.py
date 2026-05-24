import streamlit as st

from firebase_config import db

from firebase_admin import firestore

from datetime import datetime

# =====================================
# ページ設定
# =====================================

st.set_page_config(
    page_title="改善提案",
    layout="centered"
)

# =====================================
# タイトル
# =====================================

st.title("📮 横浜市への改善提案")

st.write(
    """
    匿名で改善提案を投稿できます。

    保育園制度・点数制度・
    情報公開などについて、
    実際の声を集めています。
    """
)

# =====================================
# 入力補助
# =====================================

st.info(
    """
例：

・園ごとの倍率を公開してほしい
・点数制度を分かりやすくしてほしい
・空き情報をリアルタイム化してほしい
"""
)

# =====================================
# 入力
# =====================================

title = st.text_input(
    "タイトル"
)

ward = st.selectbox(
    "区",
    [
        "港北区",
        "青葉区",
        "都筑区",
        "鶴見区",
        "西区",
        "中区",
        "南区",
        "保土ケ谷区",
        "磯子区",
        "金沢区",
        "港南区",
        "旭区",
        "緑区",
        "瀬谷区",
        "栄区",
        "泉区",
        "神奈川区"
    ]
)

tags = st.multiselect(
    "タグ",
    [
        "保育園",
        "点数制度",
        "情報公開",
        "時短",
        "待機児童",
        "1歳問題",
        "兄弟加点"
    ]
)

content = st.text_area(
    "内容"
)

# =====================================
# NGワード
# =====================================

ng_words = [
    "死ね",
    "殺",
    "バカ",
    "住所",
    "電話番号"
]

# =====================================
# 投稿
# =====================================

if st.button("投稿する"):

    # 入力確認
    if not title or not content:

        st.error(
            "タイトルと内容を入力してください"
        )

    # NGワード
    elif any(
        w in content
        for w in ng_words
    ):

        st.error(
            "不適切な内容が含まれています"
        )

    else:

        db.collection(
            "suggestions"
        ).add({

            "title": title,
            "ward": ward,
            "tags": tags,
            "content": content,
            "created_at": datetime.utcnow()

        })

        st.success(
            "投稿しました"
        )

# =====================================
# 一覧
# =====================================

st.divider()

st.subheader(
    "みんなの提案"
)

# =====================================
# Firestore取得
# =====================================

docs = db.collection(
    "suggestions"
).order_by(
    "created_at",
    direction=firestore.Query.DESCENDING
).stream()

# =====================================
# 表示
# =====================================

for doc in docs:

    d = doc.to_dict()

    title = d.get(
        "title",
        ""
    )

    ward = d.get(
        "ward",
        ""
    )

    tags = d.get(
        "tags",
        []
    )

    content = d.get(
        "content",
        ""
    )

    created_at = d.get(
        "created_at"
    )

    # 日付整形
    if created_at:

        dt = created_at.strftime(
            "%Y-%m-%d %H:%M"
        )

    else:

        dt = ""

    # カード
    with st.container():

        st.markdown(
            f"### {title}"
        )

        st.caption(
            f"{ward} | "
            + " ".join(tags)
            + f" | {dt}"
        )

        st.write(
            content
        )

        st.divider()

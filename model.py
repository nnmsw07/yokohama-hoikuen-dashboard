import numpy as np


# =====================================
# 難易度ラベル
# =====================================

def difficulty_label(score):

    if score >= 4.8:
        return "🔥 超激戦"

    elif score >= 4.2:
        return "🟠 激戦"

    elif score >= 3.5:
        return "🟡 やや激戦"

    elif score >= 2.5:
        return "🟢 比較的入りやすい"

    else:
        return "🔵 入りやすい"


# =====================================
# ユーザースコア
# =====================================


def calc_user_score(

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

):

    # =================================
    # 横浜保活ランク近似
    #
    # ランク壁を強くするため、
    # rank_score * 100
    # + adjustment
    # で構成
    # =================================

    rank_map = {

        "月160時間以上": 5,
        "月140〜160時間": 4,
        "月120〜140時間": 3,
        "月100〜120時間": 2,
        "月64〜100時間": 1,
        "月64時間未満": 0

    }

    rank_score = rank_map.get(
        employment_type,
        0
    )

    # =================================
    # 求職中は大幅弱化
    # =================================

    if work_status == "求職中":

        rank_score = min(
            rank_score,
            1
        )

    # =================================
    # 出産・育児
    # =================================

    elif work_status == "出産・育児（下の子育児など）":

        rank_score = max(
            rank_score - 2,
            1
        )

    # =================================
    # 就学・介護
    # =================================

    elif work_status in [

        "介護・看護",
        "就学"

    ]:

        rank_score = max(
            rank_score - 1,
            1
        )

    # =================================
    # 調整指数
    # =================================

    adjust = 0

    # 兄弟加点
    if has_sibling:
        adjust += 7

    # ひとり親
    if single_parent:
        adjust += 8

    # 認可外
    if ninkaigai:
        adjust += 4

    # 保育士
    if nursery_worker:
        adjust += 5

    # 土曜勤務
    if saturday_work:
        adjust += 1

    # 夜勤
    if night_shift:
        adjust += 2

    # 週6
    if six_day_work:
        adjust += 2

    # 祖父母近居
    if grandparents_nearby:
        adjust -= 2

    # 自営業
    if self_employed:
        adjust -= 1

    # clamp
    adjust = max(
        min(adjust, 15),
        -15
    )

    
    # =================================
    # 年収補正
    #
    # 横浜では低年収が
    # やや有利傾向
    # =================================

    income_bias = np.random.choice(

        [

            -3,
            -1,
            0,
            1,
            2

        ],

        p=[

            0.10,
            0.20,
            0.40,
            0.20,
            0.10

        ]

    )

    # =================================
    # ランダムノイズ
    #
    # 実際の横浜保活では
    # 園希望順
    # 年度差
    # 転園
    # 地域偏差
    # 兄弟構成
    # などで分散するため
    # 完全ランク制にはならない
    # =================================

    noise = np.random.normal(
        0,
        6
    )

    # =================================
    # 最終スコア
    #
    # rank壁を維持しつつ
    # 正規分布へ近づける
    # =================================

    score = (

        rank_score * 10

        + adjust

        + income_bias

        + noise

    )

    return round(score, 1)




# =====================================
# 母集団シミュレーション
# =====================================


def simulate_population(
    age,
    ward
):

    # =================================
    # 横浜保活の人口構成を
    # モンテカルロ近似
    #
    # 実際の応募者属性割合を
    # ざっくり反映
    # =================================

    np.random.seed(42)

    scores = []

    # =================================
    # 区補正
    # =================================

    ward_bonus = {

        "港北区": 2,
        "中区": 2,
        "神奈川区": 1.5,
        "青葉区": 1.5,
        "都筑区": 1.5,

        "旭区": -1,
        "泉区": -1,
        "瀬谷区": -1

    }

    # =================================
    # 年齢補正
    # =================================

    age_bonus = {

        "0歳": -2,
        "1歳": 2,
        "2歳": 1,
        "3歳": -1,
        "4歳": -2,
        "5歳": -3

    }

    for _ in range(10000):

        # =============================
        # 就労状況
        # =============================

        work_status = np.random.choice(

            [

                "既に就労中",
                "育休復職予定",
                "出産・育児（下の子育児など）",
                "介護・看護",
                "就学",
                "求職中"

            ],

            p=[

                0.63,
                0.20,
                0.08,
                0.03,
                0.02,
                0.04

            ]

        )

        # =============================
        # 就労時間
        # =============================

        employment_type = np.random.choice(

            [

                "月160時間以上",
                "月140〜160時間",
                "月120〜140時間",
                "月100〜120時間",
                "月64〜100時間",
                "月64時間未満"

            ],

            p=[

                0.55,
                0.25,
                0.10,
                0.06,
                0.03,
                0.01

            ]

        )

        # =============================
        # 属性
        # =============================

        has_sibling = (
            np.random.rand() < 0.15
        )

        single_parent = (
            np.random.rand() < 0.05
        )

        ninkaigai = (
            np.random.rand() < 0.08
        )

        nursery_worker = (
            np.random.rand() < 0.02
        )

        grandparents_nearby = (
            np.random.rand() < 0.30
        )

        saturday_work = (
            np.random.rand() < 0.15
        )

        night_shift = (
            np.random.rand() < 0.08
        )

        six_day_work = (
            np.random.rand() < 0.05
        )

        self_employed = (
            np.random.rand() < 0.07
        )

        # =============================
        # score
        # =============================

        score = calc_user_score(

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

        # =============================
        # area adjustment
        # =============================

        score += ward_bonus.get(
            ward,
            0
        )

        score += age_bonus.get(
            age,
            0
        )

        scores.append(score)

    scores = np.array(scores)

    scores = np.clip(
        scores,
        10,
        90
    )

    return scores



# =====================================
# 通過率推定
# =====================================

def get_pass_probability(

    scores,
    user_score,
    accepted,
    waiting,
    income

):

    # =================================
    # pass ratio
    # =================================

    pass_ratio = accepted / max(
        waiting,
        1
    )

    pass_ratio = min(
        max(pass_ratio, 0.01),
        0.99
    )

    # =================================
    # threshold
    # =================================

    threshold = np.percentile(

        scores,

        (1 - pass_ratio) * 100

    )

    # =================================
    # probability
    # =================================

    pass_prob = np.mean(
        scores <= user_score
    )

    # =================================
    # 年収補正
    # 横浜保活では影響小
    # =================================

    income_adjust = {

        "〜400万": 1.02,
        "400〜600万": 1.01,
        "600〜800万": 1.00,
        "800〜1000万": 0.99,
        "1000万〜": 0.98

    }

    pass_prob *= income_adjust.get(
        income,
        1.0
    )

    # =================================
    # clamp
    # =================================

    pass_prob = min(
        max(pass_prob, 0.01),
        0.99
    )

    return (

        round(threshold, 1),

        round(pass_prob, 4),

        round(pass_ratio, 4)

    )


import numpy as np


# =====================================
# ユーザースコア計算
# =====================================



def calc_user_score(

    work_status,
    employment_type,

    has_sibling,
    single_parent,
    ninkaigai,

    nursery_worker=False,
    grandparents_nearby=False,
    saturday_work=False,
    night_shift=False,
    six_day_work=False,
    self_employed=False

):

    # =================================
    # 横浜市ランク壁再現
    #
    # A/B/C... をまず決定し、
    # 調整指数は ±10未満へ制限。
    #
    # これにより、
    # BランクがAランクを
    # 超えにくくする。
    # =================================

    # =================================
    # 就労ランク
    # =================================

    # =================================
    # 実データ分布へキャリブレーション
    #
    # Aランク:
    # 48〜58
    #
    # Bランク:
    # 40〜48
    #
    # C以下:
    # 30〜40
    # =================================

    rank_base = {

        "月160時間以上": 52,
        "月140〜160時間": 48,
        "月120〜140時間": 44,
        "月100〜120時間": 40,
        "月64〜100時間": 36,
        "月64時間未満": 30

    }

    score = rank_base.get(
        employment_type,
        50
    )

    # =================================
    # 求職中補正
    # =================================

    if work_status == "求職中":

        score -= 8

    elif work_status == "育休復職予定":

        score += 0

    # =================================
    # adjustment
    # =================================

    adjustment = 0

    if has_sibling:
        adjustment += 3

    if single_parent:
        adjustment += 4

    if ninkaigai:
        adjustment += 3

    if nursery_worker:
        adjustment += 2

    if saturday_work:
        adjustment += 1

    if night_shift:
        adjustment += 2

    if six_day_work:
        adjustment += 2

    if self_employed:
        adjustment += 1

    # =================================
    # 祖父母近居は軽微減点
    # =================================

    if grandparents_nearby:
        adjustment -= 2

    # =================================
    # 調整指数制限
    # =================================

    adjustment = max(
        min(adjustment, 8),
        -8
    )

    score += adjustment

    return score




# =====================================
# 難易度ラベル
# =====================================

def difficulty_label(score):

    if score >= 4:
        return "🔥 超激戦"

    elif score >= 3:
        return "🔴 激戦"

    elif score >= 2:
        return "⚠️ やや激戦"

    else:
        return "🟢 比較的入りやすい"


# =====================================
# 年収補正
# =====================================

def income_adjustment(income):

    table = {

        "〜400万": -1.5,
        "400〜600万": -0.5,
        "600〜800万": 0,
        "800〜1000万": 0.5,
        "1000万〜": 1.5

    }

    return table.get(
        income,
        0
    )


# =====================================
# 母集団シミュレーション
# =====================================

def simulate_population(
    age,
    ward=None,
    n=10000
):

    # =================================
    # 現実寄りキャリブレーション
    # =================================

    params = {

        "0歳": (45, 4),
        "1歳": (48, 4),
        "2歳": (46, 4)

    }

    mean, std = params[age]

    # =================================
    # 区別統計
    # =================================

    ward_stats = {

        "青葉区": {
            "high_income": 0.42,
            "grandparents": 0.20,
            "dual_fulltime": 0.68
        },

        "都筑区": {
            "high_income": 0.35,
            "grandparents": 0.24,
            "dual_fulltime": 0.70
        },

        "港北区": {
            "high_income": 0.35,
            "grandparents": 0.22,
            "dual_fulltime": 0.72
        },

        "西区": {
            "high_income": 0.38,
            "grandparents": 0.18,
            "dual_fulltime": 0.71
        },

        "中区": {
            "high_income": 0.30,
            "grandparents": 0.28,
            "dual_fulltime": 0.64
        },

        "神奈川区": {
            "high_income": 0.28,
            "grandparents": 0.30,
            "dual_fulltime": 0.66
        },

        "戸塚区": {
            "high_income": 0.25,
            "grandparents": 0.35,
            "dual_fulltime": 0.62
        },

        "港南区": {
            "high_income": 0.24,
            "grandparents": 0.36,
            "dual_fulltime": 0.61
        },

        "磯子区": {
            "high_income": 0.22,
            "grandparents": 0.38,
            "dual_fulltime": 0.58
        },

        "鶴見区": {
            "high_income": 0.18,
            "grandparents": 0.38,
            "dual_fulltime": 0.58
        },

        "保土ケ谷区": {
            "high_income": 0.22,
            "grandparents": 0.36,
            "dual_fulltime": 0.60
        },

        "旭区": {
            "high_income": 0.17,
            "grandparents": 0.44,
            "dual_fulltime": 0.54
        },

        "瀬谷区": {
            "high_income": 0.15,
            "grandparents": 0.46,
            "dual_fulltime": 0.52
        },

        "泉区": {
            "high_income": 0.16,
            "grandparents": 0.45,
            "dual_fulltime": 0.53
        },

        "栄区": {
            "high_income": 0.18,
            "grandparents": 0.43,
            "dual_fulltime": 0.55
        },

        "金沢区": {
            "high_income": 0.20,
            "grandparents": 0.40,
            "dual_fulltime": 0.57
        },

        "緑区": {
            "high_income": 0.27,
            "grandparents": 0.30,
            "dual_fulltime": 0.64
        },

        "南区": {
            "high_income": 0.14,
            "grandparents": 0.40,
            "dual_fulltime": 0.50
        }

    }

    default_stats = {

        "high_income": 0.25,
        "grandparents": 0.35,
        "dual_fulltime": 0.60

    }

    stats = ward_stats.get(
        ward,
        default_stats
    )

    scores = []

    for _ in range(n):

        s = np.random.normal(
            mean,
            std
        )

        # =============================
        # 共働き
        # =============================

        if np.random.rand() < stats["dual_fulltime"]:
            s += 1.5

        # =============================
        # 兄弟加点
        # =============================

        if np.random.rand() < 0.30:
            s += 2

        # =============================
        # ひとり親
        # =============================

        if np.random.rand() < 0.10:
            s += 4

        # =============================
        # 認可外
        # =============================

        if np.random.rand() < 0.15:
            s += 1

        # =============================
        # 保育士
        # =============================

        if np.random.rand() < 0.03:
            s += 2

        # =============================
        # 祖父母近居
        # =============================

        if np.random.rand() < stats["grandparents"]:
            s -= 1

        # =============================
        # 土曜勤務
        # =============================

        if np.random.rand() < 0.25:
            s += 0.5

        # =============================
        # 夜勤
        # =============================

        if np.random.rand() < 0.08:
            s += 1

        # =============================
        # 週6
        # =============================

        if np.random.rand() < 0.12:
            s += 1

        # =============================
        # 自営業
        # =============================

        if np.random.rand() < 0.10:
            s -= 0.5

        # =============================
        # 年収補正
        # =============================

        r = np.random.rand()

        high_income_bias = stats[
            "high_income"
        ]

        if r < high_income_bias:
            s -= 1

        elif r < (
            high_income_bias + 0.20
        ):
            s -= 0.5

        elif r < 0.75:
            s += 0

        elif r < 0.92:
            s += 0.5

        else:
            s += 1.5

        scores.append(s)

    return np.array(scores)


# =====================================
# 通過確率
# =====================================

def get_pass_probability(

    scores,
    user_score,

    accepted=100,
    waiting=100,

    income="600〜800万"

):

    # =================================
    # 通過率
    # =================================

    # =================================
    # 横浜保活では
    # 1人が複数園申し込むため、
    # 待機人数は重複カウントされる
    # =================================

    effective_waiting = (
        waiting * 0.35
    )

    pass_ratio = accepted / (
        accepted
        + effective_waiting
        + 1
    )

    pass_ratio = max(
        0.01,
        min(0.99, pass_ratio)
    )

    # =================================
    # ボーダー
    # =================================

    threshold = np.percentile(

        scores,

        100 * (1 - pass_ratio)

    )

    # =================================
    # 年収補正
    # =================================

    threshold += income_adjustment(
        income
    )

    # =================================
    # 疑似確率
    # =================================

    diff = (
        user_score
        - threshold
    )

    prob = 1 / (
        1 + np.exp(-diff / 3)
    )

    prob = max(
        0,
        min(1, prob)
    )

    return (
        threshold,
        prob,
        pass_ratio
    )

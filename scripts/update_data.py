import os
import glob
import pandas as pd

RAW_DIR = "data/raw"

WARD_OUTPUT = (
    "data/ward_difficulty.csv"
)

NURSERY_OUTPUT = (
    "data/nursery_difficulty.csv"
)

YEARLY_OUTPUT = (
    "data/nursery_yearly.csv"
)

MONTHLY_OUTPUT = (
    "data/nursery_monthly.csv"
)

year_weights = {

    "令和6": 1.0,
    "令和7": 1.5,
    "令和8": 2.0

}

year_dirs = glob.glob(
    os.path.join(
        RAW_DIR,
        "令和*"
    )
)

all_rows = []

# =====================================
# helper
# =====================================

def load_all_sheets(path):

    xls = pd.ExcelFile(path)

    frames = []

    for sheet in xls.sheet_names:

        df = pd.read_excel(
            path,
            sheet_name=sheet
        )

        df["月"] = sheet

        frames.append(df)

    return pd.concat(
        frames,
        ignore_index=True
    )

# =====================================
# 年度処理
# =====================================

for year_dir in year_dirs:

    year = os.path.basename(
        year_dir
    )

    print(
        f"processing: {year}"
    )

    waiting_path = glob.glob(
        os.path.join(
            year_dir,
            "*待ち*.xlsx"
        )
    )[0]

    accepted_path = glob.glob(
        os.path.join(
            year_dir,
            "*受入*.xlsx"
        )
    )[0]

    enrolled_path = glob.glob(
        os.path.join(
            year_dir,
            "*入所児童*.xlsx"
        )
    )[0]

    waiting_df = load_all_sheets(
        waiting_path
    )

    accepted_df = load_all_sheets(
        accepted_path
    )

    enrolled_df = load_all_sheets(
        enrolled_path
    )

    for df in [
        waiting_df,
        accepted_df,
        enrolled_df
    ]:

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

    # =================================
    # merge
    # =================================

    base = waiting_df.copy()

    accepted_cols = [
        c for c in accepted_df.columns
        if c in [
            "区",
            "施設・事業名",
            "受入可能数",
            "月"
        ]
    ]

    enrolled_cols = [
        c for c in enrolled_df.columns
        if c in [
            "区",
            "施設・事業名",
            "入所児童数",
            "月"
        ]
    ]

    base = base.merge(

        accepted_df[
            accepted_cols
        ],

        on=[
            "区",
            "施設・事業名",
            "月"
        ],

        how="left"
    )

    base = base.merge(

        enrolled_df[
            enrolled_cols
        ],

        on=[
            "区",
            "施設・事業名",
            "月"
        ],

        how="left"
    )

    # =================================
    # rename
    # =================================

    base = base.rename(
        columns={
            "施設・事業名": "園名"
        }
    )

    # =================================
    # 数値化
    # =================================

    for col in [
        "受入可能数",
        "合計",
        "入所児童数"
    ]:

        if col not in base.columns:
            base[col] = 0

        base[col] = pd.to_numeric(
            base[col],
            errors="coerce"
        ).fillna(0)

    # =================================
    # 通過率
    # =================================

    base["通過率"] = (
        base["受入可能数"]
        /
        (
            base["受入可能数"]
            + base["合計"]
            + 1
        )
    )

    # =================================
    # 難易度
    # =================================

    base["単年難易度"] = (
        1 - base["通過率"]
    ) * 5

    base["年度"] = year

    base["weight"] = year_weights.get(
        year,
        1.0
    )

    base["weighted_score"] = (
        base["単年難易度"]
        * base["weight"]
    )

    all_rows.append(base)

# =====================================
# 結合
# =====================================

raw = pd.concat(
    all_rows,
    ignore_index=True
)

# =====================================
# 園別
# =====================================

nursery_df = raw.groupby(
    ["区", "園名"]
).agg({

    "weighted_score": "sum",
    "weight": "sum",
    "受入可能数": "mean",
    "合計": "mean",
    "入所児童数": "mean",
    "通過率": "mean"

}).reset_index()

nursery_df["難易度スコア"] = (
    nursery_df["weighted_score"]
    /
    nursery_df["weight"]
)

nursery_df = nursery_df.sort_values(
    "難易度スコア",
    ascending=False
)

nursery_df.to_csv(
    NURSERY_OUTPUT,
    index=False
)

# =====================================
# 区別
# =====================================

ward_df = nursery_df.groupby(
    "区"
).agg({

    "難易度スコア": "mean",
    "通過率": "mean",
    "園名": "count"

}).reset_index()

ward_df = ward_df.rename(
    columns={
        "園名": "園数"
    }
)

ward_df.to_csv(
    WARD_OUTPUT,
    index=False
)

# =====================================
# 年度推移
# =====================================

yearly_df = raw.groupby(
    ["年度", "区", "園名"]
).agg({

    "単年難易度": "mean",
    "通過率": "mean",
    "受入可能数": "mean",
    "合計": "mean"

}).reset_index()

yearly_df = yearly_df.rename(
    columns={
        "単年難易度": "難易度スコア"
    }
)

yearly_df.to_csv(
    YEARLY_OUTPUT,
    index=False
)

# =====================================
# 月次推移
# =====================================

monthly_df = raw.groupby(
    ["年度", "月", "区", "園名"]
).agg({

    "単年難易度": "mean",
    "通過率": "mean",
    "受入可能数": "mean",
    "合計": "mean"

}).reset_index()

monthly_df = monthly_df.rename(
    columns={
        "単年難易度": "難易度スコア"
    }
)

monthly_df.to_csv(
    MONTHLY_OUTPUT,
    index=False
)

print(
    "saved monthly analysis"
)

# =====================================
# HTML生成
# =====================================

os.system(
    "python scripts/generate_pages.py"
)

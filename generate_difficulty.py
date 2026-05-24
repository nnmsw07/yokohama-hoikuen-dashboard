import os
import glob
import pandas as pd

# =====================================
# paths
# =====================================

RAW_DIR = "data/raw"

WARD_OUTPUT = "data/ward_difficulty.csv"
NURSERY_OUTPUT = "data/nursery_difficulty.csv"
YEARLY_OUTPUT = "data/nursery_yearly.csv"
MONTHLY_OUTPUT = "data/nursery_monthly.csv"

# =====================================
# weights
# =====================================

YEAR_WEIGHTS = {

    "令和6": 1.0,
    "令和7": 1.5,
    "令和8": 2.0

}

# =====================================
# helper
# =====================================

def normalize_columns(df):

    df.columns = [
        str(c).strip()
        for c in df.columns
    ]

    return df

# =====================================
# 年齢判定
# =====================================

def detect_age(col):

    c = str(col).strip()

    mapping = {

        "0歳児": "0歳",
        "1歳児": "1歳",
        "2歳児": "2歳",
        "3歳児": "3歳",
        "4歳児": "4歳",
        "5歳児": "5歳",

        "０歳児": "0歳",
        "１歳児": "1歳",
        "２歳児": "2歳",
        "３歳児": "3歳",
        "４歳児": "4歳",
        "５歳児": "5歳"

    }

    return mapping.get(c)

# =====================================
# monthly excel
# =====================================

def load_monthly_excel(
    path,
    value_name
):

    xls = pd.ExcelFile(path)

    all_rows = []

    for sheet in xls.sheet_names:

        print(f"loading: {sheet}")

        try:

            df = pd.read_excel(

                path,

                sheet_name=sheet,

                header=1

            )

        except Exception as e:

            print("skip:", sheet, e)

            continue

        df = normalize_columns(df)

        # =================================
        # rename
        # =================================

        df = df.rename(
            columns={

                "施設所在区": "区",
                "施設・事業名": "園名"

            }
        )

        if "区" not in df.columns:
            continue

        if "園名" not in df.columns:
            continue

        # =================================
        # age columns
        # =================================

        age_cols = []

        for col in df.columns:

            age = detect_age(col)

            if age:

                age_cols.append(
                    (col, age)
                )

        print("age_cols:", age_cols)

        if len(age_cols) == 0:

            continue

        # =================================
        # age rows
        # =================================

        for age_col, age_name in age_cols:

            temp = df[[
                "区",
                "園名",
                age_col
            ]].copy()

            temp = temp.rename(
                columns={
                    age_col: value_name
                }
            )

            temp["年齢"] = age_name

            temp["月"] = sheet

            all_rows.append(temp)

    if len(all_rows) == 0:

        raise Exception(
            f"no rows loaded: {path}"
        )

    result = pd.concat(
        all_rows,
        ignore_index=True
    )

    # =================================
    # duplicate remove
    # =================================

    result = result.groupby(

        [
            "区",
            "園名",
            "年齢",
            "月"
        ]

    ).agg({

        value_name: "sum"

    }).reset_index()

    return result

# =====================================
# year dirs
# =====================================

year_dirs = glob.glob(
    os.path.join(
        RAW_DIR,
        "令和*"
    )
)

all_data = []

# =====================================
# process years
# =====================================

for year_dir in year_dirs:

    year = os.path.basename(
        year_dir
    )

    print("processing:", year)

    # =================================
    # files
    # =================================

    waiting_files = glob.glob(
        os.path.join(
            year_dir,
            "*待*.xlsx"
        )
    )

    accepted_files = glob.glob(
        os.path.join(
            year_dir,
            "*受*.xlsx"
        )
    )

    enrolled_files = glob.glob(
        os.path.join(
            year_dir,
            "*入所*.xlsx"
        )
    )

    if len(waiting_files) == 0:
        raise Exception(
            f"waiting file not found: {year}"
        )

    if len(accepted_files) == 0:
        raise Exception(
            f"accepted file not found: {year}"
        )

    if len(enrolled_files) == 0:
        raise Exception(
            f"enrolled file not found: {year}"
        )

    waiting_path = waiting_files[0]
    accepted_path = accepted_files[0]
    enrolled_path = enrolled_files[0]

    # =================================
    # load
    # =================================

    waiting_df = load_monthly_excel(
        waiting_path,
        "待機人数"
    )

    accepted_df = load_monthly_excel(
        accepted_path,
        "受入可能数"
    )

    enrolled_df = load_monthly_excel(
        enrolled_path,
        "入所児童数"
    )

    # =================================
    # merge
    # =================================

    base = waiting_df.merge(

        accepted_df,

        on=[
            "区",
            "園名",
            "年齢",
            "月"
        ],

        how="outer"

    )

    base = base.merge(

        enrolled_df,

        on=[
            "区",
            "園名",
            "年齢",
            "月"
        ],

        how="outer"

    )

    # =================================
    # numeric
    # =================================

    for col in [

        "待機人数",
        "受入可能数",
        "入所児童数"

    ]:

        base[col] = pd.to_numeric(
            base[col],
            errors="coerce"
        ).fillna(0)

    # =================================
    # duplicated apply calibration
    # =================================

    effective_waiting = (
        base["待機人数"] * 0.35
    )

    # =================================
    # pass ratio
    # =================================

    base["通過率"] = (

        base["受入可能数"]

        /

        (
            base["受入可能数"]
            + effective_waiting
            + 1
        )

    )

    # =================================
    # score
    # =================================

    base["単年難易度"] = (

        1 - base["通過率"]

    ) * 5

    base["年度"] = year

    base["weight"] = YEAR_WEIGHTS.get(
        year,
        1.0
    )

    base["weighted_score"] = (

        base["単年難易度"]

        * base["weight"]

    )

    all_data.append(base)

# =====================================
# concat
# =====================================

raw = pd.concat(
    all_data,
    ignore_index=True
)

# =====================================
# nursery
# =====================================

nursery_df = raw.groupby(
    ["区", "園名", "年齢"]
).agg({

    "weighted_score": "sum",
    "weight": "sum",

    "待機人数": "mean",
    "受入可能数": "mean",
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
# ward
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
# yearly
# =====================================

yearly_df = raw.groupby(
    ["年度", "区", "園名", "年齢"]
).agg({

    "単年難易度": "mean",
    "通過率": "mean"

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
# monthly
# =====================================

monthly_df = raw.groupby(
    ["年度", "月", "区", "園名", "年齢"]
).agg({

    "単年難易度": "mean",

    "通過率": "mean",

    "待機人数": "mean",

    "受入可能数": "mean",

    "入所児童数": "mean"

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

print("✅ completed")

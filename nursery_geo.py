# geocode_nursery.py

import time
import requests
import pandas as pd
from pathlib import Path

# =====================================
# files
# =====================================

FILES = [
    "公表施設情報_認可_神奈川県_20260525.csv",
    "公表施設情報_認可外_神奈川県横浜市_20260525.csv"
]

OUTPUT = "data/nursery_geo.csv"

# =====================================
# geocoder
# =====================================

def geocode(address):

    url = "https://msearch.gsi.go.jp/address-search/AddressSearch"

    try:

        r = requests.get(
            url,
            params={"q": address},
            timeout=10
        )

        data = r.json()

        if len(data) == 0:
            return None, None

        lon, lat = data[0]["geometry"]["coordinates"]

        return lat, lon

    except Exception as e:

        print("ERROR:", address, e)

        return None, None

# =====================================
# load csv
# =====================================

dfs = []

for file in FILES:

    print("loading:", file)

    try:

        df = pd.read_csv(
            file,
            encoding="utf-8"
        )

    except:

        df = pd.read_csv(
            file,
            encoding="cp932"
        )

    dfs.append(df)

df = pd.concat(
    dfs,
    ignore_index=True
)

# =====================================
# columns
# =====================================

print("")
print("===== columns =====")
print(df.columns.tolist())
print("===================")

# =====================================
# nursery name
# =====================================

NAME_COL = "施設の名称"

if NAME_COL not in df.columns:
    raise Exception("施設の名称 列が見つかりません")

# =====================================
# address columns
# =====================================

address_cols = []

for c in df.columns:

    c2 = str(c)

    if "施設の所在地" in c2:
        address_cols.append(c)

print("")
print("===== address cols =====")

for c in address_cols:
    print(c)

print("========================")

if len(address_cols) == 0:
    raise Exception("住所列が見つかりません")

# =====================================
# create address
# =====================================

df["住所"] = ""

for c in address_cols:

    df["住所"] += (
        df[c]
        .fillna("")
        .astype(str)
        .str.strip()
    )

# =====================================
# rename
# =====================================

df = df.rename(columns={
    NAME_COL: "園名"
})

# =====================================
# remove empty
# =====================================

df = df[
    df["住所"].str.len() > 5
].copy()

# =====================================
# geocode
# =====================================

results = []

for i, row in df.iterrows():

    name = str(row["園名"]).strip()
    address = str(row["住所"]).strip()

    print(f"[{i}] {name}")
    print(address)

    lat, lon = geocode(address)

    results.append({

        "園名": name,
        "住所": address,
        "lat": lat,
        "lon": lon

    })

    time.sleep(0.2)

# =====================================
# save
# =====================================

geo_df = pd.DataFrame(results)

Path("data").mkdir(
    exist_ok=True
)

geo_df.to_csv(
    OUTPUT,
    index=False
)

print("")
print("==========================")
print("saved:", OUTPUT)
print("==========================")
print("")
print(geo_df.head())

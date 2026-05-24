import pandas as pd
import requests
import time

df = pd.read_csv(
    "data/nursery_difficulty.csv"
)

addresses = []

for _, row in df.iterrows():

    nursery = row["園名"]

    query = f"{nursery} 横浜市"

    print(query)

    try:

        url = (
            "https://nominatim.openstreetmap.org/search"
        )

        params = {

            "q": query,
            "format": "json",
            "limit": 1

        }

        headers = {
            "User-Agent": "hoikuen-map"
        }

        r = requests.get(
            url,
            params=params,
            headers=headers
        )

        data = r.json()

        if len(data) > 0:

            address = data[0].get(
                "display_name",
                ""
            )

        else:

            address = ""

    except:

        address = ""

    addresses.append(address)

    time.sleep(1)

df["住所"] = addresses

df.to_csv(
    "data/nursery_master.csv",
    index=False
)

from geopy.geocoders import Nominatim

import pandas as pd
import time

df = pd.read_csv(
    "data/nursery_master.csv"
)

geolocator = Nominatim(
    user_agent="hoikuen-map"
)

lats = []
lons = []

for _, row in df.iterrows():

    address = row["住所"]

    try:

        location = geolocator.geocode(
            address
        )

        if location:

            lat = location.latitude
            lon = location.longitude

        else:

            lat = None
            lon = None

    except:

        lat = None
        lon = None

    lats.append(lat)
    lons.append(lon)

    time.sleep(1)

df["lat"] = lats
df["lon"] = lons

df.to_csv(
    "data/nursery_geo.csv",
    index=False
)

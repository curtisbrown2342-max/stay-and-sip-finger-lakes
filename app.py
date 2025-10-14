import streamlit as st
import pandas as pd
import json
import pydeck as pdk
from pathlib import Path

st.set_page_config(page_title="Stay & Sip Finger Lakes", page_icon="🍷", layout="wide")

@st.cache_data
def load_json(path):
    with open(path, "r") as f:
        return pd.DataFrame(json.load(f))

st.title("🍷 Stay & Sip Finger Lakes")
st.caption("Discover cozy stays, wineries & distilleries, attractions, and wedding venues around Keuka, Seneca, and Cayuga Lakes.")

st.sidebar.header("Search")
lake_opts = ["All", "Keuka", "Seneca", "Cayuga"]
lake = st.sidebar.selectbox("Lake", lake_opts, index=0)
budget = st.sidebar.slider("Max price per night (stays)", 100, 400, 300, step=10)
st.sidebar.markdown("---")
view = st.sidebar.radio("View", ["Stays", "Wineries & Distilleries", "Attractions", "Wedding Venues", "Map", "Itineraries"], index=0)

# Load datasets
stays_df = load_json("data/stays.json")
wineries_df = load_json("data/wineries.json")
attr_df = load_json("data/attractions.json")
venues_df = load_json("data/wedding_venues.json")
itin_df = load_json("data/itineraries.json")

def apply_lake(df):
    if lake != "All" and "lake" in df.columns:
        return df[df["lake"] == lake]
    return df

def card_grid(df, card_type):
    if df.empty:
        st.info("No results. Try broadening filters.")
        return
    cols_per_row = 3
    rows = [df.iloc[i:i+cols_per_row] for i in range(0, len(df), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, (_, item) in zip(cols, row.iterrows()):
            with col:
                if "image" in item and isinstance(item["image"], str) and item["image"]:
                    st.image(item["image"], use_column_width=True)
                title = item.get("name", card_type)
                subtitle = item.get("address", item.get("lake", ""))
                st.subheader(title)
                if card_type == "stay":
                    meta = f"{item.get('type','')} • {item.get('beds','?')} beds • up to {item.get('guests','?')} guests"
                    st.markdown(f"**${int(item.get('price_per_night',0))}/night** • {meta}")
                    tags = ", ".join(item.get("tags", []))
                    if tags:
                        st.caption(tags)
                elif card_type == "winery":
                    bits = []
                    if item.get("tasting"): bits.append("Tastings")
                    if item.get("tour"): bits.append("Tours")
                    st.markdown(f"{', '.join(bits)}")
                    st.caption(item.get("notes",""))
                elif card_type == "attraction":
                    st.markdown(item.get("category",""))
                    st.caption(item.get("notes",""))
                elif card_type == "venue":
                    st.markdown(f"{item.get('type','')} • up to {item.get('capacity','?')} guests")
                    st.caption(item.get("notes",""))
                if subtitle:
                    st.caption(subtitle)
                link = item.get("link","")
                if link:
                    st.link_button("View details / Book", link, use_container_width=True)

if view == "Stays":
    df = apply_lake(stays_df)
    df = df[df["price_per_night"] <= budget]
    type_opts = ["All"] + sorted(df["type"].dropna().unique().tolist())
    tsel = st.selectbox("Type", type_opts, index=0)
    if tsel != "All":
        df = df[df["type"] == tsel]
    card_grid(df, "stay")

elif view == "Wineries & Distilleries":
    df = apply_lake(wineries_df)
    only_tastings = st.checkbox("Show places with tastings", value=False)
    if only_tastings:
        df = df[df["tasting"] == True]
    card_grid(df, "winery")

elif view == "Attractions":
    df = apply_lake(attr_df)
    cat_opts = ["All"] + sorted(df["category"].dropna().unique().tolist())
    csel = st.selectbox("Category", cat_opts, index=0)
    if csel != "All":
        df = df[df["category"] == csel]
    card_grid(df, "attraction")

elif view == "Wedding Venues":
    df = apply_lake(venues_df)
    min_cap = st.slider("Min capacity", 50, 300, 100, step=25)
    df = df[df["capacity"] >= min_cap]
    card_grid(df, "venue")

elif view == "Map":
    st.subheader("All Listings Map")
    combined = []
    for dataset, ctype in [(stays_df, "Stay"), (wineries_df, "Winery"), (attr_df, "Attraction"), (venues_df, "Wedding Venue")]:
        d = apply_lake(dataset).copy()
        d["ctype"] = ctype
        combined.append(d[["name","lat","lng","ctype","lake"]])
    mdf = pd.concat(combined, ignore_index=True)
    if not mdf.empty:
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v11",
            initial_view_state=pdk.ViewState(latitude=42.6, longitude=-77.1, zoom=8, pitch=0),
            layers=[pdk.Layer(
                "ScatterplotLayer",
                data=mdf.rename(columns={"lng":"lon"}),
                get_position="[lon, lat]",
                get_radius=800,
                pickable=True,
            )],
            tooltip={"text": "{name}\n{ctype} • {lake} Lake"}
        ))
    else:
        st.info("No locations to show.")

elif view == "Itineraries":
    st.subheader("Trip Ideas")
    df = apply_lake(itin_df)
    if df.empty:
        st.info("Add itineraries in data/itineraries.json")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['title']} • {row['days']} days"):
                st.write(row["summary"])
                st.caption(f"Focus: {row['lake']} Lake")
                st.write("**Stays**")
                st.table(stays_df[stays_df["id"].isin(row["stays"])][["name","address","price_per_night"]])
                st.write("**Wineries**")
                st.table(wineries_df[wineries_df["id"].isin(row["wineries"])][["name","address"]])
                st.write("**Attractions**")
                st.table(attr_df[attr_df["id"].isin(row.get("attractions", []))][["name","address"]])

st.markdown("---")
st.caption("Affiliate disclosure: We may earn a commission when you book via links on this site.")
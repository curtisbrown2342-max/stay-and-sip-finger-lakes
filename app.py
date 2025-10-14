import os
import json
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(
    page_title="Stay & Sip Finger Lakes",
    page_icon="🍷",
    layout="wide",
)

# ---------- Data loading (cache invalidates when files change) ----------
@st.cache_data
def _load_json_df(path: str, _mtime: float) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

def load_json_df(path: str) -> pd.DataFrame:
    """Wrapper that forces cache refresh when the file's modified time changes."""
    mtime = os.path.getmtime(path)
    return _load_json_df(path, mtime)

def safe_load(path: str) -> pd.DataFrame:
    try:
        return load_json_df(path)
    except json.JSONDecodeError as e:
        st.error(
            f"{Path(path).name} has invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"
        )
        return pd.DataFrame()

# ---------- Hero ----------
hero_html = '''
<div style="text-align:center; padding: 28px 12px 8px;">
    <img src="https://images.unsplash.com/photo-1560179707-f14e90ef3623"
         alt="Wine glass" width="96"
         style="border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,0.35); margin-bottom:14px;">
    <h1 style="margin:0; color:#f5f5fb; letter-spacing:0.3px;">Stay &amp; Sip Finger Lakes</h1>
    <p style="margin:8px 0 0; color:#cfd2e0; font-size:17px;">
        Explore. Taste. Relax. Hand-picked stays, wineries, attractions, and wedding venues around Keuka, Seneca &amp; Cayuga.
    </p>
</div>
'''
st.markdown(hero_html, unsafe_allow_html=True)

# Quick-links row
c1, c2, c3, c4 = st.columns(4)
c1.link_button("🍓 Stays", "#stays", use_container_width=True)
c2.link_button("🍷 Wineries", "#wineries", use_container_width=True)
c3.link_button("🗺️ Attractions", "#attractions", use_container_width=True)
c4.link_button("💍 Venues", "#venues", use_container_width=True)
st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ---------- Sidebar controls ----------
st.sidebar.header("Search")
lake_opts = ["All", "Keuka", "Seneca", "Cayuga"]
lake = st.sidebar.selectbox("Lake", lake_opts, index=0)
budget = st.sidebar.slider("Max price per night (stays)", 100, 400, 300, step=10)
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Results"):
    st.cache_data.clear()
    st.rerun()
# ---------- Helpers ----------
def apply_lake(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if lake != "All" and "lake" in df.columns:
        return df[df["lake"] == lake]
    return df

def card_grid(df: pd.DataFrame, card_type: str):
    if df is None or df.empty:
        st.info("No results. Try broadening filters.")
        return
    cols_per_row = 3
    rows = [df.iloc[i:i+cols_per_row] for i in range(0, len(df), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, (_, item) in zip(cols, row.iterrows()):
            with col:
                img = item.get("image")
                if isinstance(img, str) and img:
                    st.image(img, use_column_width=True)

                title = item.get("name", card_type)
                subtitle = item.get("address", item.get("lake", ""))
                st.subheader(title)

                if card_type == "stay":
                    meta = f"{item.get('type','')} • {item.get('beds','?')} beds • up to {item.get('guests','?')} guests"
                    price = int(item.get("price_per_night", 0)) if pd.notnull(item.get("price_per_night", None)) else 0
                    st.markdown(f"**${price}/night** • {meta}")
                    tags = ", ".join(item.get("tags", []))
                    if tags:
                        st.caption(tags)

                elif card_type == "winery":
                    bits = []
                    if item.get("tasting"): bits.append("Tastings")
                    if item.get("tour"): bits.append("Tours")
                    st.markdown(", ".join(bits))
                    st.caption(item.get("notes", ""))

                elif card_type == "attraction":
                    st.markdown(item.get("category", ""))
                    st.caption(item.get("notes", ""))

                elif card_type == "venue":
                    st.markdown(f"{item.get('type','')} • up to {item.get('capacity','?')} guests")
                    st.caption(item.get("notes",""))

                if subtitle:
                    st.caption(subtitle)

                link = item.get("link", "")
                if link:
                    st.link_button("View details / Book", link, use_container_width=True)

# ---------- Modern tabs ----------
st.markdown(
    """
    <style>
      /* tighten spacing and give cards a little lift */
      .element-container:has(.stImage) { margin-bottom: 0.25rem; }
      .stButton>button { border-radius: 12px; padding: 0.5rem 0.75rem; }
      .stTabs [data-baseweb="tab-list"] { gap: .5rem; }
      .stTabs [data-baseweb="tab"] {
        background: #111827; border-radius: 12px; padding: .6rem 1rem; font-weight: 600;
        border: 1px solid rgba(255,255,255,.06);
      }
      .stTabs [aria-selected="true"] {
        background: #1f2937; border-color: rgba(155,135,245,.6);
      }
    </style>
    """,
    unsafe_allow_html=True
)

stays_tab, wineries_tab, attractions_tab, venues_tab, map_tab, itineraries_tab = st.tabs(
    ["🍓 Stays", "🍷 Wineries", "🗺️ Attractions", "💍 Wedding Venues", "🧭 Map", "🧳 Itineraries"]
)

# --- Stays ---
with stays_tab:
    st.markdown("<a name='stays'></a>", unsafe_allow_html=True)
    df = apply_lake(stays_df)
    if not df.empty and "price_per_night" in df.columns:
        df = df[df["price_per_night"] <= budget]
    type_opts = ["All"] + (sorted(df["type"].dropna().unique().tolist()) if "type" in df.columns and not df.empty else [])
    c1, c2 = st.columns([1,2])
    with c1:
        tsel = st.selectbox("Type", type_opts, index=0)
    with c2:
        st.caption(f"Filtering: Lake = **{lake}**, Max ${budget}/night")
    if tsel != "All" and not df.empty:
        df = df[df["type"] == tsel]
    card_grid(df, "stay")

# --- Wineries ---
with wineries_tab:
    st.markdown("<a name='wineries'></a>", unsafe_allow_html=True)
    df = apply_lake(wineries_df)
    c1, c2 = st.columns([1,2])
    with c1:
        only_tastings = st.checkbox("Show places with tastings", value=False)
    with c2:
        st.caption(f"Filtering: Lake = **{lake}**")
    if only_tastings and not df.empty:
        df = df[df.get("tasting", False) == True]
    card_grid(df, "winery")

# --- Attractions ---
with attractions_tab:
    st.markdown("<a name='attractions'></a>", unsafe_allow_html=True)
    df = apply_lake(attr_df)
    cat_opts = ["All"] + (sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns and not df.empty else [])
    c1, c2 = st.columns([1,2])
    with c1:
        csel = st.selectbox("Category", cat_opts, index=0)
    with c2:
        st.caption(f"Filtering: Lake = **{lake}**")
    if csel != "All" and not df.empty:
        df = df[df["category"] == csel]
    card_grid(df, "attraction")

# --- Wedding Venues ---
with venues_tab:
    st.markdown("<a name='venues'></a>", unsafe_allow_html=True)
    df = apply_lake(venues_df)
    c1, c2 = st.columns([1,2])
    with c1:
        min_cap = st.slider("Min capacity", 50, 300, 100, step=25)
    with c2:
        st.caption(f"Filtering: Lake = **{lake}**, Capacity ≥ **{min_cap}**")
    if not df.empty and "capacity" in df.columns:
        df = df[df["capacity"] >= min_cap]
    card_grid(df, "venue")

# --- Map ---
with map_tab:
    st.subheader("All Listings Map")
    combined = []
    for dataset, ctype in [
        (stays_df, "Stay"),
        (wineries_df, "Winery"),
        (attr_df, "Attraction"),
        (venues_df, "Wedding Venue"),
    ]:
        d = apply_lake(dataset).copy()
        if not d.empty and {"lat", "lng"}.issubset(d.columns):
            d["ctype"] = ctype
            combined.append(d[["name", "lat", "lng", "ctype", "lake"]])
    if combined:
        mdf = pd.concat(combined, ignore_index=True)
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v11",
                initial_view_state=pdk.ViewState(latitude=42.6, longitude=-77.1, zoom=8, pitch=0),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=mdf.rename(columns={"lng": "lon"}),
                        get_position="[lon, lat]",
                        get_radius=800,
                        pickable=True,
                    )
                ],
                tooltip={"text": "{name}\n{ctype} • {lake} Lake"},
            )
        )
    else:
        st.info("No locations to show.")

# --- Itineraries ---
with itineraries_tab:
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


# ---------- Load datasets ----------
stays_df     = safe_load("data/stays.json")
wineries_df  = safe_load("data/wineries.json")
attr_df      = safe_load("data/attractions.json")
venues_df    = safe_load("data/wedding_venues.json")
itin_df      = safe_load("data/itineraries.json")

# ---------- Helpers ----------
def apply_lake(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if lake != "All" and "lake" in df.columns:
        return df[df["lake"] == lake]
    return df

def card_grid(df: pd.DataFrame, card_type: str):
    if df is None or df.empty:
        st.info("No results. Try broadening filters.")
        return
    cols_per_row = 3
    rows = [df.iloc[i:i+cols_per_row] for i in range(0, len(df), cols_per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, (_, item) in zip(cols, row.iterrows()):
            with col:
                img = item.get("image")
                if isinstance(img, str) and img:
                    st.image(img, use_column_width=True)

                title = item.get("name", card_type)
                subtitle = item.get("address", item.get("lake", ""))
                st.subheader(title)

                if card_type == "stay":
                    meta = f"{item.get('type','')} • {item.get('beds','?')} beds • up to {item.get('guests','?')} guests"
                    price = int(item.get("price_per_night", 0)) if pd.notnull(item.get("price_per_night", None)) else 0
                    st.markdown(f"**${price}/night** • {meta}")
                    tags = ", ".join(item.get("tags", []))
                    if tags:
                        st.caption(tags)

                elif card_type == "winery":
                    bits = []
                    if item.get("tasting"): bits.append("Tastings")
                    if item.get("tour"): bits.append("Tours")
                    st.markdown(", ".join(bits))
                    st.caption(item.get("notes", ""))

                elif card_type == "attraction":
                    st.markdown(item.get("category", ""))
                    st.caption(item.get("notes", ""))

                elif card_type == "venue":
                    st.markdown(f"{item.get('type','')} • up to {item.get('capacity','?')} guests")
                    st.caption(item.get("notes",""))

                if subtitle:
                    st.caption(subtitle)

                link = item.get("link", "")
                if link:
                    st.link_button("View details / Book", link, use_container_width=True)

# ---------- Views ----------
# Stays
if view == "Stays":
    st.markdown("<a name='stays'></a>", unsafe_allow_html=True)
    df = apply_lake(stays_df)
    if not df.empty and "price_per_night" in df.columns:
        df = df[df["price_per_night"] <= budget]
    type_opts = ["All"] + (sorted(df["type"].dropna().unique().tolist()) if "type" in df.columns and not df.empty else [])
    tsel = st.selectbox("Type", type_opts, index=0)
    if tsel != "All" and not df.empty:
        df = df[df["type"] == tsel]
    card_grid(df, "stay")

# Wineries
elif view == "Wineries & Distilleries":
    st.markdown("<a name='wineries'></a>", unsafe_allow_html=True)
    df = apply_lake(wineries_df)
    only_tastings = st.checkbox("Show places with tastings", value=False)
    if only_tastings and not df.empty:
        df = df[df.get("tasting", False) == True]
    card_grid(df, "winery")

# Attractions
elif view == "Attractions":
    st.markdown("<a name='attractions'></a>", unsafe_allow_html=True)
    df = apply_lake(attr_df)
    cat_opts = ["All"] + (sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns and not df.empty else [])
    csel = st.selectbox("Category", cat_opts, index=0)
    if csel != "All" and not df.empty:
        df = df[df["category"] == csel]
    card_grid(df, "attraction")

# Wedding Venues
elif view == "Wedding Venues":
    st.markdown("<a name='venues'></a>", unsafe_allow_html=True)
    df = apply_lake(venues_df)
    min_cap = st.slider("Min capacity", 50, 300, 100, step=25)
    if not df.empty and "capacity" in df.columns:
        df = df[df["capacity"] >= min_cap]
    card_grid(df, "venue")

# Map
elif view == "Map":
    st.subheader("All Listings Map")
    combined = []
    for dataset, ctype in [
        (stays_df, "Stay"),
        (wineries_df, "Winery"),
        (attr_df, "Attraction"),
        (venues_df, "Wedding Venue"),
    ]:
        d = apply_lake(dataset).copy()
        if not d.empty and {"lat", "lng"}.issubset(d.columns):
            d["ctype"] = ctype
            combined.append(d[["name", "lat", "lng", "ctype", "lake"]])
    if combined:
        mdf = pd.concat(combined, ignore_index=True)
        st.pydeck_chart(
            pdk.Deck(
                map_style="mapbox://styles/mapbox/dark-v11",
                initial_view_state=pdk.ViewState(latitude=42.6, longitude=-77.1, zoom=8, pitch=0),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=mdf.rename(columns={"lng": "lon"}),
                        get_position="[lon, lat]",
                        get_radius=800,
                        pickable=True,
                    )
                ],
                tooltip={"text": "{name}\n{ctype} • {lake} Lake"},
            )
        )
    else:
        st.info("No locations to show.")

# Itineraries
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
                st.table(stays_df[stays_df["id"].isin(row["stays"])][["name", "address", "price_per_night"]])
                st.write("**Wineries**")
                st.table(wineries_df[wineries_df["id"].isin(row["wineries"])][["name", "address"]])
                st.write("**Attractions**")
                st.table(attr_df[attr_df["id"].isin(row.get("attractions", []))][["name", "address"]])

# ---------- Footer ----------
st.markdown("---")

footer_html = '''
<div style="display:flex; gap:16px; flex-wrap:wrap; align-items:center; justify-content:center; padding:10px 6px; color:#bfc3d6; font-size:14px;">
  <span>&copy; {year} Stay &amp; Sip Finger Lakes</span>
  <span>&bull;</span>
  <a href="mailto:hello@stayandsipflx.com" style="color:#cfd2e0; text-decoration:none;">Contact</a>
  <span>&bull;</span>
  <a href="https://maps.google.com/?q=Keuka+Lake+NY" target="_blank" style="color:#cfd2e0; text-decoration:none;">Map: Keuka Lake</a>
  <span>&bull;</span>
  <a href="https://www.instagram.com/" target="_blank" style="color:#cfd2e0; text-decoration:none;">Instagram</a>
  <span>&bull;</span>
  <a href="#" style="color:#cfd2e0; text-decoration:none;">Privacy</a>
</div>
<div style="text-align:center; color:#9aa0b8; font-size:12px; padding-bottom:12px;">
  Affiliate disclosure: We may earn a commission when you book via links on this site. Thanks for supporting local guides.
</div>
'''.format(year=pd.Timestamp.today().year)

st.markdown(footer_html, unsafe_allow_html=True)

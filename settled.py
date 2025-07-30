import streamlit as st
from rapidfuzz import process
import overpy
from geopy.geocoders import Nominatim
import math
import pandas as pd
import random

# Geolocator instance
geolocator = Nominatim(user_agent="settled_app", timeout=5)

# Haversine function to compute distance between two points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in KM
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Fetch and filter restaurants
def fetch_restaurants(city, cuisine_a, cuisine_b, radius_km):
    try:
        location = geolocator.geocode(city)
        if not location:
            return [], [], [], []

        center_lat, center_lon = location.latitude, location.longitude

        api = overpy.Overpass()
        query = f"""
        [out:json];
        (
          node["amenity"="restaurant"](around:{int(radius_km)*1000},{center_lat},{center_lon});
          way["amenity"="restaurant"](around:{int(radius_km)*1000},{center_lat},{center_lon});
          relation["amenity"="restaurant"](around:{int(radius_km)*1000},{center_lat},{center_lon});
        );
        out center tags;
        """
        result = api.query(query)

        cuisine_list = set()
        restaurants = []

        for el in result.nodes + result.ways + result.relations:
            tags = el.tags.get("cuisine", "")
            name = el.tags.get("name", "Unnamed")
            tags_list = tags.split(";")
            cuisine_list.update(tags_list)

            lat = getattr(el, "lat", getattr(el, "center_lat", None))
            lon = getattr(el, "lon", getattr(el, "center_lon", None))
            if lat is None or lon is None:
                continue

            # Extract address from tags
            addr_parts = [
                el.tags.get("addr:housenumber", ""),
                el.tags.get("addr:street", ""),
                el.tags.get("addr:suburb", ""),
                el.tags.get("addr:city", ""),
            ]
            address = ", ".join([part for part in addr_parts if part])

            restaurants.append({
                "Name": name,
                "Cuisine(s)": ', '.join(tags_list),
                "Address": address if address else "N/A",
                "Latitude": lat,
                "Longitude": lon
            })

        matched_cuisine_a = process.extractOne(cuisine_a, cuisine_list)[0] if cuisine_a else None
        matched_cuisine_b = process.extractOne(cuisine_b, cuisine_list)[0] if cuisine_b else None

        filtered = [r for r in restaurants if 
                    (matched_cuisine_a and matched_cuisine_a.lower() in r["Cuisine(s)"].lower()) or 
                    (matched_cuisine_b and matched_cuisine_b.lower() in r["Cuisine(s)"].lower())]

        return cuisine_list, matched_cuisine_a, matched_cuisine_b, filtered[:5]

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return [], None, None, []


# PAGE SETUP
st.set_page_config(page_title="Settled 🍜", layout="centered")

st.markdown("""
<style>
/* General layout and dark theme */
html, body {
    background: linear-gradient(180deg, #000000, #0a0f35);
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
.stApp {
    background: 
        linear-gradient(135deg, #120505 60%, #9c0606 100%);
}

/* Input box styling */
input[type="text"] {
    background-color: #000000 !important;
    color: white !important;
    border: 1px solid #FF4B4B !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}

/* Center align buttons */
div.stButton {
    text-align: center;
}

/* Wrapper for title + form */
.form-card {
    background: rgba(255, 255, 255, 0.04);
    padding: 1.5rem;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.07);
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    margin-bottom: 2rem;
}

/* Transparent button with hover */
div.stButton > button {
    background-color: transparent;
    color: #FF4B4B;
    border: 2px solid #FF4B4B;
    border-radius: 10px;
    padding: 0.5em 1.2em;
    font-size: 16px;
    font-weight: 600;
    transition: 0.3s ease-in-out;
    box-shadow: none;
}

div.stButton > button:hover {
    background-color: #FF4B4B;
    color: black;
    transform: translateY(-2px);
}

/* Title styling */
.custom-title-container {
    text-align: center;
    margin-bottom: 1rem;
}

.custom-title {
    font-family: 'Beckan', sans-serif;
    font-size: 64px;
    background: linear-gradient(45deg, #ff4b4b, #cc0000);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}

.tagline {
    font-size: 16px;
    color: #aaa;
    margin-top: 4px;
}

/* Result card styling */
.result-card {
    background: rgba(255, 255, 255, 0.04);
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.result-card h4 {
    margin: 0;
    color: #ff4b4b;
}

.result-card p {
    margin: 0.3rem 0;
    color: #e0e0e0;
}

/* Slider accent color */
input[type="range"]::-webkit-slider-thumb {
    background: #FF4B4B;
}
input[type="range"]::-moz-range-thumb {
    background: #FF4B4B;
}
input[type="range"]::-ms-thumb {
    background: #FF4B4B;
}
input[type="range"]::-webkit-slider-runnable-track {
    background: linear-gradient(to right, #FF4B4B 0%, #444 0%);
}
</style>
<link href="https://fonts.cdnfonts.com/css/beckan" rel="stylesheet">
""", unsafe_allow_html=True)

# Wrap title and form into a styled card
st.markdown("""
<div class="form-card">
    <div class="custom-title-container">
        <div class="custom-title">🍽️ Settled</div>
        <div class="tagline">Let us decide for you!</div>
    </div>
""", unsafe_allow_html=True)

# Start of form (inside same div)
city = st.text_input("📍 Enter your city or neighborhood", "")
col1, col2 = st.columns(2)
with col1:
    cuisine_a = st.text_input("👤 Person A's preferred cuisine", "")
with col2:
    cuisine_b = st.text_input("👤 Person B's preferred cuisine", "")
radius_km = st.slider("📏 Search radius (km)", 1, 10, 3)

st.markdown("</div>", unsafe_allow_html=True)  # close form-card div

# --- SESSION STATE INIT ---
if "random_pick" not in st.session_state:
    st.session_state.random_pick = None
if "results_ready" not in st.session_state:
    st.session_state.results_ready = False

# --- BUTTON TO FETCH RESTAURANTS ---
if st.button("Find Restaurants"):
    cuisine_list, matched_a, matched_b, results = fetch_restaurants(city, cuisine_a, cuisine_b, radius_km)

    st.session_state.results_ready = True
    st.session_state.random_pick = None
    st.session_state.results = results

    if cuisine_list:
        st.markdown("#### 🍴 Unique cuisine types found in area:")
        st.write(", ".join(sorted(cuisine_list)))

    st.markdown(f"✅ **Matched for Person A:** `{matched_a}`" if matched_a else "❌ No match for Person A")
    st.markdown(f"✅ **Matched for Person B:** `{matched_b}`" if matched_b else "❌ No match for Person B")

# --- DISPLAY RESULTS ---
if st.session_state.results_ready and st.session_state.results:
    st.markdown("### 🏆 Top Matching Restaurants")

    for r in st.session_state.results:
        st.markdown(f"""
        <div class="result-card">
            <h4>📌 {r['Name']}</h4>
            <p>🍽️ Cuisine(s): {r['Cuisine(s)']}</p>
            <p>🗺️ Address: {r['Address']}</p>
        </div>
        """, unsafe_allow_html=True)

# --- SETTLE RANDOM PICK ---
st.markdown("## 🎲 Still undecided?")
if st.button("🎯 Settle"):
    st.session_state.random_pick = random.choice(st.session_state.results)

if st.session_state.random_pick:
    r = st.session_state.random_pick

    st.markdown(f"""
    <div style="
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    ">
        <h3 style="color: #ffcc70; margin-bottom: 0.5rem;">✅ Settled Pick: {r['Name']}</h3>
        <p><strong>📍 Address:</strong> {r['Address']}</p>
        <p><strong>🍽️ Cuisine:</strong> {r['Cuisine(s)']}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔁 Do it again"):
        st.session_state.random_pick = random.choice(st.session_state.results)

import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DMS to Decimal Converter", layout="centered")

st.title("📍 DMS → Decimal Degrees Converter")
st.write("Convert coordinates from Degrees Minutes Seconds (DMS) format to Decimal Degrees (DD).")


# --- Helper: Convert one DMS string to Decimal Degrees
def dms_to_decimal(dms_str):
    """
    Converts DMS like '35°45\'30"N' or '82 18 45 W' into decimal degrees.
    """
    if not isinstance(dms_str, str):
        return None

    # Match degrees, minutes, seconds, and direction (N/S/E/W)
    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\D+(\d+(?:\.\d+)?)?\D*(\d+(?:\.\d+)?)?\D*([NSEW])",
        re.IGNORECASE
    )
    match = pattern.search(dms_str.strip().replace("’", "'").replace("`", "'"))
    if not match:
        return None

    deg = float(match.group(1))
    mins = float(match.group(2)) if match.group(2) else 0
    secs = float(match.group(3)) if match.group(3) else 0
    direction = match.group(4).upper()

    decimal = deg + mins / 60 + secs / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return round(decimal, 6)


# --- Extract coordinate pairs from line
def extract_pair_from_line(line):
    """
    Extracts a latitude/longitude pair from one line of text.
    Handles commas, spaces, and mixed formats.
    """
    # Split line into all DMS-like components
    tokens = re.findall(r"\d+[^NSEW\d]*[NSEW]", line.replace("’", "'").replace("`", "'"), re.IGNORECASE)
    if len(tokens) >= 2:
        return tokens[0], tokens[1]
    # Try splitting manually if above fails
    parts = [p.strip() for p in re.split(r'[,;/]', line) if p.strip()]
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None


# --- UI Input Section
st.subheader("Input Coordinates")

input_method = st.radio("Choose input method:", ["Paste DMS list", "Upload CSV"])

coords = []

if input_method == "Paste DMS list":
    text_input = st.text_area(
        "Paste DMS coordinates (one per line or separated by commas/spaces):",
        height=200,
        placeholder=(
            "Examples:\n"
            "35°45'30\"N 82°18'45\"W\n"
            "35 45 30 N, 82 18 45 W\n"
            "35°45'N 82°18'W"
        )
    )

    if text_input:
        lines = [line.strip() for line in text_input.splitlines() if line.strip()]
        for line in lines:
            lat, lon = extract_pair_from_line(line)
            if lat and lon:
                coords.append((lat, lon))

elif input_method == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a CSV with DMS coordinates", type=["csv"])
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(df_uploaded.head())

        option_type = st.radio("Coordinate format:", ["Two columns (Lat/Lon)", "Single column (Combined)"])

        if option_type == "Two columns (Lat/Lon)":
            lat_col = st.selectbox("Select Latitude column", df_uploaded.columns)
            lon_col = st.selectbox("Select Longitude column", df_uploaded.columns)
            coords = df_uploaded[[lat_col, lon_col]].dropna().values.tolist()

        else:
            combo_col = st.selectbox("Select Combined Coordinate column", df_uploaded.columns)
            for val in df_uploaded[combo_col].dropna().tolist():
                lat, lon = extract_pair_from_line(str(val))
                if lat and lon:
                    coords.append((lat, lon))


# --- Convert and Output
if st.button("Convert to Decimal Degrees"):
    if not coords:
        st.warning("⚠️ No coordinates detected. Please check your input format.")
    else:
        results = []
        for lat_dms, lon_dms in coords:
            lat_dd = dms_to_decimal(lat_dms)
            lon_dd = dms_to_decimal(lon_dms)
            results.append({"Latitude": lat_dd, "Longitude": lon_dd})

        df = pd.DataFrame(results)
        st.success(f"✅ Conversion complete! {len(df)} coordinates processed.")
        st.dataframe(df)

        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="decimal_coordinates.csv",
            mime="text/csv"
        )

        # Optional: plot on map
        if st.checkbox("Show coordinates on map"):
            st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))

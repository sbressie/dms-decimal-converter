import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DMS to Decimal Converter", layout="centered")

st.title("📍 DMS → Decimal Degrees Converter")
st.write("Convert coordinates from Degrees Minutes Seconds (DMS) to Decimal Degrees (DD).")

# --- Helper function to convert DMS to decimal degrees
def dms_to_decimal(dms_str):
    """
    Converts a DMS string like '35°45\'30"N' or '82°18\'45"W' to decimal degrees.
    """
    pattern = re.compile(
        r"""(?P<deg>\d+)[°\s]?      # degrees
            (?P<min>\d+)?['\s]?     # minutes
            (?P<sec>\d+(?:\.\d+)?)?["\s]?   # seconds (optional)
            (?P<dir>[NSEW])         # direction
        """, re.VERBOSE
    )
    match = pattern.search(str(dms_str).strip())
    if not match:
        return None

    parts = match.groupdict(default='0')
    deg = float(parts['deg'])
    mins = float(parts['min'])
    secs = float(parts['sec'])
    direction = parts['dir']

    decimal = deg + mins / 60 + secs / 3600
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# --- Extract coordinate pairs from text line
def extract_pair_from_line(line):
    """
    Detects and extracts a latitude/longitude pair from a line of text.
    Supports formats like:
      - 35°45'30"N 82°18'45"W
      - 35°45'30"N, 82°18'45"W
    """
    pattern = re.compile(
        r'(\d+°\s*\d*\'?\s*\d*"?\s*[NS])[, ]+\s*(\d+°\s*\d*\'?\s*\d*"?\s*[EW])',
        re.IGNORECASE
    )
    match = pattern.search(line)
    if match:
        return match.group(1), match.group(2)
    return None, None


# --- Input section
st.subheader("Input Coordinates")

input_method = st.radio("Choose input method:", ["Paste DMS list", "Upload CSV"])

coords = []

if input_method == "Paste DMS list":
    text_input = st.text_area(
        "Paste DMS coordinates (one per line or separated by commas/spaces):",
        height=200,
        placeholder=(
            'Examples:\n'
            '35°45\'30"N, 82°18\'45"W\n'
            '35°46\'00"N 82°19\'00"W\n'
            '35°45\'N 82°18\'W'
        )
    )

    if text_input:
        lines = [line.strip() for line in text_input.splitlines() if line.strip()]
        for line in lines:
            # Try to detect pair automatically
            lat, lon = extract_pair_from_line(line)
            if not lat or not lon:
                # Try splitting manually by comma if not detected
                parts = [p.strip() for p in re.split(r'[,/]', line) if p.strip()]
                if len(parts) == 2:
                    lat, lon = parts
            if lat and lon:
                coords.append((lat, lon))

elif input_method == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a CSV file containing DMS coordinates", type=["csv"])
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded file:")
        st.dataframe(df_uploaded.head())

        # Automatically detect column(s)
        st.write("Select the columns that contain coordinates:")
        col_options = list(df_uploaded.columns)
        option_type = st.radio("Coordinate format:", ["Two columns (Lat/Lon)", "Single column (combined)"])

        if option_type == "Two columns (Lat/Lon)":
            lat_col = st.selectbox("Select Latitude column", col_options)
            lon_col = st.selectbox("Select Longitude column", col_options)
            coords = df_uploaded[[lat_col, lon_col]].values.tolist()
        else:
            combo_col = st.selectbox("Select Combined Coordinate column", col_options)
            for val in df_uploaded[combo_col].dropna().tolist():
                lat, lon = extract_pair_from_line(str(val))
                if lat and lon:
                    coords.append((lat, lon))


# --- Process and output
if st.button("Convert to Decimal Degrees"):
    if not coords:
        st.warning("Please enter or upload coordinates first.")
    else:
        results = []
        for lat_dms, lon_dms in coords:
            lat_dd = dms_to_decimal(lat_dms)
            lon_dd = dms_to_decimal(lon_dms)
            results.append({"Latitude": lat_dd, "Longitude": lon_dd})

        df = pd.DataFrame(results)
        st.success("✅ Conversion complete!")
        st.dataframe(df)

        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="decimal_coordinates.csv",
            mime="text/csv"
        )

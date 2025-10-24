import streamlit as st
import pandas as pd
import re
from io import StringIO

# --- Core Conversion Logic ---

def dms_to_dd(dms_str):
    """
    Parses a Degrees-Minutes-Seconds (DMS) string and converts it to Decimal Degrees (DD).
    Handles various formats (e.g., 40° 44' 55" N, 40 44 55 N, 40.7486, 40-44-55N).
    """
    dms_str = str(dms_str).strip().replace(',', '.').upper()

    # 1. Check for pure decimal degree format first (e.g., '40.7486', '25.0')
    try:
        return float(dms_str)
    except ValueError:
        pass

    # 2. Use regex to extract numbers and direction
    # This finds all floating point numbers and the single direction letter (N, S, E, W)
    parts = re.findall(r"[\d.]+|[NSEW]", dms_str)

    if not parts:
        raise ValueError(f"Could not find coordinate components in: {dms_str}")

    # Separate numerical components from the direction
    nums = [float(p) for p in parts if p not in ('N', 'S', 'E', 'W')]
    direction = next((p for p in parts if p in ('N', 'S', 'E', 'W')), None)

    D = nums[0] if len(nums) > 0 else 0
    M = nums[1] if len(nums) > 1 else 0
    S = nums[2] if len(nums) > 2 else 0

    # Calculate Decimal Degrees
    dd = D + (M / 60) + (S / 3600)

    # Apply sign based on direction
    if direction in ('S', 'W'):
        dd *= -1

    return dd

def convert_dataframe(df, lat_col, lon_col):
    """Applies DMS to DD conversion to the specified columns of a DataFrame."""
    results = []
    errors = []

    for index, row in df.iterrows():
        try:
            dd_lat = dms_to_dd(row[lat_col])
            dd_lon = dms_to_dd(row[lon_col])
            results.append({
                'Original Latitude': row[lat_col],
                'Original Longitude': row[lon_col],
                'Decimal Latitude': round(dd_lat, 6),
                'Decimal Longitude': round(dd_lon, 6)
            })
        except Exception as e:
            errors.append(f"Row {index + 1}: Could not process ({row[lat_col]}, {row[lon_col]}). Error: {e}")

    return pd.DataFrame(results), errors

# --- Streamlit Application Layout ---

st.set_page_config(
    page_title="DMS to DD Converter",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌎 DMS to Decimal Degrees Converter")
st.markdown("Use this tool to convert Degrees, Minutes, Seconds (DMS) formats into standard Decimal Degrees (DD).")

# Use tabs for clean separation of input modes
tab1, tab2 = st.tabs(["Individual Pair Conversion", "CSV File Conversion"])

# --- Tab 1: Individual Conversion ---
with tab1:
    st.header("Single Coordinate Pair")
    st.markdown("Enter latitude and longitude in any standard DMS format (e.g., `40 44 55 N` or `40° 44' 55\"`).")

    col_lat, col_lon = st.columns(2)
    lat_input = col_lat.text_input("Latitude (DMS or DD)", value="40 44 55 N")
    lon_input = col_lon.text_input("Longitude (DMS or DD)", value="73 59 11 W")

    if st.button("Convert Individual Pair"):
        if lat_input and lon_input:
            try:
                dd_lat = dms_to_dd(lat_input)
                dd_lon = dms_to_dd(lon_input)

                st.success("Conversion Successful!")
                st.info(f"**Original Coordinates:** ({lat_input}, {lon_input})")
                
                st.metric(label="Decimal Latitude", value=f"{dd_lat:.6f}")
                st.metric(label="Decimal Longitude", value=f"{dd_lon:.6f}")
                
                st.markdown("---")
                st.subheader("Output List Format:")
                st.code(f"[{dd_lat:.6f}, {dd_lon:.6f}]")

            except ValueError as e:
                st.error(f"Error converting input: {e}")
        else:
            st.warning("Please enter both Latitude and Longitude.")

# --- Tab 2: CSV Conversion ---
with tab2:
    st.header("Bulk Conversion via CSV File")
    st.markdown("Upload a CSV file containing your coordinates. It must have separate columns for Latitude and Longitude.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.subheader("1. Select Coordinate Columns")

            available_cols = df.columns.tolist()
            
            # Use selectboxes to allow the user to map their columns
            lat_col_name = st.selectbox(
                "Select Latitude Column",
                available_cols,
                index=0 if 'latitude' in [c.lower() for c in available_cols] else 0
            )
            
            lon_col_name = st.selectbox(
                "Select Longitude Column",
                available_cols,
                index=1 if 'longitude' in [c.lower() for c in available_cols] else 1
            )

            if st.button("Convert CSV Data"):
                with st.spinner('Converting coordinates...'):
                    # Convert the data
                    df_converted, errors = convert_dataframe(df, lat_col_name, lon_col_name)

                st.subheader("2. Converted Decimal Coordinates")
                st.dataframe(df_converted, use_container_width=True)

                if errors:
                    st.error("Conversion Errors:")
                    for error in errors:
                        st.code(error)

                # Download button
                @st.cache_data
                def convert_df_to_csv(df):
                    # IMPORTANT: Cache the conversion to prevent re-running on every page load
                    return df.to_csv(index=False).encode('utf-8')

                csv_data = convert_df_to_csv(df_converted)

                st.download_button(
                    label="Download Converted CSV",
                    data=csv_data,
                    file_name='converted_coordinates.csv',
                    mime='text/csv',
                    help="Click to download the resulting DataFrame as a CSV file."
                )
                
                # Show list output format
                st.markdown("---")
                st.subheader("Output List Format (First 5 Rows):")
                list_output = df_converted[['Decimal Latitude', 'Decimal Longitude']].head(5).values.tolist()
                st.code(list_output)

        except Exception as e:
            st.error(f"An error occurred during file processing or conversion: {e}")

# --- Instructions in Sidebar ---
with st.sidebar:
    st.header("How to Run the App")
    st.markdown("""
    1.  **Save** the code above as `dms_converter.py`.
    2.  **Install** Streamlit and pandas:
        ```bash
        pip install streamlit pandas
        ```
    3.  **Run** the app from your terminal:
        ```bash
        streamlit run dms_converter.py
        ```
    """)
    st.markdown("---")
    st.header("Supported Formats")
    st.markdown("""
    The converter can handle the following common formats:
    * `40 44 55 N, 73 59 11 W`
    * `40° 44' 55.00" N`
    * `40-44-55N, 73.9863` (Mixed format)
    * Pure Decimal Degrees (`40.7486`)
    """)
    

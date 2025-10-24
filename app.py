import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="DMS to Decimal Converter", layout="centered")

st.title("📍 DMS → Decimal Degrees Converter")
st.write("Convert coordinates from Degrees Minutes Seconds (DMS) format to Decimal Degrees (DD).")

# --- Normalize Unicode and punctuation for consistent parsing
def normalize_dms_string(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    # Normalize Unicode primes and similar punctuation
    s = s.replace("′", "'").replace("″", '"')
    s = s.replace("’", "'").replace("`", "'")
    # Replace multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s


# --- Convert one DMS string to Decimal Degrees
def dms_to_decimal(dms_str):
    """
    Converts DMS like:
      - 35°45'30"N
      - 82 18 45 W
      - 31°52′40.24″N
    into decimal degrees.
    """
    if not isinstance(dms_str, str) or dms_str.strip() == "":
        return None

    dms_str = normalize_dms_string(dms_str)

    # Match DMS pattern robustly
    pattern = re.compile(
        r"(\d+(?:\.\d+)?)\D*"   # degrees
        r"(\d+(?:\.\d+)?)?\D*"  # minutes
        r"(\d+(?:\.\d+)?)?\D*"  # seconds
        r"([NSEW])",            # direction
        re.IGNORECASE,
    )
    match = pattern.search(dms_str)
    if not match:
        return None

    deg = float(match.group(1))
    mins = float(match.group(2)) if match.group(2) else 0
    secs = float(match.group(3)) if match.group(3) else 0
    direction = match.group(4).upper()

    decimal = deg + mins / 60 + secs / 3600
    if direction in ["S", "W"]:
        decimal *= -1

    return round(decimal, 6)


# --- Extract coordinate pairs from line
def extract_pair_from_line(line):
    """
    Extracts a latitude/longitude pair from one line of text.
    Handles commas, spaces, and Unicode DMS symbols.
    """
    line = normalize_dms_string(line)
    tokens = re.findall(r"\d+[^NSEW\d]*[NSEW]", line, re.IGNORECASE)
    if len(tokens) >= 2:
        return tokens[0], tokens[1]
    # fallback to comma/space split
    parts = [p.strip() for p in re.split(r"[,;/]", line) if p.strip()]
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None


# --- Streamlit Input
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
            "31°52′40.24″N 35°26′46.24″E"
        ),
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
        st.write("Preview of uploa

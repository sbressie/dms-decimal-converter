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

import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs 
import cartopy.feature as cfeature  
import numpy as np
import plotly.express as px # <--- NEW INTERACTIVE LIBRARY

st.set_page_config(layout="wide", page_title="Climate Explorer Pro")

# --- 1. OPTIMIZED CACHING FUNCTIONS ---
@st.cache_resource
def get_dataset(file_path):
    """Caches the file connection without overloading RAM."""
    return xr.open_dataset(file_path)

# --- 2. FILE SCANNING & LOADING ---
st.title("🌍 PyClimaExplorer Dashboard")

current_folder = os.getcwd()
nc_files = [f for f in os.listdir(current_folder) if f.endswith('.nc')]

if nc_files:
    selected_filename = st.selectbox("Select a dataset:", nc_files)
    file_path = os.path.join(current_folder, selected_filename)

    # Initial metadata check
    ds_meta = xr.open_dataset(file_path)
    
    # Move the dictionary UP here so the dropdown can use it!
    friendly_names = {
        't2m': '2 Metre Temperature (K)',
        'sd': 'Snow Depth (m)',
        'swvl1': 'Soil Moisture (m³/m³)',
        'tp': 'Total Precipitation (m)'
    }
    
    # The format_func translates 'sd' into 'Snow Depth' in the UI automatically
    variable = st.selectbox(
        "Select Climate Variable", 
        list(ds_meta.data_vars),
        format_func=lambda x: friendly_names.get(x, x)
    )

    # Access the variable directly without forcing it into RAM
    ds = get_dataset(file_path)
    data = ds[variable]
    
    clean_name = friendly_names.get(variable, variable)

    # Navigation Sidebar
    locations = {
        "Manual Selection": None,
        "Amazon Rainforest": {"lat": -3.4, "lon": -60.0},
        "Sahara Desert": {"lat": 23.4, "lon": 25.0},
        "Himalayas": {"lat": 28.0, "lon": 86.0},
        "Arctic Circle": {"lat": 66.5, "lon": 0.0}
    }
    st.sidebar.header("Navigation")
    selected_loc = st.sidebar.selectbox("Jump to Location Preset:", list(locations.keys()))
    st.sidebar.metric(label="Active Parameter", value=clean_name)

    #
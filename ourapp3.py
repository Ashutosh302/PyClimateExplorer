import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs 
import numpy as np

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
    variable = st.selectbox("Select Climate Variable", list(ds_meta.data_vars))

    # Access the variable directly without forcing it into RAM
    ds = get_dataset(file_path)
    data = ds[variable]

    friendly_names = {
        't2m': '2 Metre Temperature (K)',
        'sd': 'Snow Depth (m)',
        'swvl1': 'Volumetric Soil Water Layer 1 (m³/m³)',
        'tp': 'Total Precipitation (m)'
    }
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

    # --- 3. COORDINATE DETECTION ---
    lon_name = [c for c in data.coords if 'lon' in c.lower()][0]
    lat_name = [c for c in data.coords if 'lat' in c.lower()][0]
    time_coords = [c for c in data.coords if 'time' in c.lower() or c.lower() == 't']
    time_name = time_coords[0] if time_coords else None

    # --- 4. TIME LOGIC (MANUAL SLIDER) ---
    if time_name:
        num_steps = len(data[time_name])
        st.write("---")
        
        # Simple manual slider, no animation loop needed
        time_index = st.slider("Timeline Step", 0, num_steps - 1, 0)
            
        time_label = str(data[time_name].values[time_index])[:10]
        step_data = data.isel({time_name: time_index})
    else:
        time_index = 0
        time_label = "Static"
        step_data = data

    # Colormap Logic
    if variable == 'sd': cmap = plt.cm.Blues
    elif variable == 'swvl1': cmap = plt.cm.BrBG
    else: cmap = plt.cm.coolwarm

    # --- 5. DYNAMIC LOCATION TABS ---
    st.write("### 📍 Location-Specific Analysis")
    
    # We create a tab for every location in your dictionary
    tab_list = list(locations.keys())
    location_tabs = st.tabs(tab_list)

    lat_vals, lon_vals = data[lat_name].values, data[lon_name].values

    for i, tab in enumerate(location_tabs):
        with tab:
            loc_name = tab_list[i]
            
            if loc_name == "Manual Selection":
                st.info("Use the sliders below to explore any coordinate on Earth.")
                c1, c2 = st.columns(2)
                l_idx = c1.slider("Latitude", 0, len(lat_vals)-1, len(lat_vals)//2, key="man_lat")
                o_idx = c2.slider("Longitude", 0, len(lon_vals)-1, len(lon_vals)//2, key="man_lon")
            else:
                # Automatically find the index for the preset location
                target_lat = locations[loc_name]["lat"]
                target_lon = locations[loc_name]["lon"]
                l_idx = int(np.abs(lat_vals - target_lat).argmin())
                o_idx = int(np.abs(lon_vals - target_lon).argmin())
                st.success(f"Viewing Preset: {loc_name} ({lat_vals[l_idx]:.2f}°, {lon_vals[o_idx]:.2f}°)")

            # Fetch the data for this specific tab's location
            ts = data.isel({lat_name: l_idx, lon_name: o_idx}).load()

            if ts.isnull().all():
                st.warning("⚠️ No data at this coordinate (Ocean).")
            else:
                # Layout for this location's data
                col_graph, col_stats = st.columns([3, 1])
                
                with col_graph:
                   st.line_chart(ts.to_dataframe()[variable], width='stretch')
                
                with col_stats:
                    st.write("**Quick Stats**")
                    st.metric("Max", f"{ts.max().values:.2f}")
                    st.metric("Min", f"{ts.min().values:.2f}")
                    st.metric("Avg", f"{ts.mean().values:.2f}")

    # --- 6. GLOBAL VISUALIZATION SECTION ---
    with st.expander("🌍 Show Global Map", expanded=False):
        st.subheader(f"2D Map - {time_label}")
        
        # Draw the 2D map directly
        fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.coastlines()
        mesh = ax.pcolormesh(data[lon_name].values, data[lat_name].values, step_data.values,
                             transform=ccrs.PlateCarree(), cmap=cmap, rasterized=True)
        fig.colorbar(mesh, ax=ax, label=clean_name)
        st.pyplot(fig)
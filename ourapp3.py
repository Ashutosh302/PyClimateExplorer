import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs 
import cartopy.feature as cfeature  
import numpy as np
import plotly.express as px

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
    
    # FIXED: Changed 'sd' to 'sde' to match your exact file
    friendly_names = {
        't2m': '2 Metre Temperature (K)',
        'sde': 'Snow Depth (m)',
        'swvl1': 'Soil Moisture (m³/m³)',
        'tp': 'Total Precipitation (m)'
    }
    
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

    # --- 3. COORDINATE DETECTION ---
    lon_name = [c for c in data.coords if 'lon' in c.lower()][0]
    lat_name = [c for c in data.coords if 'lat' in c.lower()][0]
    time_coords = [c for c in data.coords if 'time' in c.lower() or c.lower() == 't']
    time_name = time_coords[0] if time_coords else None

    # --- 4. TIME LOGIC (MANUAL SLIDER) ---
    if time_name:
        num_steps = len(data[time_name])
        st.write("---")
        time_index = st.slider("Timeline Step", 0, num_steps - 1, 0)
        time_label = str(data[time_name].values[time_index])[:10]
        step_data = data.isel({time_name: time_index})
    else:
        time_index = 0
        time_label = "Static"
        step_data = data

    # --- 5. DYNAMIC LOCATION TABS ---
    st.write("### 📍 Location-Specific Analysis")
    
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
                target_lat = locations[loc_name]["lat"]
                target_lon = locations[loc_name]["lon"]
                l_idx = int(np.abs(lat_vals - target_lat).argmin())
                o_idx = int(np.abs(lon_vals - target_lon).argmin())
                st.success(f"Viewing Preset: {loc_name} ({lat_vals[l_idx]:.2f}°, {lon_vals[o_idx]:.2f}°)")

            ts = data.isel({lat_name: l_idx, lon_name: o_idx}).load()

            if ts.isnull().all():
                st.warning("⚠️ No data at this coordinate (Ocean).")
            else:
                col_graph, col_stats = st.columns([3, 1])
                with col_graph:
                   st.line_chart(ts.to_dataframe()[variable], width='stretch')
                with col_stats:
                    st.write("**Quick Stats**")
                    st.metric("Max", f"{ts.max().values:.2f}")
                    st.metric("Min", f"{ts.min().values:.2f}")
                    st.metric("Avg", f"{ts.mean().values:.2f}")

    # --- 6. INTERACTIVE GLOBAL MAPS (PLOTLY) WITH CRASH FIX ---
    with st.expander("🌍 Show Interactive Global Maps", expanded=True):
        st.info("💡 You can now scroll to zoom, drag to pan, and hover over the map to see exact data values!")
        
        with st.spinner("Rendering interactive globe (this takes a few seconds)..."):
            # --- THE FIX: DYNAMIC SUB-SAMPLING ---
            total_pixels = step_data.size
            max_safe_pixels = 5000 
            
            # Auto-calculate the skip factor so the browser NEVER freezes
            if total_pixels > max_safe_pixels:
                skip_factor = int(np.sqrt(total_pixels / max_safe_pixels))
            else:
                skip_factor = 1
                
            light_step_data = step_data.isel(
                {lat_name: slice(None, None, skip_factor), 
                 lon_name: slice(None, None, skip_factor)}
            )
            
            df = light_step_data.to_dataframe().reset_index().dropna()
            
            # FIXED: 'sde' instead of 'sd'
            if variable == 't2m': px_cmap = 'RdYlBu_r'
            elif variable == 'sde': px_cmap = 'Blues'
            elif variable == 'swvl1': px_cmap = 'BrBG'
            elif variable == 'tp': px_cmap = 'YlGnBu'
            else: px_cmap = 'Viridis'

            col_2d, col_3d = st.columns(2)
            
            with col_2d:
                st.subheader(f"2D Map - {time_label}")
                fig_2d = px.scatter_geo(
                    df, lat=lat_name, lon=lon_name, color=variable,
                    color_continuous_scale=px_cmap,
                    projection="natural earth",
                    opacity=0.8,
                    hover_name=variable
                )
                fig_2d.update_traces(marker=dict(size=4, symbol='square'))
                fig_2d.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_2d, use_container_width=True)
                
            with col_3d:
                st.subheader(f"3D Globe - {time_label}")
                fig_3d = px.scatter_geo(
                    df, lat=lat_name, lon=lon_name, color=variable,
                    color_continuous_scale=px_cmap,
                    projection="orthographic", 
                    opacity=0.8,
                    hover_name=variable
                )
                fig_3d.update_traces(marker=dict(size=4, symbol='square'))
                fig_3d.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_3d, use_container_width=True)

import os
import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs 
import numpy as np

st.set_page_config(layout="wide")



st.title("Climate Data Explorer Dashboard")


current_folder = os.getcwd()
nc_files = [f for f in os.listdir(current_folder) if f.endswith('.nc')]

if nc_files:
    selected_filename = st.selectbox("Select a dataset from your folder:", nc_files)
    file_path = os.path.join(current_folder, selected_filename)

    ds = xr.open_dataset(file_path,chunks={'time':1})

    st.write("Dataset variables:")
    
    variable = st.selectbox(
        "Select Climate Variable",
        list(ds.data_vars)
    )

    friendly_names = {
        't2m': 'Surface Temperature (K)',
        'sd': 'Global Snow Depth (m)',
        'swvl1': 'Topsoil Moisture (m³/m³)', # Friendly name for Layer 1
        'tp': 'Total Precipitation (m)'
    }
    # Get the clean name, or use the technical name if not in our list
    
    clean_name = friendly_names.get(variable, variable)
    
    # --- ADDED: LOCATION PRESETS ---
    locations = {
        "Manual Selection": None,
        "Amazon Rainforest": {"lat": -3.4, "lon": -60.0},
        "Sahara Desert": {"lat": 23.4, "lon": 25.0},
        "Himalayas": {"lat": 28.0, "lon": 86.0},
        "Arctic Circle": {"lat": 66.5, "lon": 0.0}
    }
    st.sidebar.header("Navigation")
    selected_loc = st.sidebar.selectbox("Jump to Location:", list(locations.keys()))
    st.sidebar.metric(label="Active Parameter", value=clean_name)
    data = ds[variable]

    # --- AUTO-DETECT COORDINATE NAMES ---
    # This finds the names even if they are 'longitude', 'nav_lon', etc.
    lon_name = [c for c in data.coords if 'lon' in c.lower()][0]
    lat_name = [c for c in data.coords if 'lat' in c.lower()][0]
    # ------------------------------------

    
    st.subheader(" Global Temperature Map")

    # --- AUTO-DETECT TIME NAME ---
    time_coords = [c for c in data.coords if 'time' in c.lower() or c.lower() == 't']
    time_name = time_coords[0] if time_coords else None
    
    if time_name:
        num_steps = len(data[time_name])
        if num_steps > 1:
            time_index = st.slider("Select Time Index", 0, num_steps - 1, 0)
            year = str(data[time_name].values[time_index])[:4]
        else:
            st.info("Note: This dataset contains only one time step.")
            time_index = 0
            year = str(data[time_name].values[0])[:4]
    else:
        time_index = 0
        year = "N/A"

    # Set Colormap based on variable
    if variable == 'sd':
        current_cmap = plt.cm.Blues
    elif variable == 'swvl1':
        current_cmap = plt.cm.BrBG
    else:
        current_cmap = plt.cm.coolwarm

        if variable == 'sd':
         current_cmap = plt.cm.Blues    # Blue for Snow
        elif variable == 'swvl1':
         current_cmap = plt.cm.BrBG     # Brown-to-Green for Soil Moisture
        else:
         current_cmap = plt.cm.coolwarm # Red-Blue for Temperature
           
    fig = plt.figure(figsize=(12,6))

    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.coastlines()

    mesh = ax.pcolormesh(
        data[lon_name].values, 
        data[lat_name].values, 
        data.isel({time_name: time_index}).values if time_name else data.values,
        transform=ccrs.PlateCarree(),
        cmap=current_cmap 
    )

    plt.colorbar(mesh, ax=ax, label=clean_name) 
    ax.set_title(f"Global Map - {year}")
    st.pyplot(fig)

    st.subheader("3D Earth Globe Visualization")

    # 1. Prepare coordinates in Radians for the sphere
    lon_rad = np.deg2rad(data[lon_name].values)
    lat_rad = np.deg2rad(data[lat_name].values)
    lon_grid, lat_grid = np.meshgrid(lon_rad, lat_rad)

    # 2. Spherical Math (X, Y, Z)
    X = np.cos(lat_grid) * np.cos(lon_grid)
    Y = np.cos(lat_grid) * np.sin(lon_grid)
    Z = np.sin(lat_grid)

    # 3. Get Data using the dynamic time name
    step_data = data.isel({time_name: time_index}) if time_name else data
    z_values = step_data.values
    
    z_min, z_max = np.nanmin(z_values), np.nanmax(z_values)
    norm_data = (z_values - z_min) / (z_max - z_min) if z_max > z_min else np.zeros_like(z_values)

    # 4. Plot Globe
    fig3 = plt.figure(figsize=(10, 10))
    ax3 = fig3.add_subplot(111, projection='3d')

    surf = ax3.plot_surface(X, Y, Z, facecolors=current_cmap(norm_data),
                           antialiased=True, rstride=10, cstride=10)

    ax3.set_axis_off() 
    ax3.view_init(elev=20, azim=45) 
    st.pyplot(fig3)

    st.subheader("Time Series Plot")

    lat_vals = data[lat_name].values
    lon_vals = data[lon_name].values
    
    # Calculate default indices based on preset
    def_lat_idx = 0
    def_lon_idx = 0
    if locations[selected_loc]:
        def_lat_idx = int(np.abs(lat_vals - locations[selected_loc]["lat"]).argmin())
        def_lon_idx = int(np.abs(lon_vals - locations[selected_loc]["lon"]).argmin())

    c1, c2 = st.columns(2)
    lat_index = c1.slider("Latitude Index", 0, len(lat_vals)-1, def_lat_idx)
    lon_index = c2.slider("Longitude Index", 0, len(lon_vals)-1, def_lon_idx)

    # This selects by index regardless of the dimension order
    # Fetch data and force load for the 1D slice (essential for 3GB files)
    ts = data.isel({lat_name: lat_index, lon_name: lon_index}).load()

    if ts.isnull().all():
        st.warning("No data here (likely ocean). Move the sliders to a land area!")
    else:
        # Use native Streamlit chart for interactive hovering
        chart_data = ts.to_dataframe()[variable]
        st.line_chart(chart_data)
# 🌍 PyClimaExplorer

**PyClimaExplorer** is a high-performance, interactive web dashboard designed to visualize massive NetCDF climate datasets in real-time. Built with Python and Streamlit, it transforms heavy scientific data into accessible, interactive 2D maps and 3D globes.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/ashutosh302/pyclimateexplorer/main/ourapp3.py)

## 🚀 The Challenge & Solution
Climate data is typically stored in `.nc` (NetCDF) files, which can contain millions of data points across multiple dimensions (Latitude, Longitude, Time). Processing and rendering this in a browser often leads to memory crashes. 

**PyClimaExplorer solves this through Dynamic Sub-Sampling.** The app auto-calculates the optimal resolution for the user's hardware, reducing the data footprint by up to 75% on the fly. This allows it to render interactive Plotly 3D globes without freezing the browser or crashing cloud servers.

## ✨ Key Features
* **Interactive 3D Globe & 2D Maps:** Powered by Plotly, allowing users to zoom, pan, and hover over specific coordinates to read exact atmospheric values.
* **Professional Meteorological Styling:** Automatically applies industry-standard colormaps (e.g., reverse Red-Yellow-Blue for temperature, custom Blues for snow depth).
* **Location-Specific Time Series:** Select a global preset (like the Amazon Rainforest or the Sahara Desert) or manually select coordinates to generate instant time-series charts and statistical breakdowns (Max, Min, Avg).
* **Dynamic Time Scrubbing:** Step through historical timeline data seamlessly.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **Data Processing:** Xarray, NumPy
* **Visualization:** Plotly, Matplotlib, Cartopy
* **Data Format:** NetCDF4 (.nc)

## 📊 Supported Variables
This dashboard is configured to automatically parse and format standard ERA5 climate model codes:
* `t2m`: 2 Metre Surface Temperature (K)
* `sde`: Snow Depth (m)
* `swvl1`: Volumetric Soil Water Layer 1 (m³/m³)
* `tp`: Total Precipitation (m)

## 💻 Local Installation
If you want to run this project locally on your machine:

1. Clone the repository:
   ```bash
   git clone [https://github.com/Ashutosh302/PyClimateExplorer.git](https://github.com/Ashutosh302/PyClimateExplorer.git)
   cd PyClimateExplorer

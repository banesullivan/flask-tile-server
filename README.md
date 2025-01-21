![tile-diagram](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/oam-tiles.jpg)

# 🌐 Local Tile Server for Geospatial Rasters

[![codecov](https://codecov.io/gh/banesullivan/localtileserver/branch/main/graph/badge.svg?token=S0HQ64FW8G)](https://codecov.io/gh/banesullivan/localtileserver)
[![PyPI](https://img.shields.io/pypi/v/localtileserver.svg?logo=python&logoColor=white)](https://pypi.org/project/localtileserver/)
[![conda](https://img.shields.io/conda/vn/conda-forge/localtileserver.svg?logo=conda-forge&logoColor=white)](https://anaconda.org/conda-forge/localtileserver)

*Need to visualize a rather large (gigabytes+) raster?* **This is for you.**

A Python package for serving tiles from large raster files in
the [Slippy Maps standard](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
(i.e., `/zoom/x/y.png`) for visualization in Jupyter with `ipyleaflet` or `folium`.

Launch a [demo](https://github.com/banesullivan/localtileserver-demo) on MyBinder [![MyBinder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD)

Documentation: https://localtileserver.banesullivan.com/

Built on [rio-tiler](https://github.com/cogeotiff/rio-tiler)


## 🌟 Highlights

- Launch a tile server for large geospatial images
- View local or remote* raster files with `ipyleaflet` or `folium` in Jupyter
- View rasters with CesiumJS with the built-in web application

**remote raster files should be pre-tiled Cloud Optimized GeoTiffs*

## 🚀 Usage

Usage details and examples can be found in the documentation: https://localtileserver.banesullivan.com/

The following is a minimal example to visualize a local raster file with
`ipyleaflet`:

```py
import localtileserver as lts
from ipyleaflet import Map

# First, create a tile server from local raster file
client = lts.open('path/to/geo.tif')

# Create ipyleaflet tile layer from that server
t = lts.get_leaflet_tile_layer(client)

m = Map(center=client.center(), zoom=client.default_zoom)
m.add(t)
m
```

![ipyleaflet](https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/ipyleaflet.png)

## ℹ️ Overview

The `TileClient` class can be used to to launch a tile server in a background
thread which will serve raster imagery to a viewer (usually `ipyleaflet` or
`folium` in Jupyter notebooks).

This tile server can efficiently deliver varying resolutions of your
raster imagery to your viewer; it helps to have pre-tiled,
[Cloud Optimized GeoTIFFs (COGs)](https://www.cogeo.org/).

There is an included, standalone web viewer leveraging
[CesiumJS](https://cesium.com/platform/cesiumjs/).


## ⬇️ Installation

Get started with `localtileserver` to view rasters in Jupyter or deploy as your
own Flask application.

### 🐍 Installing with `conda`

Conda makes managing `localtileserver`'s dependencies across platforms quite
easy and this is the recommended method to install:

```bash
conda install -c conda-forge localtileserver
```

### 🎡 Installing with `pip`

If you prefer pip, then you can install from PyPI: https://pypi.org/project/localtileserver/

```
pip install localtileserver
```

## 💭 Feedback

Please share your thoughts and questions on the [Discussions](https://github.com/banesullivan/localtileserver/discussions) board.
If you would like to report any bugs or make feature requests, please open an issue.

If filing a bug report, please share a scooby `Report`:

```py
import localtileserver as lts
print(lts.Report())
```

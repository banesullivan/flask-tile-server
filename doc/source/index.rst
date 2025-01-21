🌐 localtileserver
==================

.. toctree::
   :hidden:

   installation/index
   user-guide/index
   api/index



*Need to visualize a rather large (gigabytes+) raster?* **This is for you.**

  Try it out below!

.. jupyter-execute::

  import localtileserver as lts
  from localtileserver import examples
  from ipyleaflet import Map

  # Create a TileClient from a raster file
  # client = lts.open('path/to/geo.tif')
  client = examples.get_san_francisco()  # use example data

  # Create ipyleaflet TileLayer from that server
  t = lts.get_leaflet_tile_layer(client)
  # Create ipyleaflet map, add tile layer, and display
  m = Map(center=client.center(), zoom=client.default_zoom)
  m.add(t)
  m



.. raw:: html

  <br/>


A Python package for serving tiles from large raster files in
the `Slippy Maps standard <https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames>`_
(i.e., `/zoom/x/y.png`) for visualization in Jupyter with ``ipyleaflet`` or ``folium``.


.. |binder| image:: https://mybinder.org/badge_logo.svg
   :target: https://mybinder.org/v2/gh/banesullivan/localtileserver-demo/HEAD
   :alt: MyBinder

Launch a `demo <https://github.com/banesullivan/localtileserver-demo>`_ on MyBinder |binder|


Built on `rio-tiler <https://github.com/cogeotiff/rio-tiler>`_.


🌟 Highlights
=============

- Launch a tile server for large geospatial images
- View local or remote* raster files with ``ipyleaflet`` or ``folium`` in Jupyter
- View rasters with CesiumJS with the built-in web application

*remote raster files should be pre-tiled Cloud Optimized GeoTiffs*

ℹ️ Overview
===========

The :class:`TileClient` class can be used to to launch a tile server in a background
thread which will serve raster imagery to a viewer (see ``ipyleaflet`` and
``folium`` examples in :ref:`user_guide`).

This tile server can efficiently deliver varying resolutions of your
raster imagery to your viewer; it helps to have pre-tiled,
`Cloud Optimized GeoTIFFs (COG) <https://www.cogeo.org/>`_.

There is an included, standalone web viewer leveraging
`CesiumJS <https://cesium.com/platform/cesiumjs/>`_.


🪢 Community Usage
==================

- `leafmap <https://github.com/giswqs/leafmap>`_ and `geemap <https://github.com/giswqs/geemap>`_: use localtileserver for visualizing large raster images in a Jupyter-based geospatial mapping application
- `streamlit-geospatial <https://github.com/giswqs/streamlit-geospatial>`_: uses localtileserver's remote tile server for viewing image tiles
- `remotetileserver <https://github.com/banesullivan/remotetileserver>`_: uses the core flask application to spin up a production ready tile server
- `Kaustav Mukherjee's blog post <https://kaustavmukherjee-66179.medium.com/visualize-raster-tiles-locally-using-localtileserver-0-4-1-and-jupyter-notebook-cccd59e6420a>`_: a user-created demonstration on how to get started with localtileserver
- `Serving up SpaceNet Imagery for Bokeh <https://medium.com/geodesic/serving-up-spacenet-imagery-for-bokeh-e85b8fffe05>`_: Adam Van Etten's blog post using localtileserver to view imagery with Bokeh

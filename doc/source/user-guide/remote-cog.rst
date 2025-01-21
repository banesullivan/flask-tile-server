☁️ Remote Cloud Optimized GeoTiffs (COGs)
-----------------------------------------

While ``localtileserver`` is intended to be used only with raster files existing
on your local filesystem, there is support for URL files through GDAL's
`Virtual Storage Interface <https://gdal.org/user/virtual_file_systems.html>`_.
Simply pass your ``http<s>://`` or ``s3://`` URL to the :class:`TileClient`. This will
work quite well for pre-tiled Cloud Optimized GeoTiffs, but I do not recommend
doing this with non-tiled raster formats.

For example, the raster at the url below is ~3GiB but because it is pre-tiled,
we can view tiles of the remote file very efficiently in a Jupyter notebook.

.. jupyter-execute::

  import localtileserver as lts
  import folium, ipyleaflet

  url = 'https://github.com/giswqs/data/raw/main/raster/landsat7.tif'

  # First, create a tile server from the URL raster file
  client = lts.open(url)


Here we can create a folium map with the raster overlain:

.. jupyter-execute::

  # Create folium tile layer from that server
  t = lts.get_folium_tile_layer(client)

  m = folium.Map(location=client.center(), zoom_start=client.default_zoom)
  m.add_child(t)
  m


Or we can do the same ipyleaflet:

.. jupyter-execute::

  # Create ipyleaflet tile layer from that server
  l = lts.get_leaflet_tile_layer(client)

  m = ipyleaflet.Map(center=client.center(), zoom=client.default_zoom)
  m.add(l)
  m


.. note::

  Note that the Virtual Storage Interface is a complex API, and :class:`TileClient`
  currently only handles ``vsis3`` and ``vsicurl``. If you need a different VFS
  mechanism, simply create your ``/vsi`` path and pass that to :class:`TileClient`.

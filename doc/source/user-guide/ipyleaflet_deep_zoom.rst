🔬 Deep Zoom with ``ipyleaflet``
--------------------------------

In order to perform deep zooming of tile sources with ``ipyleaflet``, you must
specify a few keyword arguments:

- ``max_zoom`` and ``max_native_zoom`` set appropriately in the ``TileLayer``
- ``max_zoom`` set in the ``Map`` which matches ``max_zoom`` in the ``TileLayer``

For more information, please see https://github.com/jupyter-widgets/ipyleaflet/issues/925

.. jupyter-execute::

  import localtileserver as lts
  from localtileserver import examples
  from ipyleaflet import Map, TileLayer

  # Load high res raster
  client = examples.get_oam2()

  max_zoom = 30

  # Create zoomable tile layer from high res raster
  layer = lts.get_leaflet_tile_layer(client,
      # extra kwargs to pass to the TileLayer
      max_zoom=max_zoom,
      max_native_zoom=max_zoom,
  )

  # Make the ipyleaflet map with deeper zoom
  m = Map(center=client.center(),
          zoom=22, max_zoom=max_zoom
  )
  m.add(layer)
  m

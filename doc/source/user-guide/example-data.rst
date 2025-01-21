🗺️ Example Datasets
-------------------

A few example datasets are included with `localtileserver`. A particularly
useful one has global elevation data which you can use to create high resolution
Digital Elevation Models (DEMs) of a local region.


.. code:: python

  import localtileserver as lts
  from localtileserver import examples
  from ipyleaflet import Map

  # Load example tile layer from publicly available DEM source
  client = examples.get_elevation()

  # Create ipyleaflet tile layer from that server
  t = lts.get_leaflet_tile_layer(client,
                                 indexes=1, vmin=-500, vmax=5000,
                                 colormap='plasma',
                                 opacity=0.75)

  m = Map(zoom=2)
  m.add(t)
  m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/elevation.png


Here is another example with the Virtual Earth satellite imagery

.. code:: python

  import localtileserver as lts
  from localtileserver import examples
  from ipyleaflet import Map

  # Load example tile layer from publicly available imagery
  client = examples.get_virtual_earth()

  # Create ipyleaflet tile layer from that server
  t = lts.get_leaflet_tile_layer(client, opacity=1)

  m = Map(center=(39.751343612695145, -105.22181306125279), zoom=18)
  m.add(t)
  m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/kafadar.png

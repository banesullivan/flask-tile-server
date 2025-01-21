⛰️ DEM Hillshade
----------------

Generate hillshade map from Digital Elevation Model (DEM).

A hillshade is a 3D representation of a surface where the darker and lighter
colors represent the shadows and highlights that you would visually expect to
see in a terrain model. Hillshades are often used as an underlay in a map, to
make the data appear more 3-Dimensional.


.. note::

  This example was adopted from `EarthPy <https://earthpy.readthedocs.io/en/latest/gallery_vignettes/plot_dem_hillshade.html>`_


.. code:: python

  import localtileserver as lts
  from localtileserver import examples, helpers
  from ipyleaflet import Map, SplitMapControl
  import rasterio

  # Example DEM dataset
  client = examples.get_co_elevation()

  tdem = lts.get_leaflet_tile_layer(client, colormap='gist_earth', nodata=0)

  m = client.get_leaflet_map()
  m.add(tdem)
  m


Read the DEM data as a NumPy array using rasterio:

.. code:: python

  dem = client.dataset.read()[0, :, :]
  dem.shape


Compute the hillshade of the DEM using the :func:`localtileserver.helpers.hillshade`
function (adopted from EarthPy).

.. code:: python

  help(helpers.hillshade)

.. code:: python

  # Compute hillshade
  hs_arr = helpers.hillshade(dem)

  # Save hillshade arrays as new raster and open with rasterio
  hs = rasterio.open(helpers.save_new_raster(client, hs_arr))


.. code:: python

  # Make an ipyleaflet tile layer of the hillshade
  hst = lts.get_leaflet_tile_layer(hs, nodata=0)

  m = client.get_leaflet_map()
  control = SplitMapControl(left_layer=tdem, right_layer=hst)
  m.add_control(control)
  m

.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/hillshade_compare.png


We can also overlay the hillshade on the original DEM so that it gives it a 3D
effect:

.. code:: python

  m = client.get_leaflet_map()
  m.add(tdem)
  m.add(lts.get_leaflet_tile_layer(hs, opacity=0.5, nodata=0))
  m


.. image:: https://raw.githubusercontent.com/banesullivan/localtileserver/main/imgs/hillshade.png

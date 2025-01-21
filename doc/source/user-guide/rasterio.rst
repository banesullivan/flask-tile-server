🧩 Rasterio
-----------

``localtileserver.TileClient`` supports viewing ``rasterio.DatasetReader``
so that you can easily visualize your data when working with rasterio.
This will only work when opening a raster in read-mode.


.. code-block:: python

    import rasterio
    import localtileserver as lts
    from ipyleaflet import Map

    src = rasterio.open('path/to/geo.tif')

    client = lts.TileClient(src)

    t = lts.get_leaflet_tile_layer(client)

    m = Map(center=client.center(), zoom=client.default_zoom)
    m.add(t)
    m


``localtileserver`` actually uses ``rasterio`` under the hood for everything
and keeps a reference to a ``rasterio.DatasetReader`` for all clients.


.. code-block:: python

    from localtileserver import examples

    # Load example tile layer from publicly available DEM source
    client = examples.get_elevation()

    client.dataset

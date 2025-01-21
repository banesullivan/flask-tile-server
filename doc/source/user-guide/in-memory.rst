🧠 In-Memory Rasters
--------------------

.. jupyter-execute::

    import rasterio
    import localtileserver as lts
    from ipyleaflet import Map

    # Open a rasterio dataset
    dataset = rasterio.open('https://open.gishub.org/data/raster/srtm90.tif')
    data_array = dataset.read(1)


.. jupyter-execute::

    # Do some processing on the data array
    data_array[data_array < 1000] = 0

    # Create rasterio dataset in memory
    memory_file = rasterio.MemoryFile()
    raster_dataset = memory_file.open(driver='GTiff',
                                    height=data_array.shape[0],
                                    width=data_array.shape[1],
                                    count=1,
                                    dtype=str(data_array.dtype),
                                    crs=dataset.crs,
                                    transform=dataset.transform)

    # Write data array values to the rasterio dataset
    raster_dataset.write(data_array, 1)
    raster_dataset.close()


.. jupyter-execute::

    client = lts.TileClient(raster_dataset)
    client.thumbnail(colormap="terrain")

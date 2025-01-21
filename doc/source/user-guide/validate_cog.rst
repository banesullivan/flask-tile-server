✅ Validate COG
---------------

``localtileserver`` includes a helper method to validate whether or not a
source image meets the requirements of a Cloud Optimized GeoTiff.

:func:`localtileserver.validate.validate_cog` uses rio-cogeo to validate
whether or not a source image meets the requirements of a Cloud Optimized
GeoTIFF.

You can use the script by:

.. jupyter-execute::

   import localtileserver as lts

   # Path to raster (URL or local path)
   url = 'https://github.com/giswqs/data/raw/main/raster/landsat7.tif'

   # If invalid, returns False
   lts.validate_cog(url)


This can also be used with an existing :class:`localtileserver.TileClient`:

.. jupyter-execute::

   import localtileserver as lts
   from localtileserver import examples

   client = examples.get_san_francisco()

   # If invalid, returns False
   lts.validate_cog(client)

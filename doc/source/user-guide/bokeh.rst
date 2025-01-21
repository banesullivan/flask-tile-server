🎨 Plotting with Bokeh
----------------------

.. jupyter-execute::

  from bokeh.plotting import figure, output_file, show
  from bokeh.io import output_notebook
  from bokeh.models import WMTSTileSource
  from localtileserver import examples

  output_notebook()

  client = examples.get_san_francisco()
  raster_provider = WMTSTileSource(url=client.get_tile_url(client=True))
  bounds = client.bounds(projection='EPSG:3857')

  p = figure(x_range=(bounds[2], bounds[3]), y_range=(bounds[0], bounds[1]),
             x_axis_type="mercator", y_axis_type="mercator")
  p.add_tile('CARTODBPOSITRON')
  p.add_tile(raster_provider)
  show(p)

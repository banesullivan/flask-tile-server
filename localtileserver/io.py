import pathlib
from typing import Union

import rasterio

from localtileserver.client import TileClient, get_or_create_tile_client


def open(
    source: Union[
        pathlib.Path,
        str,
        TileClient,
        rasterio.io.DatasetReaderBase,
    ],
    port: Union[int, str] = "default",
    debug: bool = False,
):
    """Open a raster file as a TileClient.

    Parameters
    ----------
    source : pathlib.Path, str, TileClient, rasterio.io.DatasetReaderBase
        The source dataset to use for the tile client.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.

    """
    return get_or_create_tile_client(source, port=port, debug=debug)[0]

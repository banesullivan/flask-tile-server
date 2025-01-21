from collections.abc import Iterable
import json
import logging
import pathlib
from typing import List, Optional, Union

from matplotlib.colors import Colormap, ListedColormap
import rasterio
import requests
from rio_tiler.io import Reader

try:
    import anywidget
except ImportError:  # pragma: no cover
    anywidget = None
try:
    import ipyleaflet
except ImportError:  # pragma: no cover
    ipyleaflet = None
try:
    import shapely
except ImportError:  # pragma: no cover
    shapely = None

from server_thread import ServerManager, launch_server

from localtileserver.configure import get_default_client_params
from localtileserver.manager import AppManager
from localtileserver.tiler import (
    format_to_encoding,
    get_building_docs,
    get_meta_data,
    get_point,
    get_preview,
    get_reader,
    get_source_bounds,
    get_tile,
    palette_valid_or_raise,
)
from localtileserver.utilities import add_query_parameters

BUILDING_DOCS = get_building_docs()
DEMO_REMOTE_TILE_SERVER = "https://tileserver.banesullivan.com/"
logger = logging.getLogger(__name__)


class TilerInterface:
    """Base TileClient methods and configuration.

    This class interfaces directly with rasterio and rio-tiler.

    Parameters
    ----------
    source : pathlib.Path, str, Reader, DatasetReaderBase
        The source dataset to use for the tile client.

    """

    def __init__(
        self,
        source: Union[pathlib.Path, str, rasterio.io.DatasetReaderBase],
    ):
        if isinstance(source, rasterio.io.DatasetReaderBase):  # and hasattr(source, "name"):
            self._reader = get_reader(source.name)
        elif isinstance(source, Reader):
            self._reader = source
        else:
            self._reader = get_reader(source)

    @property
    def reader(self):
        return self._reader

    @property
    def dataset(self):
        return self.reader.dataset

    @property
    def filename(self):
        return self.dataset.name

    @property
    def info(self):
        return self.reader.info()

    @property
    def metadata(self):
        return get_meta_data(self.reader)

    @property
    def band_names(self):
        return [desc[0] for desc in self.metadata["band_descriptions"]]

    @property
    def min_zoom(self):
        if hasattr(self.info, "minzoom"):
            return self.info.minzoom
        else:
            return self.reader.minzoom

    @property
    def max_zoom(self):
        if hasattr(self.info, "maxzoom"):
            return self.info.maxzoom
        else:
            return self.reader.maxzoom

    @property
    def default_zoom(self):
        return self.min_zoom

    def bounds(
        self, projection: str = "EPSG:4326", return_polygon: bool = False, return_wkt: bool = False
    ):
        bounds = get_source_bounds(self.reader, projection=projection)
        extent = (bounds["bottom"], bounds["top"], bounds["left"], bounds["right"])
        if not return_polygon and not return_wkt:
            return extent
        # Safely import shapely
        try:
            from shapely.geometry import Polygon
        except ImportError as e:  # pragma: no cover
            raise ImportError(f"Please install `shapely`: {e}")
        coords = (
            (bounds["left"], bounds["top"]),
            (bounds["left"], bounds["top"]),
            (bounds["right"], bounds["top"]),
            (bounds["right"], bounds["bottom"]),
            (bounds["left"], bounds["bottom"]),
            (bounds["left"], bounds["top"]),  # Close the loop
        )
        poly = Polygon(coords)
        if return_wkt:
            return poly.wkt
        return poly

    def center(
        self, projection: str = "EPSG:4326", return_point: bool = False, return_wkt: bool = False
    ):
        """Get center in the form of (y <lat>, x <lon>).

        Parameters
        ----------
        projection : str
            The srs or projection as a Proj4 string of the returned coordinates

        return_point : bool, optional
            If true, returns a shapely.Point object.

        return_wkt : bool, optional
            If true, returns a Well Known Text (WKT) string of center
            coordinates.

        """
        bounds = self.bounds(projection=projection)
        point = (
            (bounds[1] - bounds[0]) / 2 + bounds[0],
            (bounds[3] - bounds[2]) / 2 + bounds[2],
        )
        if return_point or return_wkt:
            # Safely import shapely
            try:
                from shapely.geometry import Point
            except ImportError as e:  # pragma: no cover
                raise ImportError(f"Please install `shapely`: {e}")

            point = Point(point)
            if return_wkt:
                return point.wkt

        return point

    def tile(
        self,
        z: int,
        x: int,
        y: int,
        indexes: Optional[List[int]] = None,
        colormap: Optional[str] = None,
        vmin: Optional[Union[float, List[float]]] = None,
        vmax: Optional[Union[float, List[float]]] = None,
        nodata: Optional[Union[int, float]] = None,
        output_path: pathlib.Path = None,
        encoding: str = "PNG",
    ):
        """Generate a tile from the source raster.

        Parameters
        ----------
        z : int
            The zoom level of the tile.
        x : int
            The x coordinate of the tile.
        y : int
            The y coordinate of the tile.
        indexes : int
            The band of the source raster to use (default if None is to show RGB if
            available). Band indexing starts at 1. This can also be a list of
            integers to set which 3 bands to use for RGB.
        colormap : str
            The name of the matplotlib colormap to use when plotting a single band.
            Default is greyscale.
        vmin : float
            The minimum value to use when colormapping a single band.
        vmax : float
            The maximized value to use when colormapping a single band.
        nodata : float
            The value from the band to use to interpret as not valid data.

        """
        if encoding.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        encoding = format_to_encoding(encoding)
        tile_binary = get_tile(
            self.reader,
            z,
            x,
            y,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
        )
        if output_path:
            with open(output_path, "wb") as f:
                f.write(tile_binary)
        return tile_binary

    def thumbnail(
        self,
        indexes: Optional[List[int]] = None,
        colormap: Optional[str] = None,
        vmin: Optional[Union[float, List[float]]] = None,
        vmax: Optional[Union[float, List[float]]] = None,
        nodata: Optional[Union[int, float]] = None,
        output_path: pathlib.Path = None,
        encoding: str = "PNG",
        max_size: int = 512,
    ):
        """Generate a thumbnail preview of the dataset.

        Parameters
        ----------
        indexes : int
            The band of the source raster to use (default if None is to show RGB if
            available). Band indexing starts at 1. This can also be a list of
            integers to set which 3 bands to use for RGB.
        colormap : str
            The name of the matplotlib colormap to use when plotting a single band.
            Default is greyscale.
        vmin : float
            The minimum value to use when colormapping a single band.
        vmax : float
            The maximized value to use when colormapping a single band.
        nodata : float
            The value from the band to use to interpret as not valid data.

        """
        if encoding.lower() not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Encoding ({encoding}) not supported.")
        encoding = format_to_encoding(encoding)
        thumb_data = get_preview(
            self.reader,
            max_size=max_size,
            colormap=colormap,
            indexes=indexes,
            nodata=nodata,
            img_format=encoding,
            vmin=vmin,
            vmax=vmax,
        )

        if output_path:
            with open(output_path, "wb") as f:
                f.write(thumb_data)
        return thumb_data

    def point(self, lon: float, lat: float, **kwargs):
        return get_point(self.reader, lon, lat, **kwargs)

    def _repr_png_(self):
        return self.thumbnail(encoding="png")


class TileServerMixin:
    """Serve tiles from a local raster file in a background thread.

    Parameters
    ----------
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    client_port : int
        The port on your client browser to use for fetching tiles. This is
        useful when running in Docker and performing port forwarding.
    client_host : str
        The host on which your client browser can access the server.

    """

    def __init__(
        self,
        port: Union[int, str] = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int = None,
        client_host: str = None,
        client_prefix: str = None,
        cors_all: bool = False,
    ):
        app = AppManager.get_or_create_app(cors_all=cors_all)
        self._key = launch_server(app, port=port, debug=debug, host=host)
        # Store actual port just in case
        self._port = ServerManager.get_server(self._key).srv.port
        client_host, client_port, client_prefix = get_default_client_params(
            client_host, client_port, client_prefix
        )
        self.client_host = client_host
        self.client_port = client_port
        self.client_prefix = client_prefix
        if BUILDING_DOCS and not client_host:
            self._client_host = DEMO_REMOTE_TILE_SERVER

        if not debug:
            logging.getLogger("rasterio").setLevel(logging.ERROR)
        else:
            logging.getLogger("rasterio").setLevel(logging.DEBUG)

        try:
            import google.colab  # noqa

            self.enable_colab()
        except ImportError:
            pass

    def shutdown(self, force: bool = False):
        if hasattr(self, "_key"):
            ServerManager.shutdown_server(self._key, force=force)

    def __del__(self):
        self.shutdown()

    @property
    def server(self):
        return ServerManager.get_server(self._key)

    @property
    def server_port(self):
        return self.server.port

    @property
    def server_host(self):
        return self.server.host

    @property
    def server_base_url(self):
        return f"http://{self.server_host}:{self.server_port}"

    @property
    def client_port(self):
        return self._client_port

    @client_port.setter
    def client_port(self, value):
        if value is True:
            value = self.server_port
        self._client_port = value

    @property
    def client_host(self):
        return self._client_host

    @client_host.setter
    def client_host(self, value):
        self._client_host = value

    @property
    def client_prefix(self):
        if self._client_prefix:
            return self._client_prefix.replace("{port}", str(self.server_port))

    @client_prefix.setter
    def client_prefix(self, value):
        self._client_prefix = value

    def enable_colab(self):
        """Configure this client for use on Google Colab."""
        self.client_host = "localhost"
        self.client_port = True

    @property
    def client_base_url(self):
        scheme = (
            "http://"
            if self.client_host is not None and not self.client_host.startswith("http")
            else ""
        )
        if self.client_port is not None and self.client_host is not None:
            base = f"{scheme}{self.client_host}:{self.client_port}"
        elif self.client_port is None and self.client_host is not None:
            base = f"{scheme}{self.client_host}"
        elif self.client_port is not None and self.client_host is None:
            base = f"http://{self.server_host}:{self.client_port}"
        else:
            base = "/"  # Use relative path
        if self.client_prefix is not None:
            base = f"{base}{self.client_prefix}"
        if base.startswith("/"):
            base = f"/{base.lstrip('/')}"
        return base

    def _produce_url(self, base: str):
        return add_query_parameters(base, {"filename": self.filename})

    def create_url(self, path: str, client: bool = False):
        if client and (
            self.client_port is not None
            or self.client_host is not None
            or self.client_prefix is not None
        ):
            return self._produce_url(f"{self.client_base_url}/{path.lstrip('/')}")
        return self._produce_url(f"{self.server_base_url}/{path.lstrip('/')}")

    def get_tile_url(
        self,
        indexes: Optional[List[int]] = None,
        colormap: Optional[Union[str, Colormap, List[str]]] = None,
        vmin: Optional[Union[float, List[float]]] = None,
        vmax: Optional[Union[float, List[float]]] = None,
        nodata: Optional[Union[int, float]] = None,
        client: bool = False,
    ):
        """Get slippy maps tile URL (e.g., `/zoom/x/y.png`).

        Parameters
        ----------
        indexes : int
            The band of the source raster to use (default if None is to show RGB if
            available). Band indexing starts at 1. This can also be a list of
            integers to set which 3 bands to use for RGB.
        colormap : str
            The name of the matplotlib colormap to use when plotting a single band.
            Default is greyscale.
        vmin : float
            The minimum value to use when colormapping a single band.
        vmax : float
            The maximized value to use when colormapping a single band.
        nodata : float
            The value from the band to use to interpret as not valid data.

        """
        # First handle query parameters to check for errors
        params = {}
        if indexes is not None:
            params["indexes"] = indexes
        if colormap is not None:
            if isinstance(colormap, ListedColormap):
                colormap = json.dumps([c for c in colormap.colors])
            elif isinstance(colormap, Colormap):
                colormap = json.dumps(
                    {k: tuple(v.tolist()) for k, v in enumerate(colormap(range(256), 1, 1))}
                )
            elif isinstance(colormap, list):
                colormap = json.dumps(colormap)
            else:
                # make sure palette is valid
                palette_valid_or_raise(colormap)

            params["colormap"] = colormap
        if vmin is not None:
            if isinstance(vmin, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmin` is an iterable.")
            params["vmin"] = vmin
        if vmax is not None:
            if isinstance(vmax, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `vmax` is an iterable.")
            params["vmax"] = vmax
        if nodata is not None:
            if isinstance(nodata, Iterable) and not isinstance(indexes, Iterable):
                raise ValueError("`indexes` must be explicitly set if `nodata` is an iterable.")
            params["nodata"] = nodata
        return add_query_parameters(
            self.create_url("api/tiles/{z}/{x}/{y}.png", client=client), params
        )

    def as_leaflet_layer(self):
        from localtileserver.widgets import get_leaflet_tile_layer

        return get_leaflet_tile_layer(self)

    def get_leaflet_map(self, add_bounds: bool = False, **kwargs):
        """Get an ipyleaflet Map centered and zoomed to the dataset bounds.

        Note
        ----
        You will need to add the tile layer to the map yourself.

        Parameters
        ----------
        kwargs : dict
            Additional keyword arguments to pass to the ipyleaflet Map.

        """
        from ipyleaflet import Map, WKTLayer

        m = Map(center=self.center(), zoom=self.default_zoom, **kwargs)
        if add_bounds:
            if not shapely:
                raise ImportError("Please install `shapely` to use this feature.")
            wlayer = WKTLayer(
                wkt_string=self.bounds(return_wkt=True),
                style={"dashArray": 9, "fillOpacity": 0, "weight": 1},
            )
            m.add(wlayer)
        return m

    if False:  # ipyleaflet:

        def _ipython_display_(self):
            from IPython.display import display

            from localtileserver.widgets import get_leaflet_tile_layer

            t = get_leaflet_tile_layer(self)
            m = self.get_leaflet_map(add_bounds=shapely)
            m.add(t)
            return display(m)

    elif anywidget:

        def _ipython_display_(self):
            from IPython.display import display

            from localtileserver.custom.widgets import TileLayerWidget

            w = TileLayerWidget(self)
            return display(w)


class TileClient(TilerInterface, TileServerMixin):
    """Tile client interface for generateing and serving tiles.

    Parameters
    ----------
    source : pathlib.Path, str, Reader, DatasetReaderBase
        The source dataset to use for the tile client.
    port : int
        The port on your host machine to use for the tile server. This defaults
        to getting an available port.
    debug : bool
        Run the tile server in debug mode.
    client_port : int
        The port on your client browser to use for fetching tiles. This is
        useful when running in Docker and performing port forwarding.
    client_host : str
        The host on which your client browser can access the server.

    """

    def __init__(
        self,
        source: Union[pathlib.Path, str, rasterio.io.DatasetReaderBase],
        port: Union[int, str] = "default",
        debug: bool = False,
        host: str = "127.0.0.1",
        client_port: int = None,
        client_host: str = None,
        client_prefix: str = None,
        cors_all: bool = False,
    ):
        TilerInterface.__init__(self, source=source)
        TileServerMixin.__init__(
            self,
            port=port,
            debug=debug,
            host=host,
            client_port=client_port,
            client_host=client_host,
            client_prefix=client_prefix,
            cors_all=cors_all,
        )


def get_or_create_tile_client(
    source: Union[
        pathlib.Path,
        str,
        TileClient,
        rasterio.io.DatasetReaderBase,
    ],
    port: Union[int, str] = "default",
    debug: bool = False,
):
    """A helper to safely get a TileClient from a path on disk.

    Note
    ----
    TODO: There should eventually be a check to see if a TileClient instance exists
    for the given filename. For now, it is not really a big deal because the
    default is for all TileClient's to share a single server.

    """
    _internally_created = False
    # Launch tile server if file path is given
    if not isinstance(source, TileClient):
        source = TileClient(source, port=port, debug=debug)
        _internally_created = True

    # Check that the tile source is valid and no server errors
    try:
        r = requests.get(source.create_url("api/metadata"))
        r.raise_for_status()
    except requests.HTTPError as e:
        # Make sure to destroy the server and its thread if internally created.
        if _internally_created:
            source.shutdown()
            del source
        raise e
    return source, _internally_created

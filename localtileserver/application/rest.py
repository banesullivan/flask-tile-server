import io
import logging
import time

from PIL import Image, ImageOps
from flask import request, send_file
from flask.views import View
from flask_caching import Cache
from large_image_source_gdal import GDALFileTileSource

from localtileserver import style, utilities
from localtileserver.application import app

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})
logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 120


def make_cache_key(*args, **kwargs):
    path = request.path
    args = str(hash(frozenset(request.args.items())))
    return (path + args).encode("utf-8")


class BaseTileView(View):
    def get_tile_source(self, projection="EPSG:3857"):
        """Return the built tile source."""
        filename = utilities.get_clean_filename(request.args.get("filename", ""))
        style_args = style.reformat_style_query_parameters(request.args)
        band = style_args.get("band", 0)
        vmin = style_args.get("min", None)
        vmax = style_args.get("max", None)
        palette = style_args.get("palette", None)
        nodata = style_args.get("nodata", None)
        sty = style.make_style(band, vmin=vmin, vmax=vmax, palette=palette, nodata=nodata)
        return utilities.get_tile_source(filename, projection, style=sty)

    @staticmethod
    def add_border_to_image(content):
        img = Image.open(io.BytesIO(content))
        img = ImageOps.crop(img, 1)
        border = ImageOps.expand(img, border=1, fill="black")
        img_bytes = io.BytesIO()
        border.save(img_bytes, format="PNG")
        return img_bytes.getvalue()


class TilesDebugView(BaseTileView):
    """A dummy tile server endpoint that produces borders of the tile grid.

    This is used for testing tile viewers. It returns the same thing on every
    call. This takes a query parameter `sleep` to delay the response for
    testing (default is 0.5).

    """

    def dispatch_request(self, x: int, y: int, z: int):
        img = Image.new("RGBA", (255, 255))
        img = ImageOps.expand(img, border=1, fill="black")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        time.sleep(float(request.args.get("sleep", 0.5)))
        return send_file(
            img_bytes,
            download_name=f"{x}.{y}.{z}.png",
            mimetype="image/png",
        )


class MetadataView(BaseTileView):
    @cache.cached(timeout=REQUEST_TIMEOUT, key_prefix=make_cache_key)
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        return utilities.get_meta_data(tile_source)


class BoundsView(BaseTileView):
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        projection = request.args.get("projection", "EPSG:4326")
        return utilities.get_tile_bounds(
            tile_source,
            projection=projection,
        )


class TilesView(BaseTileView):
    @cache.cached(timeout=REQUEST_TIMEOUT, key_prefix=make_cache_key)
    def dispatch_request(self, x: int, y: int, z: int):
        projection = request.args.get("projection", "EPSG:3857")
        tile_source = self.get_tile_source(projection=projection)
        tile_binary = tile_source.getTile(x, y, z)
        mime_type = tile_source.getTileMimeType()
        grid = request.args.get("grid", "False")
        if grid.lower() in ["false", "no", "off"]:
            grid = False
        if grid:
            tile_binary = self.add_border_to_image(tile_binary)
        return send_file(
            io.BytesIO(tile_binary),
            download_name=f"{x}.{y}.{z}.png",
            mimetype=mime_type,
        )


class ThumbnailView(BaseTileView):
    @cache.cached(timeout=REQUEST_TIMEOUT, key_prefix=make_cache_key)
    def dispatch_request(self):
        tile_source = self.get_tile_source()
        thumb_data, mime_type = tile_source.getThumbnail(encoding="PNG")
        return send_file(
            io.BytesIO(thumb_data),
            download_name="thumbnail.png",
            mimetype=mime_type,
        )


class RegionWorldView(BaseTileView):
    """Returns region tile binary from world coordinates in given EPSG.

    Note
    ----
    Use the `units` query parameter to inidicate the projection of the given
    coordinates. This can be different than the `projection` parameter used
    to open the tile source. `units` defaults to `EPSG:4326`.

    """

    def dispatch_request(self, left: float, right: float, bottom: float, top: float):
        tile_source = self.get_tile_source()
        if not isinstance(tile_source, GDALFileTileSource):
            raise TypeError("Source image must have geospatial reference.")
        units = request.args.get("units", "EPSG:4326")
        encoding = request.args.get("encoding", "TILED")
        path, mime_type = utilities.get_region_world(
            tile_source,
            left,
            right,
            bottom,
            top,
            units,
            encoding,
        )
        return send_file(
            path,
            mimetype=mime_type,
        )


class RegionPixelView(BaseTileView):
    """Returns region tile binary from pixel coordinates."""

    def dispatch_request(self, left: float, right: float, bottom: float, top: float):
        tile_source = self.get_tile_source()
        encoding = request.args.get("encoding", None)
        path, mime_type = utilities.get_region_pixel(
            tile_source,
            left,
            right,
            bottom,
            top,
            encoding=encoding,
        )
        return send_file(
            path,
            mimetype=mime_type,
        )

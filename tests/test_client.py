import json
import os

import pytest
import rasterio
from rasterio.errors import RasterioIOError
import requests
from server_thread import ServerManager

import localtileserver as lts
from localtileserver.client import TileClient, get_or_create_tile_client
from localtileserver.helpers import parse_shapely, polygon_to_geojson
from localtileserver.tiler import get_cache_dir, get_clean_filename
from localtileserver.tiler.utilities import ImageBytes

from .utilities import get_content

skip_shapely = False
try:
    from shapely.geometry import Polygon
except ImportError:
    skip_shapely = True

TOLERANCE = 2e-2


def test_create_tile_client(bahamas_file):
    assert ServerManager.server_count() == 0
    tile_client = TileClient(bahamas_file, debug=True)
    assert str(tile_client.filename) == str(get_clean_filename(bahamas_file))
    assert tile_client.server_port
    assert tile_client.server_base_url
    assert "crs" in tile_client.metadata
    assert tile_client.bounds()
    center = tile_client.center()
    assert center[0] == pytest.approx(24.5579, abs=TOLERANCE)
    assert center[1] == pytest.approx(-77.7668, abs=TOLERANCE)
    tile_url = tile_client.get_tile_url().format(z=8, x=72, y=110)
    assert get_content(tile_url)  # just make sure it doesn't fail
    tile_conent = tile_client.tile(z=8, x=72, y=110)
    assert tile_conent
    tile_url = tile_client.get_tile_url(colormap="plasma").format(z=8, x=72, y=110)
    assert get_content(tile_url)  # just make sure it doesn't fail
    thumb = tile_client.thumbnail()
    assert isinstance(thumb, ImageBytes)
    assert thumb.mimetype == "image/png"
    tile_client.shutdown(force=True)


def test_create_tile_client_bad(bahamas_file):
    with pytest.raises(OSError):
        TileClient("foo.tif", debug=True)
    with pytest.raises(ValueError):
        TileClient(bahamas_file, port="0", debug=True)


def test_client_force_shutdown(bahamas):
    tile_url = bahamas.get_tile_url().format(z=8, x=72, y=110)
    assert get_content(tile_url)  # just make sure it doesn't fail
    assert ServerManager.server_count() == 1
    bahamas.shutdown(force=True)
    assert ServerManager.server_count() == 0
    with pytest.raises(requests.ConnectionError):
        assert get_content(tile_url)


# def test_multiple_tile_clients_one_server(bahamas, blue_marble):
#     assert ServerManager.server_count() == 1
#     tile_url_a = bahamas.get_tile_url().format(z=8, x=72, y=110)
#     tile_url_b = blue_marble.get_tile_url().format(z=8, x=72, y=110)
#     assert get_content(tile_url_a) != get_content(tile_url_b)
#     thumb_url_a = bahamas.create_url("api/thumbnail.png")
#     thumb_url_b = blue_marble.create_url("api/thumbnail.png")
#     assert get_content(thumb_url_a) != get_content(thumb_url_b)


def test_caching_query_params(bahamas):
    thumb_url_a = bahamas.create_url("api/thumbnail.png")
    thumb_url_b = bahamas.create_url("api/thumbnail.png?indexes=1")
    assert get_content(thumb_url_a) != get_content(
        thumb_url_b
    ), "Binary content should be different"
    thumb_url_c = bahamas.create_url("api/thumbnail.png")
    assert get_content(thumb_url_a) == get_content(thumb_url_c), "Binary content should be the same"


def test_multiband(bahamas):
    url_a = bahamas.get_tile_url(
        indexes=[1, 2, 3],
    ).format(z=8, x=72, y=110)
    assert get_content(url_a)
    url_b = bahamas.get_tile_url(
        indexes=[3, 2, 1],
    ).format(z=8, x=72, y=110)
    assert get_content(url_b)
    url_c = bahamas.get_tile_url().format(z=8, x=72, y=110)
    assert get_content(url_c)
    # Check that other options are well handled
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmin=0,
        vmax=300,
        nodata=0,
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    # Check that band names are handled
    url = bahamas.get_tile_url(
        indexes=bahamas.band_names,
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail


def test_multiband_vmin_vmax(bahamas):
    # Check that other options are well handled
    url = bahamas.get_tile_url(
        indexes=[3, 2, 1],
        vmax=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    url = bahamas.get_tile_url(
        indexes=[3, 2, 1],
        vmin=[0, 10, 50],
        vmax=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    with pytest.raises(ValueError):
        bahamas.get_tile_url(
            vmax=[100, 200, 250],
        ).format(z=8, x=72, y=110)


def test_vmin_vmax(bahamas):
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmin=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmax=[20, 50, 70],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail
    url = bahamas.get_tile_url(
        indexes=[1, 2, 3],
        vmin=[20, 50, 70],
        vmax=[100, 200, 250],
    ).format(z=8, x=72, y=110)
    assert get_content(url)  # just make sure it doesn't fail


def test_launch_non_default_server(bahamas_file):
    default = TileClient(bahamas_file)
    diff = TileClient(bahamas_file, port=0)
    assert default.server != diff.server
    assert default.server_port != diff.server_port


def test_get_or_create_tile_client(bahamas_file):
    tile_client, _ = get_or_create_tile_client(bahamas_file)
    same, created = get_or_create_tile_client(tile_client)
    assert not created
    assert tile_client == same
    diff, created = get_or_create_tile_client(bahamas_file)
    assert created
    assert tile_client != diff
    with pytest.raises(RasterioIOError):
        _, _ = get_or_create_tile_client(__file__)


def test_open(bahamas_file):
    assert lts.open(bahamas_file)


def test_point(bahamas):
    assert bahamas.point(-77.76, 24.56, coord_crs="EPSG:4326")


@pytest.mark.parametrize("encoding", ["PNG", "JPEG", "JPG"])
def test_thumbnail_encodings(bahamas, encoding):
    thumbnail = bahamas.thumbnail(encoding=encoding)
    assert thumbnail  # TODO: check content
    assert isinstance(thumbnail, ImageBytes)
    output_path = get_cache_dir() / f"thumbnail.{encoding}"
    if output_path.exists():
        os.remove(output_path)
    thumbnail = bahamas.thumbnail(encoding=encoding, output_path=output_path)
    assert os.path.exists(output_path)


def test_thumbnail_bad_encoding(bahamas):
    with pytest.raises(ValueError):
        bahamas.thumbnail(encoding="foo")


def test_default_zoom(bahamas):
    assert bahamas.default_zoom == 7


@pytest.mark.skipif(skip_shapely, reason="shapely not installed")
def test_bounds_polygon(bahamas):
    poly = bahamas.bounds(return_polygon=True)
    assert isinstance(poly, Polygon)
    e = poly.bounds
    assert e[0] == pytest.approx(-78.9586, abs=TOLERANCE)
    assert e[1] == pytest.approx(23.5650, abs=TOLERANCE)
    assert e[2] == pytest.approx(-76.5749, abs=TOLERANCE)
    assert e[3] == pytest.approx(25.5509, abs=TOLERANCE)
    wkt = bahamas.bounds(return_wkt=True)
    assert isinstance(wkt, str)


@pytest.mark.skipif(skip_shapely, reason="shapely not installed")
def test_bounds_geojson(bahamas):
    poly = bahamas.bounds(return_polygon=True)
    assert isinstance(poly, Polygon)
    geojson = polygon_to_geojson(poly)
    assert isinstance(geojson, str)
    obj = json.loads(geojson)
    assert isinstance(obj[0], dict)


@pytest.mark.skipif(skip_shapely, reason="shapely not installed")
def test_center_shapely(bahamas):
    from shapely.geometry import Point

    pt = bahamas.center(return_point=True)
    assert isinstance(pt, Point)
    wkt = bahamas.center(return_wkt=True)
    assert parse_shapely(wkt)


def test_rasterio_property(bahamas):
    src = bahamas.dataset
    assert isinstance(src, rasterio.io.DatasetReaderBase)
    assert src == bahamas.dataset

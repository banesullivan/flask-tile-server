import concurrent.futures
import os
import pathlib
import uuid

import anywidget
import traitlets

from localtileserver.client import TileClient

THIS_DIR = pathlib.Path(__file__).parent.absolute()
THREAD_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())


def handle_custom_message(widget, msg: dict, buffers: list[bytes]) -> None:
    assert msg["kind"] == "get_tile", f"unexpected message kind: {msg['kind']}"

    def target():
        response, buffers = widget.get_tile(msg["msg"])
        widget.send(
            {
                "id": msg["id"],
                "response": response,
            },
            buffers,
        )

    # t = threading.Thread(target=target)
    # t.start()
    THREAD_EXECUTOR.submit(target)


class TileLayerWidget(anywidget.AnyWidget):
    """Leaflet Tile Layer Widget.

    Args:
        client (TileClient): A TileClient instance.
    """

    _esm = THIS_DIR / "lts_widget.js"
    _css = THIS_DIR / "lts_widget.css"

    bounds = traitlets.List([0, 0, 0, 0]).tag(sync=True, o=True)
    center = traitlets.List([0, 0]).tag(sync=True, o=True)
    identifier = traitlets.Unicode("").tag(sync=True, o=True)
    default_zoom = traitlets.Int(0).tag(sync=True, o=True)

    def __init__(self, client: TileClient, **kwargs):
        super().__init__()
        self.client = client  # TODO: weakref?
        self.on_msg(handle_custom_message)
        self._display_kwargs = kwargs
        self.bounds = self.client.bounds()
        self.identifier = uuid.uuid4().hex
        self.center = self.client.center()
        self.default_zoom = self.client.default_zoom

    def get_tile(self, msg):
        try:
            x = int(msg["x"])
            y = int(msg["y"])
            z = int(msg["z"])
        except (KeyError, ValueError) as e:
            return f"failed: {e}", []

        try:
            # NOTE: when calling from a thread executor, we need a different dataset handle for each thread
            # finding that the kernel crashes... is rio-tiler or rasterio not thread safe?
            c = TileClient(self.client.dataset.name)
            tile = c.tile(z=z, x=x, y=y, **self._display_kwargs)
        except Exception as e:
            return f"failed {e}", [b""]

        return "success", [tile]

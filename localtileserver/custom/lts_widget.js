// import ESM version of Leaflet
import * as L from "https://unpkg.com/leaflet@1.9.3/dist/leaflet-src.esm.js";

function render({ model, el, experimental }) {
    // Header
    let bounds = model.get("bounds");  // TODO: use these
    let identifier = model.get("identifier");

    console.log("Rendering localtileserver widget", identifier, bounds);

    const tileHandlers = {};

    L.TileLayer.LocalTileLayer = L.TileLayer.extend({
        initialize: function (options) {
            L.TileLayer.prototype.initialize.call(this, options);
            this.identifier = options.identifier;
        },
        createTile: function (coords, done) {
            // leaflet's calls cannot be async, so must use a callback to modify the img element
            var tile = document.createElement('img');

            // ID unique to this single tile request
            const id = Math.random().toString(36).substring(7);

            function handleTile(msg, buffers) {
                if (msg.id !== id) return;
                // console.log(msg)
                if (msg.response === "success") {
                    let blob = new Blob([buffers[0]], { type: "image/png" });
                    let url = URL.createObjectURL(blob);
                    tile.src = url;
                }
                done(null, tile);
                delete tileHandlers[id];
                // console.log(Object.keys(tileHandlers).length)
            }

            tileHandlers[id] = handleTile;

            model.send(
                { id, kind: "get_tile", msg: {...coords, identifier} },
                undefined,
                [],
            );

            return tile;
        },
        getAttribution: function() {
            return "Raster file served by <a href='https://github.com/banesullivan/localtileserver' target='_blank'>localtileserver</a>."
        }
    });

    L.tileLayer.localTileLayer = function(options) {
        return new L.TileLayer.LocalTileLayer(options);
    };

    function tileHandler(msg, buffers) {
        if (msg.id in tileHandlers) {
            tileHandlers[msg.id](msg, buffers);
        }
    }
    model.on("msg:custom", tileHandler);

    var layer = L.tileLayer.localTileLayer({ identifier: identifier });
    console.log(layer)

    // TODO: add tileLayer to map in ipyleaflet or folium
    // For now, here is a custom Leaflet map

    const container = document.createElement("div");
    container.style.width = '100%';
    container.style.height = '600px';

    const center = model.get("center");  // center of raster
    const zoom = model.get("default_zoom");
    const map = L.map(container).setView(center, zoom);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
            'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);

    layer.addTo(map);
    el.appendChild(container);
    setTimeout(function(){ map.invalidateSize()}, 400);

}

export default { render };

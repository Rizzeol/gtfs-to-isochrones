
import os

import requests
from flask import Flask, request, jsonify, Response, send_from_directory
from gtfs_graph.geo import get_isochrone, stops
from flask_cors import CORS
import json


app = Flask(__name__, static_url_path='/whatever')
CORS(app)


@app.route('/search', methods=['POST'])
def search():
    pois = request.json['poi']
    max_price = request.json['max_price']
    isochrone = None
    all_paths = list()
    for petit in pois:
        gs, paths = get_isochrone(petit['lat'], petit['lon'], petit['duration'])
        isochrone = gs if isochrone is None else isochrone.union(gs)
        all_paths = all_paths + paths
    r = requests.post('http://localhost:3000/annonces', headers={'Content-Type': 'application/json'}, data=json.dumps({
        'isochrone': isochrone.__geo_interface__,
        'max_price': max_price,
    }))
    matching_properties = r.json()
    matching_properties['paths'] = all_paths
    matching_properties['stops'] = get_stop_locations_from_paths(all_paths)
    matching_properties['geoJSON'] = isochrone.__geo_interface__
    return jsonify(matching_properties)


def root_dir():  # pragma: no cover
    return '/Users/ire/dev/lauzhack-front/build'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_resource(path):  # pragma: no cover
    path = 'index.html' if path == '' else path
    return send_from_directory(
        root_dir(),
        path
    )


def get_stop_locations_from_paths(paths):
    locations = dict()
    for path in paths:
        for target, intermediates in path.items():
            for stop in intermediates:
                if stop not in locations:
                    point = stops.get(stop)
                    locations[stop] = (point.y, point.x)
    return locations


if __name__ == '__main__':
    app.run(port=80)

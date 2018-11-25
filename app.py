
import requests
from flask import Flask, request, jsonify
from gtfs_graph.geo import get_isochrone, stops
from flask_cors import CORS
import json


app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Hello, world!'


@app.route('/search', methods=['POST'])
def search():
    pois = request.json['poi']
    max_price = request.json['max_price']
    isochrone = None
    all_paths = list()
    for petit in pois:
        gs, paths = get_isochrone(petit['lat'], petit['lon'], petit['duration'])
        isochrone = gs if isochrone is None else isochrone.union(gs)
        all_paths.append(paths)
    r = requests.post('http://localhost:3000/annonces', headers={'Content-Type': 'application/json'}, data=json.dumps({
        'isochrone': isochrone.__geo_interface__,
        'max_price': max_price,
    }))
    matching_properties = r.json()
    matching_properties['paths'] = all_paths
    matching_properties['stops'] = get_stop_locations_from_paths(all_paths)
    return jsonify(matching_properties)


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
    app.run()

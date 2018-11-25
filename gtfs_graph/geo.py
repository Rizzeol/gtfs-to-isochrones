
import pickle

import networkx as nx
import pyproj
from geopandas import GeoSeries
from shapely.geometry import Point
from shapely.ops import unary_union
from functools import partial
from shapely.ops import transform


graph = pickle.load(open('graph.pickle', 'rb'))
stops = pickle.load(open('stops.pickle', 'rb'))


def get_transform_partials(point):
    local_azimuthal_projection = f"+proj=aeqd +R=6371000 +units=m +lat_0={point.y} +lon_0={point.x}"
    wgs84_to_aeqd = partial(
        pyproj.transform,
        pyproj.Proj('+proj=longlat +datum=WGS84 +no_defs'),
        pyproj.Proj(local_azimuthal_projection),
    )
    aeqd_to_wgs84 = partial(
        pyproj.transform,
        pyproj.Proj(local_azimuthal_projection),
        pyproj.Proj('+proj=longlat +datum=WGS84 +no_defs'),
    )
    return wgs84_to_aeqd, aeqd_to_wgs84


def buffer_from_point(point, radius):
    wgs84_to_aeqd, aeqd_to_wgs84 = get_transform_partials(point)
    point_transformed = transform(wgs84_to_aeqd, point)
    buffer = point_transformed.buffer(radius)
    buffer_wgs84 = transform(aeqd_to_wgs84, buffer)
    return buffer_wgs84


def buffer_from_coordinates(lat, lon, radius):
    center = Point(lon, lat)
    return buffer_from_point(center, radius)


def get_distance_in_meters(a, b):
    wgs84_to_aeqd_a, aeqd_to_wgs84_a = get_transform_partials(a)
    a_transformed = transform(wgs84_to_aeqd_a, a)
    b_transformed = transform(wgs84_to_aeqd_a, b)
    return a_transformed.distance(b_transformed)


def get_contained_stops(buffer):
    contained_stops = dict()
    for stop, point in stops.items():
        if buffer.contains(point):
            contained_stops[stop] = point
    return contained_stops


def get_reachable_stops(current_stop, remaining_time):
    return nx.single_source_dijkstra(graph,
                                     current_stop.split(':')[0],
                                     cutoff=remaining_time)


def get_isochrone(source_lat, source_lon, remaining_time, walking_speed=50):
    """

    :param source_lat:
    :param source_lon:
    :param remaining_time: in minutes
    :param walking_speed:
    :return:
    """
    source = Point(source_lon, source_lat)
    radius = remaining_time * walking_speed
    source_buffer = buffer_from_coordinates(source_lat, source_lon, radius)
    available_stops = get_contained_stops(source_buffer)
    all_buffers = [(source_buffer, list())]
    for stop, point in available_stops.items():
        distance = get_distance_in_meters(source, point)
        spent_time = distance / walking_speed
        targets, paths = get_reachable_stops(stop, remaining_time - spent_time)
        for final_stop, used_time in targets.items():
            all_buffers.append((
                buffer_from_point(
                    stops.get(final_stop),
                    (remaining_time - spent_time - used_time) * walking_speed
                ),
                paths.get(final_stop),
            ))
    return all_buffers

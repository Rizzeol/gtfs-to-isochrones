
import os
import pickle

import networkx as nx
import pandas as pd


def create_graph(path, save_temporary=False):
    stops = pd.read_csv(os.path.join(path, 'stops.txt'))
    stop_times = pd.read_csv(os.path.join(path, 'stop_times.txt'))

    g = nx.DiGraph()
    g.add_nodes_from((str(r['stop_id']).split(':')[0], {
        'lat': r['stop_lat'],
        'lon': r['stop_lon'],
        'name': r['stop_name'],
    }) for i, r in stops.iterrows())
    g.add_weighted_edges_from(
        get_weighted_edges(stop_times, save_to_pickle=save_temporary))

    if save_temporary:
        pickle.dump(g, open('graph.pickle', 'wb'))

    return g


def get_weighted_edges(stop_times, save_to_pickle=False):
    def extract_all_travel_sections():
        all_sections = list()
        previous_row = None
        current_trip_id = None
        for i, row in stop_times.iterrows():
            if i % 1000000 == 0:
                print(i)
            read_trip_id = row['trip_id']
            if current_trip_id == read_trip_id:
                section = {
                    'from': str(previous_row['stop_id']).split(':')[0],
                    'to': str(row['stop_id']).split(':')[0],
                    'departure': previous_row['departure_time'],
                    'arrival': row['arrival_time'],
                }
                all_sections.append(section)
            else:
                current_trip_id = read_trip_id
            previous_row = row

        return all_sections

    def calculate_delta(row):
        d = row['departure'].split(':')
        a = row['arrival'].split(':')
        delta = (int(a[0]) - int(d[0])) * 60 + (int(a[1]) - int(d[1]))
        assert delta >= 0
        return delta

    df = pd.DataFrame(extract_all_travel_sections())
    df = df.dropna()
    df['time'] = df.apply(calculate_delta, axis=1)
    df = df.groupby(['from', 'to'], as_index=False).mean()
    df.time = df.time.apply(round)

    if save_to_pickle:
        df.to_pickle('sections.pickle')

    return ((r['from'], r['to'], r['time']) for i, r in df.iterrows())

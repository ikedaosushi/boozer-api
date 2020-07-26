from pathlib import Path
import re

from django.http import JsonResponse
from django.core.cache import cache
from rest_framework import serializers

import pandas as pd
from django_pandas.io import read_frame
from geopy import distance
from requests_html import HTMLSession

from .models import Station

# df_stations = pd.read_csv(Path(__file__).parent / "data/stations.csv")

# class StationMasterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Station
#         include = ["id", "station_id", "station_name", "lat", "lon"]

# class StationMasterListSerializer(serializers.ListSerializer):
#     child = StationMasterSerializer

def stations(request):
    df_stations = read_frame(Station.objects.all())
    df_stations = df_stations.sort_values("num_shop", ascending=False)
    resp = dict(
        hits=df_stations.shape[0],
        results=df_stations[["id", "station_id", "station_name", "lat", "lon"]].to_dict("records")
    )
    return JsonResponse(resp, safe=False, json_dumps_params={'ensure_ascii': False})

def _response400(self, message):
    return JsonResponse(dict(message=message), safe=False, json_dumps_params={'ensure_ascii': False}, status=400)


def election(request):
    station_ids = request.GET.getlist('station_id')
    if len(station_ids) < 2:
        _response400("station_id is required at least 2")
    try:
        station_ids = [int(station_id) for station_id in station_ids]
    except ValueError:
        _response400(f"station_id is invalid: {station_ids}")
    df_stations = read_frame(Station.objects.all())
    results = Election(df_stations, station_ids).run()
    response = dict(
        station_ids=station_ids,
        results=results
    )
    return JsonResponse(response, safe=False, json_dumps_params={'ensure_ascii': False})

class EkispertRouteTime:
    def __init__(self) -> None:
        self.session = HTMLSession()
        self.url = "https://roote.ekispert.net/ja/result"
        self.base_params = dict(
            hour=12, locale="ja", minute10=0,
            minute1=0, sort="time"
        )

    def get(self, arr_station_id, dep_station_id):
        params = dict(**self.base_params, arr_code=arr_station_id, dep_code=dep_station_id)
        print(self.url)
        res = self.session.get(self.url, params=params)
        target_text = res.html.find('.candidate_list_txt > .orange_txt', first=True).text
        time = int(re.search(r'（\D*(\d+)分）', target_text).groups()[0])

        return time


class Election:
    def __init__(self, df_stations, station_ids):
        self.df_stations = df_stations
        self.station_ids = station_ids
        self.ekispert_route_time = EkispertRouteTime()

    def _partial_get_time(self, arr_station_id, dep_station_id):
        key = "_".join(str(s_id) for s_id in sorted([arr_station_id, dep_station_id]))
        # if key in cache:
        #     return arr_station_id, cache.get(key)
        time = self.ekispert_route_time.get(arr_station_id, dep_station_id)
        cache.set(key, time, None)
        return arr_station_id, time

    def _station_with_distance(self):
        candidate_stations = self.df_stations.query("station_id in @self.station_ids")
        halfway_coords = candidate_stations['lat'].mean(), candidate_stations['lon'].mean()
        ds = []
        for coords in self.df_stations[['lat', 'lon']].values:
            d = distance.distance(halfway_coords, coords.tolist())
            ds.append(d)

        df_stations = self.df_stations[['station_id', 'station_name', 'lat', 'lon', 'num_shop', 'top10_avarage_score']]
        df_stations['distance'] = ds

        return df_stations

    def run(self):
        df_stations = self._station_with_distance()
        station_id_names = df_stations.set_index("station_id")['station_name'].to_dict()
        results = []
        for _, row in df_stations.sort_values('distance').head(10).iterrows():
            candidate_station_id = row['station_id']
            result = dict(candidate_station=row.drop("distance").to_dict())
            for station_id in self.station_ids:
                staion_times = [self._partial_get_time(station_id, candidate_station_id) for station_id in self.station_ids]
                result['station_times'] = [dict(station_id=t[0], station_name=station_id_names[t[0]], time=t[1]) for t in staion_times]
                times = [r['time'] for r in result['station_times']]
                sum_ = sum(times)
                diff = max(times) - min(times)
                result['indicater'] = sum_ + diff
            results.append(result)
            
        results = sorted(results, key=lambda result: result['indicater'])

        return results
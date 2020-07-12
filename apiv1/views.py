from pathlib import Path
import re

from django.shortcuts import render
from django.http import JsonResponse
from django.core.cache import cache

import pandas as pd
from django_pandas.io import read_frame
from geopy import distance
from requests_html import HTMLSession

from .models import Station

# df_stations = pd.read_csv(Path(__file__).parent / "data/stations.csv")

def stations(request):
    df_stations = read_frame(Station.objects.all())
    resp = dict(
        hits=df_stations.shape[0],
        results=df_stations.to_dict("records")
    )
    return JsonResponse(resp, safe=False, json_dumps_params={'ensure_ascii': False})


class Election:
    def __init__(self):
        self.session = HTMLSession()
        self.url = "https://roote.ekispert.net/ja/result"
        self.base_params = dict(
            hour=12, locale="ja", minute10=0,
            minute1=0, sort="time"
        )

    def _partial_get_time(self, arr_station_id, dep_station_id):
        key = "_".join(str(s_id) for s_id in sorted([arr_station_id, dep_station_id]))
        if key in cache:
            return arr_station_id, cache.get(key)
        params = dict(**self.base_params, arr_code=arr_station_id, dep_code=dep_station_id)
        res = self.session.get(self.url, params=params)
        target_text = res.html.find('.candidate_list_txt > .orange_txt', first=True).text
        time = int(re.search(r'（\D*(\d+)分）', target_text).groups()[0])

        cache.set(key, time, None)
        return arr_station_id, time

    def _response400(self, message):
        return JsonResponse(dict(message=message), safe=False, json_dumps_params={'ensure_ascii': False}, status=400)

    def run(self, request):
        station_ids = request.GET.getlist('station_id')
        if len(station_ids) < 2:
            self._response400("station_id is required at least 2")
        try:
            station_ids = [int(station_id) for station_id in station_ids]
        except ValueError:
            self._response400(f"station_id is invalid: {station_ids}")


        df_stations = read_frame(Station.objects.all())
        candidate_stations = df_stations.query("station_id in @station_ids")
        halfway_coords = candidate_stations['lat'].mean(), candidate_stations['lon'].mean()
        ds = []
        for coords in df_stations[['lat', 'lon']].values:
            d = distance.distance(halfway_coords, coords.tolist())
            ds.append(d)

        stations = df_stations[['station_id', 'station_name', 'lat', 'lon', 'num_shop', 'top10_avarage_score']]
        stations['distance'] = ds
        results = []
        for _, row in stations.sort_values('distance').head(10).iterrows():
            candidate_station_id = row['station_id']
            result = dict(candidate_station=row.drop("distance").to_dict())
            for station_id in station_ids:
                staion_times = [self._partial_get_time(station_id, candidate_station_id) for station_id in station_ids]
                result['staion_times'] = [dict(station_id=t[0], time=t[1]) for t in staion_times]
                times = [r['time'] for r in result['staion_times']]
                sum_ = sum(times)
                diff = max(times) - min(times)
                result['indicater'] = sum_ + diff
            results.append(result)
            
        results = sorted(results, key=lambda result: result['indicater'])
        res = dict(
            station_ids=station_ids,
            results=results
        )
        return JsonResponse(res, safe=False, json_dumps_params={'ensure_ascii': False})

election = Election()
from time import sleep
from pathlib import Path
import xml.etree.ElementTree as ET

from requests_html import HTMLSession
import numpy as np
import pandas as pd
import re
from django_cron import CronJobBase, Schedule

from apiv1.models import Station



class CrawlTabelog:
    def __init__(self) -> None:
        site_xml_pah = Path(__file__).parent / "data/sitemap_pc_rst_station_1.xml"
        with open(site_xml_pah) as f:
            tree = ET.parse(f)
        root = tree.getroot()
        items = list(root)
        urls = [list(item)[0].text for item in items]
        urls = [url for url in urls if "tokyo" in url]
        self.urls = list(set(urls))
        self.params = dict(
            SrtT="rt", sort_mode=1, Srt="D"
        )
        self.sess = HTMLSession()

    def run(self):
        for url in self.urls:
            try:
                resp = self.sess.get(url, params=self.params)
                station_name = resp.html.find(".list-sidebar__item-title", first=True).text.replace("駅", "")
                ratings = resp.html.find(".list-rst__rating-val")
                top10_avarage_score = np.mean([float(rating.text) for rating in ratings])
                count = resp.html.find(".c-page-count", first=True).text
                num_shop = re.findall("\d+", count)[-1]

                qs = Station.objects.filter(station_name=station_name)
                if qs.exists():
                    station = list(qs)[0]
                    station.tabelog_url = url
                    station.top10_avarage_score = top10_avarage_score
                    station.num_shop = num_shop
                    station.save()
                sleep(1)
            except:
                print(f"error: {url}")

class TabelogCrawlCron(CronJobBase):
    RUN_EVERY_MINS = 1440

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'boozer_api.tabelog_crawl'

    def do(self):
        CrawlTabelog().run()
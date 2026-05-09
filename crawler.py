from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

from .config import BAIDU_TRAFFIC_REALTIME_URL, DEFAULT_CITY_CODE


def wait_for_next_interval(minutes: int = 5, offset_seconds: int = 30) -> None:
    now = datetime.now()
    next_time = (
        now
        + timedelta(minutes=minutes - now.minute % minutes, seconds=offset_seconds - now.second)
    ).replace(microsecond=0)
    sleep(max((next_time - datetime.now()).total_seconds(), 0))


class TrafficRankCrawler:
    def __init__(self, browser_path: str | None = None, city_code: str = DEFAULT_CITY_CODE):
        from DrissionPage import ChromiumOptions, ChromiumPage

        options = ChromiumOptions()
        if browser_path:
            options.set_browser_path(browser_path)
        self.page = ChromiumPage(options)
        self.city_code = city_code

    def start(self) -> None:
        self.page.listen.start("roadrank")

    def open_road_rank(self) -> None:
        self.page.get(f"{BAIDU_TRAFFIC_REALTIME_URL}?cityCode={self.city_code}")
        self.page.refresh()
        rank = self.page.ele("css:.realCongestRank--Pp8ke")
        if not rank:
            raise RuntimeError("Could not find realtime congestion rank panel.")

        for tab in rank.eles("css:.tabs--jxXA1 li"):
            if tab.text == "道路":
                tab.click()
                sleep(2)
                return
        raise RuntimeError("Could not find road tab in rank panel.")

    def capture_snapshots(
        self,
        output_dir: Path,
        file_prefix: str,
        start_index: int = 1,
        packets_per_round: int = 3,
        packet_interval_seconds: int = 40,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self.start()
        index = start_index
        previous_payload = None

        while True:
            self.open_road_rank()
            for packet_index in range(packets_per_round):
                packet = self.page.listen.wait()
                payload = packet.response.body
                if payload != previous_payload:
                    output_path = output_dir / f"{file_prefix} {index}.json"
                    output_path.write_text(
                        json.dumps(payload, ensure_ascii=False, indent=4),
                        encoding="utf-8",
                    )
                    previous_payload = payload
                    index += 1
                if packet_index < packets_per_round - 1:
                    sleep(packet_interval_seconds)
            wait_for_next_interval()

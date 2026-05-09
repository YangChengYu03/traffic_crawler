from __future__ import annotations

import json
from pathlib import Path
from time import sleep
from typing import Mapping

import pandas as pd
import requests

from .config import BAIDU_ROAD_CURVE_URL, DEFAULT_CITY_CODE


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135 Safari/537.36"
    ),
}


def load_cookies(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def download_road_curves(
    road_id_csv: Path,
    output_dir: Path,
    city_code: str = DEFAULT_CITY_CODE,
    cookies: Mapping[str, str] | None = None,
    delay_seconds: float = 0.2,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    road_ids = pd.read_csv(road_id_csv)["roadsegid"].dropna().astype(str)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    if cookies:
        session.cookies.update(dict(cookies))

    for road_id in road_ids:
        output_path = output_dir / f"{output_dir.name}{road_id}.json"
        if output_path.exists():
            continue

        response = session.get(
            BAIDU_ROAD_CURVE_URL,
            params={"cityCode": city_code, "id": road_id, "from": ""},
            timeout=30,
        )
        response.raise_for_status()
        output_path.write_text(
            json.dumps(response.json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        sleep(delay_seconds)

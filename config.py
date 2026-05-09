from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path = Path(".")
    road_dir: Path = Path("road")
    road_id_dir: Path = Path("roadId")

    @property
    def road_data_csv(self) -> Path:
        return self.road_dir / "road_data.csv"

    @property
    def road_ids_csv(self) -> Path:
        return self.road_dir / "roadsegidAll.csv"


BAIDU_TRAFFIC_REALTIME_URL = (
    "https://jiaotong.baidu.com/congestion/city/urbanrealtime"
)
BAIDU_ROAD_CURVE_URL = "https://jiaotong.baidu.com/trafficindex/city/roadcurve/"

DEFAULT_CITY_CODE = "163"

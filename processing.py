from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from .geo import bd09_to_wgs84


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8", "gbk", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def extract_road_ids(json_files: Iterable[Path], output_csv: Path) -> pd.DataFrame:
    road_ids: list[str] = []
    seen: set[str] = set()

    for json_file in json_files:
        payload = load_json(json_file)
        rows = payload.get("data", {}).get("list") or []
        for row in rows:
            road_id = row.get("roadsegid")
            if road_id and road_id not in seen:
                seen.add(road_id)
                road_ids.append(road_id)

    df = pd.DataFrame({"roadsegid": road_ids})
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def merge_road_id_csvs(input_csvs: Iterable[Path], output_csv: Path) -> pd.DataFrame:
    road_ids: list[str] = []
    seen: set[str] = set()

    for csv_path in input_csvs:
        df = read_csv_with_fallback(csv_path)
        if "roadsegid" not in df.columns:
            raise ValueError(f"{csv_path} is missing column: roadsegid")
        for road_id in df["roadsegid"].dropna().astype(str):
            if road_id not in seen:
                seen.add(road_id)
                road_ids.append(road_id)

    result = pd.DataFrame({"roadsegid": road_ids})
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)
    return result


def build_road_data(
    road_id_csv: Path,
    json_root: Path,
    output_csv: Path,
    year_month: str = "202505",
    days: Iterable[int] = range(1, 31),
) -> pd.DataFrame:
    road_ids = read_csv_with_fallback(road_id_csv)["roadsegid"].dropna().astype(str)
    rows: list[dict] = []

    for day in days:
        day_dir = json_root / f"5.{day}"
        date_prefix = f"{year_month}{day:02d}"
        for road_id in road_ids:
            json_path = day_dir / f"5.{day}{road_id}.json"
            if not json_path.exists():
                continue

            road_name = _road_name_from_id(road_id)
            payload = load_json(json_path)
            curve = payload.get("data", {}).get("curve") or []
            for item in curve:
                rows.append(
                    {
                        "roadName": road_name,
                        "roadSegid": item.get("roadsegid", road_id),
                        "Time": date_prefix + str(item.get("datatime", "")).replace(":", ""),
                        "congestIndex": item.get("congestIndex"),
                        "congestLength": item.get("congestLength"),
                        "speed": item.get("speed"),
                    }
                )

    df = pd.DataFrame(
        rows,
        columns=["roadName", "roadSegid", "Time", "congestIndex", "congestLength", "speed"],
    )
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def export_road_geometry(road_id_csv: Path, json_dir: Path, output_csv: Path) -> pd.DataFrame:
    road_ids = read_csv_with_fallback(road_id_csv)["roadsegid"].dropna().astype(str)
    rows: list[dict] = []

    for road_id in road_ids:
        json_path = _find_curve_json(json_dir, road_id)
        if not json_path:
            continue

        payload = load_json(json_path)
        data = payload.get("data", {})
        curve = data.get("curve") or []
        road_seg_id = curve[0].get("roadsegid", road_id) if curve else road_id
        road_name = _road_name_from_id(road_seg_id)

        for location in data.get("location") or []:
            coords = [float(value) for value in location.split(",")]
            for index in range(0, len(coords) - 2, 2):
                start_x, start_y = bd09_to_wgs84(coords[index], coords[index + 1])
                end_x, end_y = bd09_to_wgs84(coords[index + 2], coords[index + 3])
                rows.append(
                    {
                        "roadName": road_name,
                        "roadsegid": road_seg_id,
                        "START_X": start_x,
                        "START_Y": start_y,
                        "END_X": end_x,
                        "END_Y": end_y,
                    }
                )

    df = pd.DataFrame(rows, columns=["roadName", "roadsegid", "START_X", "START_Y", "END_X", "END_Y"])
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    return df


def export_congestion_at_time(
    input_csv: Path,
    output_csv: Path,
    year_month: str = "202505",
    hhmm: str = "0800",
) -> pd.DataFrame:
    df = pd.read_csv(input_csv)
    df["Time"] = df["Time"].astype(str).str.zfill(12)
    df["date"] = df["Time"].str[:8]
    mask = df["Time"].str.startswith(year_month) & (df["Time"].str[-4:] == hhmm)
    result = df.loc[mask, ["roadSegid", "date", "congestIndex"]].sort_values(["roadSegid", "date"])
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False)
    return result


def pivot_congestion(input_csv: Path, output_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(input_csv)
    table = df.pivot_table(index="roadSegid", columns="date", values="congestIndex", aggfunc="mean")
    table.to_csv(output_csv)
    return table


def _road_name_from_id(road_id: str) -> str:
    match = re.match(r"(.*?)-", road_id)
    return match.group(1) if match else road_id


def _find_curve_json(json_dir: Path, road_id: str) -> Path | None:
    candidates = sorted(json_dir.glob(f"*{road_id}.json"))
    return candidates[0] if candidates else None

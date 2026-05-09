from __future__ import annotations

import argparse
import glob
from pathlib import Path

from .crawler import TrafficRankCrawler
from .processing import (
    build_road_data,
    export_congestion_at_time,
    export_road_geometry,
    extract_road_ids,
    merge_road_id_csvs,
    pivot_congestion,
)
from .road_curve import download_road_curves, load_cookies


def expand_paths(paths: list[Path]) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        path_text = str(path)
        if "*" in path_text or "?" in path_text:
            expanded.extend(Path(match) for match in sorted(glob.glob(path_text)))
        else:
            expanded.append(path)
    return expanded


def main() -> None:
    parser = argparse.ArgumentParser(prog="traffic-crawler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rank = subparsers.add_parser("crawl-rank")
    rank.add_argument("--output-dir", type=Path, required=True)
    rank.add_argument("--prefix", required=True)
    rank.add_argument("--city-code", default="163")
    rank.add_argument("--browser-path")
    rank.add_argument("--start-index", type=int, default=1)

    extract = subparsers.add_parser("extract-roadids")
    extract.add_argument("--input-dir", type=Path, required=True)
    extract.add_argument("--pattern", default="*.json")
    extract.add_argument("--output", type=Path, required=True)

    merge = subparsers.add_parser("merge-roadids")
    merge.add_argument("--inputs", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, required=True)

    curves = subparsers.add_parser("download-curves")
    curves.add_argument("--road-id-csv", type=Path, required=True)
    curves.add_argument("--output-dir", type=Path, required=True)
    curves.add_argument("--city-code", default="163")
    curves.add_argument("--cookies-json", type=Path)
    curves.add_argument("--delay", type=float, default=0.2)

    road_data = subparsers.add_parser("build-road-data")
    road_data.add_argument("--road-id-csv", type=Path, required=True)
    road_data.add_argument("--json-root", type=Path, required=True)
    road_data.add_argument("--output", type=Path, required=True)
    road_data.add_argument("--year-month", default="202505")
    road_data.add_argument("--start-day", type=int, default=1)
    road_data.add_argument("--end-day", type=int, default=30)

    geometry = subparsers.add_parser("export-geometry")
    geometry.add_argument("--road-id-csv", type=Path, required=True)
    geometry.add_argument("--json-dir", type=Path, required=True)
    geometry.add_argument("--output", type=Path, required=True)

    at_time = subparsers.add_parser("export-time")
    at_time.add_argument("--input", type=Path, required=True)
    at_time.add_argument("--output", type=Path, required=True)
    at_time.add_argument("--year-month", default="202505")
    at_time.add_argument("--hhmm", default="0800")

    pivot = subparsers.add_parser("pivot")
    pivot.add_argument("--input", type=Path, required=True)
    pivot.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "crawl-rank":
        crawler = TrafficRankCrawler(browser_path=args.browser_path, city_code=args.city_code)
        crawler.capture_snapshots(args.output_dir, args.prefix, start_index=args.start_index)
    elif args.command == "extract-roadids":
        extract_road_ids(sorted(args.input_dir.glob(args.pattern)), args.output)
    elif args.command == "merge-roadids":
        merge_road_id_csvs(expand_paths(args.inputs), args.output)
    elif args.command == "download-curves":
        download_road_curves(
            args.road_id_csv,
            args.output_dir,
            city_code=args.city_code,
            cookies=load_cookies(args.cookies_json),
            delay_seconds=args.delay,
        )
    elif args.command == "build-road-data":
        days = range(args.start_day, args.end_day + 1)
        build_road_data(args.road_id_csv, args.json_root, args.output, args.year_month, days)
    elif args.command == "export-geometry":
        export_road_geometry(args.road_id_csv, args.json_dir, args.output)
    elif args.command == "export-time":
        export_congestion_at_time(args.input, args.output, args.year_month, args.hhmm)
    elif args.command == "pivot":
        pivot_congestion(args.input, args.output)

if __name__ == "__main__":
    main()

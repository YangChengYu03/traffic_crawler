# Traffic Crawler

这是一个面向百度交通拥堵数据的采集和清洗项目。旧脚本和原始数据仍保留在仓库中；新的重构代码位于 `traffic_crawler/`，把浏览器抓取、接口下载、数据汇总和坐标转换拆成了独立模块。

## 主要数据流

1. 抓取实时拥堵榜接口数据，保存到 `roadId/<日期>/`。
2. 从拥堵榜 JSON 中提取 `roadsegid`，合并成 `roadsegidAll.csv`。
3. 根据 `roadsegid` 下载每个路段的全天曲线 JSON，保存到 `road/<日期>/`。
4. 汇总 JSON 中的 `curve` 字段，生成 `road/road_data.csv`。
5. 可选：从 `location` 字段导出 WGS84 路段线段坐标。
6. 可选：筛选指定时刻的拥堵指数，并生成透视表用于后续分析。

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 常用命令

提取某天拥堵榜里的路段 ID：

```powershell
python -m traffic_crawler.cli extract-roadids --input-dir roadId/4.30 --output roadId/roadsegid/roadsegid4.30.csv
```

合并多个日期的路段 ID：

```powershell
python -m traffic_crawler.cli merge-roadids --inputs roadId/roadsegid/*.csv --output road/roadsegidAll.csv
```

生成路段拥堵明细 CSV：

```powershell
python -m traffic_crawler.cli build-road-data --road-id-csv road/roadsegidAll.csv --json-root road --output road/road_data.csv --year-month 202505 --start-day 1 --end-day 30
```

导出 08:00 拥堵指数：

```powershell
python -m traffic_crawler.cli export-time --input road/road_data.csv --output road/filtered_congestion_data.csv --year-month 202505 --hhmm 0800
python -m traffic_crawler.cli pivot --input road/filtered_congestion_data.csv --output road/congestion_pivot_table_202505_0800.csv
```

## 当前项目结构

```text
E:\traffic
├── traffic_crawler/          # 新增重构代码
├── road/                     # 路段曲线 JSON、汇总 CSV 等数据
├── roadId/                   # 实时拥堵榜 JSON、路段 ID CSV
├── README.txt                # 原始说明
├── README.md                 # 重构后的说明
├── get_RoadID.py             # 原始浏览器抓取脚本
├── script.py                 # 原始测试脚本
├── requirements.txt          # 依赖清单
├── 5月天气.xlsx
└── 5月空气指数.xlsx
```

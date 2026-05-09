# Traffic Crawler

`traffic_crawler` 是一个用于采集和整理百度交通拥堵数据的 Python 项目。项目当前聚焦于数据获取、路段 ID 提取、路段曲线数据汇总、坐标转换和按时间筛选分析，不包含模型训练或预测模块。

## 功能概览

- 使用浏览器监听方式采集百度交通实时拥堵榜数据。
- 从拥堵榜 JSON 中提取唯一 `roadsegid`。
- 合并多个日期的路段 ID 文件，生成统一路段清单。
- 根据路段 ID 下载路段全天拥堵曲线 JSON。
- 将路段曲线 JSON 汇总为结构化 CSV。
- 将百度坐标转换为 WGS84 坐标并导出路段线段。
- 筛选指定月份、指定时刻的拥堵指数，并生成透视表。

## 项目结构

```text
traffic_crawler/
├── __init__.py          # 包版本信息
├── cli.py               # 命令行入口
├── config.py            # 默认配置与接口地址
├── crawler.py           # 实时拥堵榜浏览器监听抓取
├── road_curve.py        # 路段曲线接口下载
├── processing.py        # JSON/CSV 数据处理
├── geo.py               # BD09、GCJ02、WGS84 坐标转换
├── requirements.txt     # 项目依赖
├── .gitignore
└── README.md
```

## 环境准备

建议使用 Python 3.10 或更高版本。

```powershell
pip install -r requirements.txt
```

浏览器监听抓取依赖 `DrissionPage`，需要本机已安装 Chrome、Edge 或其他 Chromium 内核浏览器。若浏览器路径不是默认路径，请在运行 `crawl-rank` 时通过 `--browser-path` 指定。

## 数据流程

典型流程如下：

1. 抓取实时拥堵榜 JSON。
2. 从拥堵榜 JSON 提取路段 ID。
3. 合并多个日期的路段 ID。
4. 根据路段 ID 下载路段曲线 JSON。
5. 汇总路段曲线，生成 `road_data.csv`。
6. 可选导出路段坐标或指定时刻的拥堵指数。

推荐的数据目录放在项目外部，例如：

```text
E:\traffic
├── traffic_crawler/     # 本项目代码仓库
├── roadId/              # 实时拥堵榜 JSON 与 roadsegid CSV
└── road/                # 路段曲线 JSON 与汇总 CSV
```

## 命令行使用

查看全部命令：

```powershell
python -m traffic_crawler.cli --help
```

### 抓取实时拥堵榜

```powershell
python -m traffic_crawler.cli crawl-rank `
  --output-dir ../roadId/4.30 `
  --prefix "4.30" `
  --city-code 163 `
  --browser-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" `
  --start-index 1
```

该命令会持续运行并监听包含 `roadrank` 的网络响应，将不同响应保存为 JSON 文件。

### 提取单日路段 ID

```powershell
python -m traffic_crawler.cli extract-roadids `
  --input-dir ../roadId/4.30 `
  --output ../roadId/roadsegid/roadsegid4.30.csv
```

### 合并多日路段 ID

```powershell
python -m traffic_crawler.cli merge-roadids `
  --inputs ../roadId/roadsegid/*.csv `
  --output ../road/roadsegidAll.csv
```

### 下载路段曲线 JSON

```powershell
python -m traffic_crawler.cli download-curves `
  --road-id-csv ../road/roadsegidAll.csv `
  --output-dir ../road/5.1 `
  --city-code 163
```

如果接口需要 Cookie，可将 Cookie 保存为 JSON 文件后传入：

```powershell
python -m traffic_crawler.cli download-curves `
  --road-id-csv ../road/roadsegidAll.csv `
  --output-dir ../road/5.1 `
  --cookies-json cookies.json
```

### 生成路段拥堵明细 CSV

```powershell
python -m traffic_crawler.cli build-road-data `
  --road-id-csv ../road/roadsegidAll.csv `
  --json-root ../road `
  --output ../road/road_data.csv `
  --year-month 202505 `
  --start-day 1 `
  --end-day 30
```

输出字段：

```text
roadName, roadSegid, Time, congestIndex, congestLength, speed
```

### 导出路段坐标

```powershell
python -m traffic_crawler.cli export-geometry `
  --road-id-csv ../road/roadsegidAll.csv `
  --json-dir ../road/5.1 `
  --output ../road/roadsegid_location.csv
```

输出坐标为 WGS84，经纬度字段包括 `START_X`、`START_Y`、`END_X`、`END_Y`。

### 筛选指定时刻拥堵指数

```powershell
python -m traffic_crawler.cli export-time `
  --input ../road/road_data.csv `
  --output ../road/filtered_congestion_data.csv `
  --year-month 202505 `
  --hhmm 0800
```

### 生成透视表

```powershell
python -m traffic_crawler.cli pivot `
  --input ../road/filtered_congestion_data.csv `
  --output ../road/congestion_pivot_table_202505_0800.csv
```

## 注意事项

- 本项目只管理代码，不建议将大批量 JSON、CSV、模型文件或图表提交到 Git 仓库。
- `download-curves` 访问外部接口时可能受到 Cookie、频率限制或接口变更影响。
- `crawl-rank` 依赖网页结构和接口名称，如果百度交通页面更新，可能需要同步调整 CSS 选择器或监听关键字。
- 当前项目不包含 LSTM、深度学习训练或预测逻辑。

## 许可证

当前仓库尚未指定许可证。如需公开复用，建议补充 `LICENSE` 文件。

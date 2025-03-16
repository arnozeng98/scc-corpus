# 加拿大最高法院刑事案例语料库收集

## 概述

本文档介绍了从加拿大最高法院（SCC）收集刑事案例语料库的现阶段实现。该系统从SCC网站抓取案例数据，过滤出刑事案例，提取相关信息，并以结构化JSON格式存储以供进一步分析和NLP应用使用。

## 技术架构

数据收集系统由三个主要组件组成：

1. **网页抓取器（`scraper.py`）**：处理与SCC数据库的网络交互
2. **标注器（`annotator.py`）**：处理HTML文件并提取结构化数据
3. **主控制器（`main.py`）**：协调抓取和标注工作流程

### 网页抓取器

抓取器使用Selenium WebDriver构建，实现以下功能：

- **搜索自动化**：自动向SCC数据库提交带有可配置日期范围的搜索查询
- **结果解析**：导航搜索结果页面并提取各个案例的链接
- **案例下载**：下载每个案例的完整HTML内容
- **状态管理**：维护已抓取链接的记录以避免重复

主要函数：

- `setup_driver()`：配置并初始化Chrome WebDriver实例
- `load_scraped_links()`：加载先前下载的案例以避免重复
- `save_scraped_link()`：记录带有案例编号的抓取链接
- `scrape_cases()`：从搜索结果页面提取所有案例链接
- `save_cases()`：下载并保存每个案例的HTML内容
- `perform_search()`：协调整个搜索和下载过程

### 标注器

标注器处理下载的HTML文件以提取关于每个案例的结构化信息：

- **元数据提取**：标题、案例编号、日期、法官等
- **事实提取**：识别并提取每个案例的"事实"部分
- **法规识别**：提取案例中引用的与刑事法相关的法规
- **过滤**：确保只包含具有完整信息的刑事案例
- **统计生成**：计算并记录语料库统计信息

主要函数：

- `extract_facts()`：从案例HTML中提取"事实"部分
- `extract_statutes()`：识别案例中引用的相关刑事法规
- `find_original_url()`：检索每个案例的原始源URL
- `annotate_cases()`：处理所有案例并输出JSON的主要函数

### 数据流

1. 主控制器在指定的日期范围内启动搜索
2. 网页抓取器收集案例链接并下载HTML内容
3. 标注器处理HTML文件以提取结构化数据
4. 创建包含所有刑事案例的单个JSON文件
5. 生成统计文件提供语料库指标

## 安装

### 先决条件

- Python 3.8或更高版本
- Chrome浏览器（用于WebDriver）

### 依赖项

安装依赖项：

```bash
pip install selenium beautifulsoup4 webdriver-manager tqdm
```

## 运行系统

系统可以通过main.py文件运行。默认配置将在预定义的日期范围内搜索刑事案例。

### 基本执行

```bash
cd backend
python src/main.py
```

### 配置

运行前，您可能需要修改`config.py`中的以下设置：

- `DATE_RANGES`：定义搜索时间段的元组列表
- `RAW_HTML_DIR`：存储HTML文件的目录
- `CRIMINAL_CASES_OUTPUT`：输出JSON文件的路径
- `LOG_FILE`：写入日志的路径

配置示例：

```python
# Chrome Driver配置
CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "chromedriver")

# 其他设置
TIMEOUT = 10     # Selenium等待超时（秒）
HEADLESS = True  # 是否使用无头模式

# 基于日期范围生成搜索URL
SEARCH_URLS = generate_date_range_urls(BASE_URL, subject_id="16")

# 日志文件路径
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SCRAPER_LOG_FILE = os.path.join(LOGS_DIR, "scraper.log")
MAIN_LOG_FILE = os.path.join(LOGS_DIR, "main.log")
ANNOTATOR_LOG_FILE = os.path.join(LOGS_DIR, "annotator.log")

# 数据存储路径
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SCRAPED_LINKS_FILE = os.path.join(PROCESSED_DIR, "scraped_links.json")
CRIMINAL_CASES_OUTPUT = os.path.join(PROCESSED_DIR, "annotation.json")
```

### 运行有限结果（测试）

出于测试目的，您可以通过在`main.py`中修改`perform_search`函数调用来限制下载的案例数量：

```python
# 每个日期范围限制为10个案例进行测试
perform_search(driver, start_date, end_date, max_cases=10)
```

## 手动检查结果

要手动验证结果：

1. 检查生成的JSON文件的结构：

   ```bash
   cat data/processed/annotation.json | jq
   ```

2. 查看统计文件：

   ```bash
   cat data/processed/annotation_statistics.json | jq
   ```

3. 检查日志文件是否有警告或错误：

   ```bash
   cat logs/scraper.log
   cat logs/annotator.log
   ```

## 数据结构

### 输出格式

刑事案例以JSON文件存储，具有以下结构：

```json
[
  {
    "Title": "R. v. Smith",
    "Collection": "Supreme Court Judgments",
    "Date": "March 1, 2021",
    "Neutral Citation": "2021 SCC 10",
    "Case Number": "39227",
    "Judges": "Wagner C.J. and Abella, Moldaver, Karakatsanis, Côté, Brown, Rowe, Martin and Kasirer JJ.",
    "On Appeal From": "Court of Appeal for Ontario",
    "Subjects": "Criminal law",
    "Statutes and Regulations Cited": ["Criminal Code, R.S.C. 1985, c. C-46, s. 486"],
    "Facts": "The defendant was charged with...",
    "Original URL": "https://scc-csc.lexum.com/scc-csc/scc-csc/en/item/1989/index.do"
  },
  ...
]
```

### 统计

单独的统计文件包括：

```json
{
  "name": "SCC Criminal Cases Corpus Statistics",
  "description": "Statistical analysis of the Supreme Court of Canada criminal cases corpus",
  "generation_date": "2023-05-15",
  "corpus_overview": {
    "total_cases": 123,
    "year_range": "1985 - 2023",
    "total_characters": 1234567,
    "estimated_tokens": 308642
  },
  "case_length": {
    "average_tokens": 2509,
    "average_characters": 10037,
    "min_tokens": 782,
    "min_case": "R. v. Smith",
    "max_tokens": 6543,
    "max_case": "R. v. Jones"
  },
  "legal_content": {
    "total_statutes": 456,
    "average_statutes_per_case": 3.71
  }
}
```

## 已知限制

- 案例检测依赖于一致的HTML结构，这可能会偶尔变化
- 当前系统处理常见变体，但可能会忽略一些非标准案例
- 如果没有明确标记，词汇检测可能会遗漏一些相关的刑事案例
- 统计中的token估计是近似的（4个字符≈1个token）

## 当前开发状态

- [x] 基本网页抓取功能
- [x] HTML解析和元数据提取
- [x] 刑事案例过滤
- [x] 事实和法规提取
- [x] 原始URL记录和添加到标注数据
- [x] 语料库统计生成
- [ ] 更精确的token计数（当前使用估计值）
- [ ] 自动化测试套件

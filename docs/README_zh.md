# SCC Corpus - 加拿大最高法院刑事案例语料库

## 项目概述

SCC Corpus 是一个用于从加拿大最高法院（Supreme Court of Canada）网站收集、处理和分析刑事案例的工具。该项目旨在创建一个结构化的刑事案例语料库，可用于法律文本分析、NLP研究和法律信息检索应用。

### 主要功能

- **自动化数据收集**：使用网络爬虫从SCC网站抓取案例数据
- **智能筛选机制**：自动识别并提取刑事相关案例
- **结构化数据提取**：从案例HTML中解析关键元数据、事实陈述和引用法条
- **断点续写支持**：支持中断后继续抓取，避免重复工作
- **语料库统计**：提供关于语料库大小、内容分布和文本特征的详细统计

## 项目结构

```bash
scc-corpus/
├── backend/                # 后端代码
│   ├── data/               # 存放数据相关内容
│   │   ├── raw/            # 原始爬取的 HTML 文件
│   │   └── processed/      # 处理后的JSON数据
│   ├── src/                # 主要 Python 代码
│   │   ├── __init__.py     # 让 src 变成一个 Python package
│   │   ├── config.py       # 配置文件（BASE_URL、爬取日期范围等）
│   │   ├── scraper.py      # 爬虫逻辑，Selenium 相关代码
│   │   ├── annotator.py    # 案例分析和结构化数据提取
│   │   ├── utils.py        # 工具函数（如文件处理、日志等）
│   │   └── main.py         # 入口脚本，控制整体流程
│   ├── logs/               # 日志文件
│   └── requirements.txt    # Python 依赖清单
├── docs/                   # 项目文档
│   ├── data_collection_poc.md       # 数据收集概念验证文档(英文)
│   └── data_collection_poc_zh.md    # 数据收集概念验证文档(中文)
├── .gitignore              # Git 忽略文件
└── README.md               # 项目说明文档
```

## 技术架构

系统由三个主要组件构成：

1. **网页抓取器（scraper.py）**：
   - 使用Selenium WebDriver自动化浏览
   - 基于日期范围定位和提取案例链接
   - 下载案例HTML内容
   - 维护抓取状态以支持断点续写

2. **标注器（annotator.py）**：
   - 使用BeautifulSoup解析HTML内容
   - 提取案例元数据（标题、日期、法官等）
   - 识别和提取案例事实和法规引用
   - 生成结构化JSON输出

3. **主控制器（main.py）**：
   - 协调爬取和标注流程
   - 管理数据处理管道
   - 处理错误和异常情况

## 安装指南

### 前提条件

- Python 3.8 或更高版本
- Chrome 浏览器 (WebDriver 需要)

### 安装步骤

1. 克隆仓库：

   ```bash
   git clone https://github.com/your-username/scc-corpus.git
   cd scc-corpus
   ```

2. 安装依赖：

   ```bash
   pip install -r backend/requirements.txt
   ```

## 使用指南

### 配置

在运行系统前，根据需要修改 `config.py` 文件：

- 调整日期范围 (`DATE_RANGES`)
- 设置输出路径
- 配置浏览器选项

### 运行

```bash
cd backend
python src/main.py
```

### 限制测试范围

测试时可以限制每个日期范围的案例数量：

```python
# 修改 main.py 中的调用
perform_search(driver, start_date, end_date, max_cases=10)
```

### 检查结果

运行完成后，检查输出：

```bash
# 查看输出的JSON文件
cat data/processed/annotation.json | jq

# 查看统计信息
cat data/processed/annotation_statistics.json | jq

# 检查日志
cat logs/scraper.log
cat logs/annotator.log
```

## 已知限制

- 网站HTML结构变化可能影响数据提取
- 旧案例的格式可能与现代案例不同，可能导致部分数据提取失败
- Token计数使用的是估算方法 (4字符≈1token)

## 当前开发状态

- [x] 基本网页抓取功能
- [x] HTML解析和元数据提取
- [x] 刑事案例过滤
- [x] 事实和法规提取
- [x] 原始URL记录
- [x] 语料库统计生成
- [x] 断点续写系统
- [ ] 更精确的token计数
- [ ] 自动化测试套件

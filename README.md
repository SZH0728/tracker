# Tracker

一个轻量的 tracker URL 聚合服务。

Tracker 会按配置定时请求多个上游文本数据源，解析并去重后写入本地文件，同时通过 HTTP 服务提供聚合结果和健康检查接口。适合将多个文本列表汇总成一个可供其他客户端读取的 tracker 文件。

## 功能特性

- 支持配置多个上游 tracker 数据源
- 支持请求超时、有限重试和自定义请求头
- 提供 `text-lines` 文本行解析器
- 聚合结果自动去重
- 使用临时文件和原子替换发布结果
- 单个来源失败时跳过该来源
- 所有来源都失败时保留上一份有效文件
- 提供 HTTP GET、HEAD 和 `/health` 接口
- 支持 Docker Compose 部署

## 工作流程

服务启动后会执行以下流程：

```text
读取 INI 配置
    ↓
请求上游 tracker
    ↓
解析各来源内容
    ↓
汇总并去重
    ↓
原子替换输出文件
    ↓
HTTP 提供文件内容
```

核心模块职责如下：

| 模块 | 职责 |
| --- | --- |
| `config.py` | 读取并校验 INI 配置 |
| `data.py` | 定义配置和数据记录 |
| `requester.py` | 请求上游数据并处理重试 |
| `parser.py` | 注册和构造解析器，目前提供 `text-lines` |
| `assembler.py` | 定期刷新、解析和聚合数据 |
| `file.py` | 读取文件并原子发布新内容 |
| `main.py` | 启动 HTTP 服务和后台刷新线程 |

服务启动时会立即刷新一次，之后按照 `refresh_interval` 秒的周期刷新。

## 环境要求

- Python `3.14.6`
- `requests >= 2.32, < 3`
- Docker 用户可使用 Docker Compose，无需在宿主机安装 Python 依赖

## 安装

建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

在 Windows PowerShell 中，也可以使用：

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 配置

复制示例配置：

```bash
cp config.example.ini config.ini
```

配置文件默认路径为当前工作目录下的 `config.ini`，也可以通过 `CONFIG_PATH` 环境变量指定：

```bash
CONFIG_PATH=/path/to/config.ini python main.py
```

配置文件由三个部分组成。

### 全局配置

```ini
[global]
host = 0.0.0.0
port = 8080
output_file = tracker.txt
refresh_interval = 300
```

| 配置项 | 必填 | 说明 |
| --- | --- | --- |
| `host` | 是 | HTTP 服务监听地址 |
| `port` | 是 | HTTP 服务监听端口 |
| `output_file` | 是 | 聚合结果输出路径；相对路径相对于进程当前工作目录 |
| `refresh_interval` | 是 | 刷新间隔，单位为秒；建议设置为正数 |

示例中的服务监听 `0.0.0.0:8080`，每 300 秒刷新一次，并将结果写入 `tracker.txt`。

### tracker 数据源

每个 `[tracker.<名称>]` 部分代表一个上游数据源：

```ini
[tracker.example]
url = https://example.com/tracker.txt
request_timeout = 10
retry = 2
retry_interval = 5
parser = text-lines
# header = {"User-Agent": "tracker-example/1.0"}
```

| 配置项 | 必填 | 说明 |
| --- | --- | --- |
| `url` | 是 | 上游数据源 URL |
| `request_timeout` | 是 | 请求超时时间，单位为秒 |
| `retry` | 是 | 额外重试次数；`retry = 2` 表示最多尝试 3 次 |
| `retry_interval` | 是 | 两次尝试之间的等待时间，单位为秒 |
| `parser` | 是 | 解析器名称，可以是 `text-lines` 或解析器配置别名 |
| `header` | 否 | JSON 对象，键和值都必须是字符串 |

上游请求默认使用 UTF-8 解析输出文件和发布结果。请求头示例：

```ini
header = {"User-Agent": "tracker-example/1.0", "Authorization": "Bearer token"}
```

请勿将包含真实凭据的配置文件提交到公开仓库。

### 解析器配置

当前内置解析器为 `text-lines`。可以直接使用基础解析器：

```ini
parser = text-lines
```

也可以通过 `[parser.<名称>]` 定义一个带选项的解析器配置：

```ini
[parser.example-lines]
base = text-lines
delimiter = ;
encoding = utf-8
```

然后在 tracker 数据源中引用：

```ini
parser = example-lines
```

`text-lines` 支持以下选项：

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `base` | 无 | 必须为 `text-lines` |
| `delimiter` | 换行符 | 文本分隔符，是字面字符串而不是正则表达式 |
| `encoding` | `utf-8` | 上游内容的字符编码 |

解析器会清除每个项目首尾的空白，并丢弃空项目。

## 本地运行

1. 准备配置文件：

   ```bash
   cp config.example.ini config.ini
   ```

2. 根据实际需求修改 `config.ini` 中的上游 URL 和输出路径。

3. 确保输出文件的父目录已经存在。使用示例中的 `tracker.txt` 时，项目根目录即可作为输出目录。

4. 启动服务：

   ```bash
   CONFIG_PATH=config.ini python main.py
   ```

   如果使用默认路径，也可以直接运行：

   ```bash
   python main.py
   ```

服务启动后会监听配置中的地址和端口。使用 `Ctrl-C` 停止服务。

项目当前没有 argparse、Click 或 Typer 命令行参数；运行参数通过配置文件和 `CONFIG_PATH` 环境变量提供。

## HTTP API

默认监听地址为 `http://127.0.0.1:8080`（服务实际绑定地址由 `global.host` 决定）。

| 方法 | 路径     | 行为 |
| --- |----------| --- |
| `GET` | 任意路径 | 返回聚合文件内容 |
| `HEAD` | 任意路径 | 返回聚合文件响应头，不包含响应体 |

当前 HTTP 服务没有认证和访问控制，任意路径的 GET 请求都会返回聚合文件内容。不要将服务直接暴露到不可信的公网环境；如需对外提供服务，请在前置反向代理中配置认证、TLS 和访问限制。

## Docker Compose 部署

Docker Compose 会将配置文件以只读方式挂载到容器，并将输出目录挂载到宿主机，以便持久化聚合结果。

首先准备配置文件和输出目录：

```bash
cp config.example.ini config.ini
mkdir -p data
```

修改 `config.ini` 后启动：

```bash
docker compose up -d --build
```

默认宿主机端口为 `8080`。可以通过 `TRACKER_HOST_PORT` 修改：

```bash
TRACKER_HOST_PORT=18080 docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f tracker
```

停止服务：

```bash
docker compose down
```

容器中的路径关系如下：

| 宿主机 | 容器 | 说明 |
| --- | --- | --- |
| `./config.ini` | `/config/config.ini` | 只读配置文件 |
| `./data` | `/data` | 聚合输出目录 |

容器工作目录为 `/data`。因此示例中的 `output_file = tracker.txt` 会生成宿主机的 `./data/tracker.txt`。

## 刷新与错误处理

- 数据源按照配置文件中的声明顺序请求。
- HTTP `2xx` 和 `3xx` 响应视为请求成功。
- `4xx` 响应不会重试。
- `5xx` 响应、连接错误和超时会按照 `retry + 1` 次尝试处理。
- 单个来源请求或解析失败时，会跳过该来源并继续处理其他来源。
- 至少有一个来源成功时，发布本轮聚合结果。
- 所有来源都失败时，保留之前的输出文件。
- 聚合结果会去重，但当前实现不保证去重后的输出顺序。
- 输出文件通过同级临时文件和原子替换发布。

## 许可证

本项目使用 [MIT License](LICENSE)。

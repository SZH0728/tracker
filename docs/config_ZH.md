### 配置文件说明

配置文件应该以`config.ini`命名，并放在`tracker_collector`文件夹下。  

以下为对于配置文件各配置项的作用的介绍

#### [base]

- **thread_pool_size**
  - **含义**: 线程池的大小。
  - **示例值**: `8` (线程池包含8个线程)

- **save_file**
  - **含义**: 存储文件的位置及文件名。
  - **示例值**: `tracker.txt` (文件位置为当前目录，文件名为`tracker.txt`)

- **tracker**
  - **含义**: 跟踪器来源的名称，多个跟踪器来源之间用英文逗号`,`分隔，跟踪器来源的具体配置应该为`[tracker_<name>]`命名的小节。
  - **示例值**: `example` (定义了一个名为`example`的跟踪器)

#### [request]

- **default_headers**
  - **含义**: 默认的HTTP请求头。
  - **示例值**: {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}  
  (设置了User-Agent请求头)

- **timeout**
  - **含义**: HTTP请求的超时时间（单位：秒）。
  - **示例值**: `8` (请求超时时间为8秒)

#### [interval]

- **second**
  - **含义**: 更新间隔的秒数。
  - **示例值**: `0` (不使用秒数)

- **minute**
  - **含义**: 更新间隔的分钟数。
  - **示例值**: `0` (不使用分钟数)

- **hour**
  - **含义**: 更新间隔的小时数。
  - **示例值**: `0` (不使用小时数)

- **day**
  - **含义**: 更新间隔的天数。
  - **示例值**: `1` (更新间隔为1天)

#### [logger]

- **log_file**
  - **含义**: 日志文件路径，如果留空，则日志输出到控制台。
  - **示例值**: ` ` (日志将输出到控制台)

- **log_level**
  - **含义**: 日志记录的级别。
  - **示例值**: `DEBUG` (记录调试级别的日志)

#### [tracker_example]

- **url**
  - **含义**: 跟踪器来源的URL地址。
  - **示例值**: `http://example.com/all.txt` (跟踪器来源URL为`http://example.com/all.txt`)

- **method**
  - **含义**: 跟踪器数据的解析方法，默认为`SPLIT()`。
  - **示例值**: `SPLIT(\n)` (具体说明请参考[解析方法](https://github.com/SZH0728/tracker-collector/blob/main/docs/rule_ZH.md))

- **headers**
  - **含义**: 专属的HTTP请求头，这些请求头将与默认请求头合并。
  - **示例值**: `{}` (没有额外的请求头)
    
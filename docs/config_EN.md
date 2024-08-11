### Configuration File Explanation

The configuration file should be named `config.ini` and placed in the `tracker_collector` folder.

Below is an explanation of the various configuration items in the configuration file.

#### [base]

- **thread_pool_size**
  - **Meaning**: The size of the thread pool.
  - **Example Value**: `8` (The thread pool contains 8 threads.)

- **save_file**
  - **Meaning**: The location and filename for the storage file.
  - **Example Value**: `tracker.txt` (The file is located in the current directory and named `tracker.txt`.)

- **tracker**
  - **Meaning**: The name of the tracker source, multiple tracker sources are separated by a comma `,`, and the specific configuration for each tracker source should be a section named `[tracker_<name>]`.
  - **Example Value**: `example` (Defines a tracker named `example`.)

#### [request]

- **default_headers**
  - **Meaning**: Default HTTP request headers.
  - **Example Value**: {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}  
  (Sets the User-Agent request header.)

- **timeout**
  - **Meaning**: The timeout duration for HTTP requests (in seconds).
  - **Example Value**: `8` (The request times out after 8 seconds.)

#### [interval]

- **second**
  - **Meaning**: The number of seconds between updates.
  - **Example Value**: `0` (Seconds are not used.)

- **minute**
  - **Meaning**: The number of minutes between updates.
  - **Example Value**: `0` (Minutes are not used.)

- **hour**
  - **Meaning**: The number of hours between updates.
  - **Example Value**: `0` (Hours are not used.)

- **day**
  - **Meaning**: The number of days between updates.
  - **Example Value**: `1` (The update interval is 1 day.)

#### [logger]

- **log_file**
  - **Meaning**: The path to the log file, if left blank, logs are output to the console.
  - **Example Value**: ` ` (Logs will be output to the console.)

- **log_level**
  - **Meaning**: The logging level.
  - **Example Value**: `DEBUG` (Logs debug-level messages.)

#### [tracker_example]

- **url**
  - **Meaning**: The URL address of the tracker source.
  - **Example Value**: `http://example.com/all.txt` (The tracker source URL is `http://example.com/all.txt`.)

- **method**
  - **Meaning**: The parsing method for tracker data, default is `SPLIT()`.
  - **Example Value**: `SPLIT(\n)` (For more details, see the [Parsing Method](/docs/rule_EN.md).)

- **headers**
  - **Meaning**: Custom HTTP request headers that are merged with the default request headers.
  - **Example Value**: `{}` (No additional request headers.)

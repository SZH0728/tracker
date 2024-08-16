### 解析器语法说明

#### 语法格式： 
  `<command>(<arg1>,<arg2, ...>)`  
  (注意使用英文逗号与圆括号)
#### 命令：
1. SPLIT:
   - 描述：将文本按指定字符进行分割
   - 参数：指定的字符
   - 示例：`SPLIT(,)` (按照`,`进行分割)
  
2. REGEX:
   - 描述：将文本按正则表达式进行提取
   - 参数：正则表达式
   - 示例：`REGEX(^[a-z]+)` (提取以小写字母开头的字符串)

3. SCRIPT:
   - 描述：使用Python脚本对文本进行处理
   - 参数：Python脚本名称或路径
   - 示例：`SCRIPT(my_script)` (使用my_script.py脚本对文本进行处理)
   
   #### 关于脚本的编写方式：
   1. 脚本位置
      - 脚本可放在`tracker-collector/scripts`目录下
      - 脚本也可以通过`SCRIPT(path/to/script)`指定脚本路径

   2. 脚本元数据
      - 脚本的元数据通过`# @key: value`注释指定
      - `name`是脚本的名称，必须存在
      - `requirements`是脚本的依赖，如`lxml`
      - 元数据结束后必须存在一行`# CODE`
      - 其余参数可自由定义

   3. 脚本内容
      - 脚本中必须存在一个`analysis`函数，该函数接收一个参数`text`，返回一个由`tracker`网址组成的集合
      - 其余内容可以自由定义
   
      例如，以下为一个示例的脚本文件，位于`tracker-collector/scripts/example.py`
      ```python
      # -*- coding:utf-8 -*-
      # @name: example
      # @author: Sun
      # @description: An example for script
      # @requirement:
   
      # CODE
      def analysis(text: str) -> set[str]:
          return set(i for i in text.split() if i)
      ```

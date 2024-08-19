### Parser Syntax Explanation

#### Syntax Format:
  `<command>(<arg1>,<arg2, ...>)`

#### Commands:
1. SPLIT:
   - Description: Splits text by a specified character.
   - Argument: The specified character.
   - Example: `SPLIT(,)` (Split by `,`)

2. REGEX:
   - Description: Extracts text using a regular expression.
   - Argument: Regular expression.
   - Example: `REGEX(^[a-z]+)` (Extract strings that start with lowercase letters)

3. SCRIPT:
   - Description: Process text using a Python script
   - Argument: Name or path of the Python script
   - Example: `SCRIPT(my_script)` (Process text using my_script.py)
   
   #### About Script Writing:
   1. Script Location
      - Scripts can be placed in the `tracker-collector/scripts` directory
      - Scripts can also specify the script path using `SCRIPT(path/to/script)`

   2. Script Metadata
      - Script metadata is specified through comments in the format `# @key: value`
      - `name` is the name of the script and must exist
      - `requirements` are dependencies for the script, such as `lxml`
      - There must be a line `# CODE` after the metadata ends
      - Other parameters can be freely defined

   3. Script Content
      - The script must contain an `analysis` function that takes one argument `text` and returns a set of `tracker` URLs
      - Other content can be freely defined
   
      For example, here is a sample script file located at `tracker-collector/scripts/example.py`
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

4. XPATH:
   - Requirements: The `lxml` library needs to be installed, and the `xpath` plugin must be enabled in the configuration.
   - Description: Use XPath expressions to extract content from web pages.
   - Parameters: XPath expression.
   - Example: `XPATH(//div[@class="content"]/text())` (Extracts the text within div elements with a class of `content`.)
     `Note: XPath expressions must specify the text to be extracted, and None values will be automatically ignored.`

5. CSS:
   - Requirements: The `PyQuery` library needs to be installed, and the `css` plugin must be enabled in the configuration.
   - Description: Use CSS selectors to extract content from web pages.
   - Parameters: CSS selector.
   - Example: `CSS(.content)` (Extracts the text within elements with a class of `content`.)
     `Note: CSS selectors do not need to specify the text to be extracted; the .text() method in the code already extracts the text.`

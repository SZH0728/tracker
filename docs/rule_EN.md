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

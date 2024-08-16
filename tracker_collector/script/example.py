# -*- coding:utf-8 -*-
# @name: example
# @author:
# @description: An example for script
# @requirement:
# CODE
def analysis(text: str) -> set[str]:
    return set(i for i in text.split() if i)

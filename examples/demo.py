# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description: 
"""
import sys

sys.path.append('..')

from webresearcher import get_weather

if __name__ == '__main__':
    r = get_weather('Beijing')
    print(r)
    r = get_weather('保定')
    print(r)

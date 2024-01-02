#!/bin/bash

# 获取脚本的第一个参数，如果没有提供参数，使用默认值f.py
filename=${1:-f.py}

for i in {1..3}
do
   python $filename&
done

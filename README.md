# ffixv-cw-calculate

又名 ffixv-crystal-world-calculate
中文名为最终幻想14:水晶世界 配方计算器

主要用于水晶世界的配方计算

目前代码成分: LLM99%+人脑1%

界面使用tkinter

## 目前进度

1. 多配方合并计算
2. 树状显示配方列表
3. 手动添加配方
4. 删除添加的配方

## 使用方法

1. pull到本地或者下载zip到本地
2. 进入src目录下,运行main.py即可

## 数据维护

1. 目前使用json进行保存
2. 数据目前区分为: 成品[products](src/data/products), 半成品[materials](src/data/materials), 原材料[base](src/data/base)
3. 因为没有解包数据,目前只能手动维护

## 开发方法

主要代码都在[core](src/core)下面

1. [generator.py](src/core/generator.py)这个是添加配方
2. [calculator.py](src/core/calculator.py)这个是计算
3. [visualizer.py](src/core/visualizer.py)这个是可视化界面代码
import json
import tkinter as tk

from src.core.calculator import BOMCalculator
from src.core.generator import BOMGenerator
from src.core.visualizer import BOMGUI


def calculator():
    # 加载数据
    with open('data/base/index.json') as f:
        base_data = json.load(f)
    with open('data/materials/index.json') as f:
        materials_data = json.load(f)
    with open('data/products/index.json') as f:
        products_data = json.load(f)

    calculator = BOMCalculator(base_data, materials_data, products_data)

    # 计算3个"盐烤公主鳟"所需基础材料
    requirements = calculator.calculate_requirements_by_id('product', 6, 3)
    print(requirements)
    requirements = calculator.calculate_requirements_by_name('product', '盐烤公主鳟', 3)
    print(requirements)
    # 输出: {13: 3.0, 1: 1.0}  # 需要3个公主鳟和1个岩盐

    # 计算5个"食盐"所需基础材料
    requirements = calculator.calculate_requirements_by_id('material', 1, 5)
    print(requirements)
    # 输出: {1: 5.0}  # 需要5个岩盐


def gene():
    generator = BOMGenerator('data')  # 基于现有数据扩展

    # 添加新的基础材料
    generator.add_base_material("水牛奶")

    # 添加新的中间材料
    generator.add_material_by_name(
        name="奶油",
        requirements=[
            ("水牛奶", 18, 2)
        ]
    )

    # 添加新的中间材料
    generator.add_material_by_name(
        name="黄油",
        requirements=[
            ("水牛奶", 18, 2)
        ]
    )
    # # 添加新产品
    # generator.add_product(
    #     name="香草蜂蜜蛋糕",
    #     output=2,  # 一次制作出2个
    #     requirements=[
    #         ("material", 4, 1),  # 黑麦粉
    #         ("material", 19, 1),  # 香草酱(上面添加的)
    #         ("base", 6, 2)  # 鸡蛋
    #     ]
    # )
    #
    # 保存更新后的数据
    generator.save_to_file('index_updated')


if __name__ == "__main__":
    root = tk.Tk()
    app = BOMGUI(root)
    root.mainloop()

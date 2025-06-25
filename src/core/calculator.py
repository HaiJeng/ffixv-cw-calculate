from collections import defaultdict



class BOMCalculator:
    def __init__(self, base_data, materials_data, products_data):
        # 创建快速查找表
        self.base_map = {item['id']: item for item in base_data}
        self.material_map = {item['id']: item for item in materials_data}
        self.product_map = {item['id']: item for item in products_data}

    def calculate_requirements_by_name(self, item_type: str, item_name: str, quantity=1):
        """
        计算制作指定数量物品所需的所有基础材料
        :param item_type: 'product' 或 'material'
        :param item_name: 物品ID
        :param quantity: 需要制作的数量
        :return: 基础材料需求字典 {base_id: required_quantity}
        """

        requirements = defaultdict(int)
        tmp_map = self.base_map
        if item_type == 'product':
            tmp_map = self.product_map
        elif item_type == 'material':
            tmp_map = self.material_map
        for key in tmp_map.keys():
            name = tmp_map[key]['name']
            if name == item_name:
                self._calculate(item_type, key, quantity, requirements)
                return dict(requirements)
        raise RuntimeError(f"{item_type}中{item_name} 不存在")

    def calculate_requirements_by_id(self, item_type: str, item_id: int, quantity=1):
        """
        计算制作指定数量物品所需的所有基础材料
        :param item_type: 'product' 或 'material'
        :param item_id: 物品ID
        :param quantity: 需要制作的数量
        :return: 基础材料需求字典 {base_id: required_quantity}
        """
        requirements = defaultdict(int)
        self._calculate(item_type, item_id, quantity, requirements)
        return dict(requirements)

    def _calculate(self, item_type, item_id, quantity, requirements):
        if item_type == 'base':
            requirements[item_id] += quantity
            return

        # 获取配方
        if item_type == 'product':
            recipe = self.product_map[item_id]['requirements']
            output_qty = self.product_map[item_id].get('output', 1)
            multiplier = quantity / output_qty
        else:  # material
            recipe = self.material_map[item_id]['requirements']
            multiplier = quantity

        # 递归计算每个成分
        for ingredient in recipe:
            ing_type = 'material' if 'material_id' in ingredient else 'base'
            ing_id = ingredient.get('material_id', ingredient.get('base_id'))
            ing_qty = ingredient['quantity'] * multiplier

            self._calculate(ing_type, ing_id, ing_qty, requirements)
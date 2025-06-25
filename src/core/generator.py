import json
from os import mkdir

from src.core.config import save_path


class BOMGenerator:
    def __init__(self, base_data, materials_data, products_data):
        self.base_template = base_data
        self.materials_template = materials_data
        self.products_template = products_data

    def _build_name_maps(self):
        """构建名称到ID的映射表"""
        self.base_name_to_id = {item['name']: item['id'] for item in self.base_template}
        self.material_name_to_id = {item['name']: item['id'] for item in self.materials_template}
        self.product_name_to_id = {item['name']: item['id'] for item in self.products_template}

    def _resolve_reference(self, ref_type, ref):
        """将名称或ID转换为ID"""
        if isinstance(ref, int):  # 已经是ID
            return ref

        if ref_type == 'base':
            return self.base_name_to_id[ref]
        elif ref_type == 'material':
            return self.material_name_to_id[ref]
        elif ref_type == 'product':
            return self.product_name_to_id[ref]
        else:
            raise ValueError(f"未知类型: {ref_type}")

    def add_base_material(self, name, properties=None):
        for item in self.base_template:
            if item['name'] == name:
                return item['id']
        """添加基础原材料"""
        new_id = max([item['id'] for item in self.base_template], default=0) + 1
        item = {"id": new_id, "name": name}
        if properties:
            item.update(properties)
        self.base_template.append(item)
        return new_id

    def add_material_by_name(self, name, requirements, output=1, properties=None):
        for item in self.materials_template:
            if item['name'] == name:
                return item['id']
        """添加半成品"""
        new_id = max([item['id'] for item in self.materials_template], default=0) + 1
        item = {
            "id": new_id,
            "name": name,
            "output": output,
            "requirements": [
                {
                    "base_id" if 'base' in req else "material_id": self._resolve_reference(req[0], req[1]),
                    "quantity": req[2]
                }
                for req in requirements]
        }
        if properties:
            item.update(properties)
        self.materials_template.append(item)
        return new_id

    def add_material(self, name, requirements, output=1, properties=None):
        for item in self.materials_template:
            if item['name'] == name:
                return item['id']
        """添加半成品"""
        new_id = max([item['id'] for item in self.materials_template], default=0) + 1
        item = {
            "id": new_id,
            "name": name,
            "output": output,
            "requirements": self._normalize_requirements(requirements)
        }
        if properties:
            item.update(properties)
        self.materials_template.append(item)
        return new_id

    def add_product(self, name, requirements, output=1, properties=None):
        for item in self.products_template:
            if item['name'] == name:
                return item['id']
        """添加产品"""
        new_id = max([item['id'] for item in self.products_template], default=0) + 1
        item = {
            "id": new_id,
            "name": name,
            "output": output,
            "requirements": self._normalize_requirements(requirements)
        }
        if properties:
            item.update(properties)
        self.products_template.append(item)
        return new_id

    def _normalize_requirements(self, requirements):
        """标准化配方输入格式"""
        normalized = []
        for req in requirements:
            if isinstance(req, tuple):  # 简化输入 (type, id, quantity)
                req_type, req_id, qty = req
                req_dict = {
                    f"{req_type}_id": req_id,
                    "quantity": qty
                }
                normalized.append(req_dict)
            else:
                normalized.append(req)
        return normalized

    def save(self):
        with open(f'{save_path}/base/index.json', 'w') as f:
            json.dump(self.base_template, f, indent=2, ensure_ascii=False)
        with open(f'{save_path}/materials/index.json', 'w') as f:
            json.dump(self.materials_template, f, indent=2, ensure_ascii=False)
        with open(f'{save_path}/products/index.json', 'w') as f:
            json.dump(self.products_template, f, indent=2, ensure_ascii=False)

    def save_to_file(self, filepath):
        mkdir(f"{filepath}")
        mkdir(f"{filepath}/base")
        mkdir(f"{filepath}/materials")
        mkdir(f"{filepath}/products")
        """保存到JSON文件"""
        with open(f"{filepath}/base/index.json", 'w') as f:
            json.dump(self.base_template, f, indent=2, ensure_ascii=False)
        with open(f"{filepath}/materials/index.json", 'w') as f:
            json.dump(self.materials_template, f, indent=2, ensure_ascii=False)
        with open(f"{filepath}/products/index.json", 'w') as f:
            json.dump(self.products_template, f, indent=2, ensure_ascii=False)

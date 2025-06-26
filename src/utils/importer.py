# 未使用
def import_from_csv(self, csv_path, item_type):
    """从CSV批量导入物品"""
    import csv
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if item_type == 'base':
                self.add_base_material(row['name'], row)
            elif item_type == 'material':
                reqs = eval(row['requirements'])  # 注意安全，实际应用应该用更安全的解析方式
                self.add_material(row['name'], reqs, row)
            elif item_type == 'product':
                reqs = eval(row['requirements'])
                self.add_product(
                    row['name'],
                    reqs,
                    int(row.get('output', 1)),
                    row
                )
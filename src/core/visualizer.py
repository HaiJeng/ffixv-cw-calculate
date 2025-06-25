import json
import math
import tkinter as tk
from collections import defaultdict
from tkinter import messagebox, ttk

from src.core import calculator
from src.core.calculator import BOMCalculator
from src.core.config import save_path
from src.core.generator import BOMGenerator


class BOMGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BOM Calculator and Generator")
        with open(f'{save_path}/base/index.json') as f:
            self.base_data = json.load(f)
        with open(f'{save_path}/materials/index.json') as f:
            self.materials_data = json.load(f)
        with open(f'{save_path}/products/index.json') as f:
            self.products_data = json.load(f)
        self.calculator = BOMCalculator(self.base_data, self.materials_data, self.products_data)
        self.generator = BOMGenerator(self.base_data, self.materials_data, self.products_data)
        self.result_window = None
        self.recipe_tree_window  = None

        self.create_homepage()

    def create_homepage(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="计算器!", font=("Arial", 20), width=40).pack(pady=30)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        calculate_button = tk.Button(btn_frame, text="计算", command=self.show_calculation_page, width=20,
                                     height=2)
        calculate_button.pack(pady=20)

        add_recipe_button = tk.Button(btn_frame, text="添加配方", command=self.show_add_recipe_page, width=20,
                                      height=2)
        add_recipe_button.pack(pady=20)
        delete_recipe_button = tk.Button(btn_frame, text="删除配方", command=self.show_delete_recipe_page, width=20,
                                         height=2)
        delete_recipe_button.pack(pady=20)  # 新增按钮

    def show_calculation_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10)

        search_label = tk.Label(search_frame, text="搜索配方:")
        search_label.pack(side=tk.LEFT)

        search_entry = tk.Entry(search_frame)
        search_entry.pack(side=tk.LEFT)
        search_entry.bind("<KeyRelease>", lambda event: self.filter_recipes(search_entry.get()))

        recipe_listbox = tk.Listbox(self.root, width=50)
        recipe_listbox.pack(side=tk.LEFT, padx=10, pady=10)

        for product in self.products_data:
            recipe_listbox.insert(tk.END, product['name'])

        # 查看配方按钮
        def view_selected_recipe(return_callback):
            selection = recipe_listbox.curselection()
            if not selection:  # 检查是否有选中项
                messagebox.showinfo("提示", "请先选择一个配方")
                return

            return_callback(recipe_listbox.get(selection))

        view_tree_button = tk.Button(self.root, text="查看配方树",
                                     command=lambda: view_selected_recipe(self.show_recipe_tree)
                                     )
        view_tree_button.pack(pady=10)

        add_recipe_button = tk.Button(self.root, text="添加到右侧列表",
                                      command=lambda: view_selected_recipe(self.add_recipe_to_selection)
                                      )
        add_recipe_button.pack(pady=10)

        selection_frame = tk.Frame(self.root)
        selection_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        selection_listbox = tk.Listbox(selection_frame, width=50)
        selection_listbox.pack(side=tk.LEFT)

        calculate_button = tk.Button(selection_frame, text="计算",
                                     command=lambda: self.calculate_selected_recipes(selection_listbox))
        calculate_button.pack(side=tk.BOTTOM, pady=10)

        # 返回按钮
        tk.Button(self.root, text="返回", command=self.create_homepage).pack(pady=10)
        self.recipe_listbox = recipe_listbox
        self.selection_listbox = selection_listbox
        self.quantity_entries = {}  # 用于存储每个配方的数量输入框

    def filter_recipes(self, keyword):
        self.recipe_listbox.delete(0, tk.END)  # 清空列表
        if not keyword:
            # 无关键字时显示所有配方
            for product in self.products_data:
                self.recipe_listbox.insert(tk.END, product['name'])
        else:
            # 过滤匹配的配方
            filtered = [p for p in self.products_data if keyword.lower() in p['name'].lower()]
            for product in filtered:
                self.recipe_listbox.insert(tk.END, product['name'])

    def add_recipe_to_selection(self, recipe_name):
        # 检查是否已添加
        if recipe_name in [self.selection_listbox.get(i) for i in range(self.selection_listbox.size())]:
            messagebox.showinfo("提示", f"{recipe_name} 已添加")
            return

        # 在右侧列表添加配方
        self.selection_listbox.insert(tk.END, recipe_name)

        # 创建数量输入框
        qty_frame = tk.Frame(self.root)
        qty_frame.pack(fill=tk.X, padx=10)

        tk.Label(qty_frame, text=f"{recipe_name} 数量:").pack(side=tk.LEFT)

        qty_entry = tk.Entry(qty_frame, width=5)
        qty_entry.insert(0, "1")  # 默认数量为1
        qty_entry.pack(side=tk.LEFT, padx=5)

        # 保存对输入框的引用
        self.quantity_entries[recipe_name] = qty_entry

        # 从左侧列表移除
        for i in range(self.recipe_listbox.size()):
            if self.recipe_listbox.get(i) == recipe_name:
                self.recipe_listbox.delete(i)
                break

    def calculate_selected_recipes(self, selection_listbox):
        # 获取所有选中的配方及其数量
        selected_recipes = []
        for i in range(selection_listbox.size()):
            recipe_name = selection_listbox.get(i)
            try:
                quantity = int(self.quantity_entries[recipe_name].get())
                selected_recipes.append((recipe_name, quantity))
            except ValueError:
                messagebox.showerror("错误", f"{recipe_name} 的数量必须是整数")
                return

        # 计算需求
        all_requirements = defaultdict(float)  # 存储所有层级的需求

        for name, qty in selected_recipes:
            # 查找配方
            product = next((p for p in self.products_data if p['name'] == name), None)
            if product is None:
                messagebox.showerror("错误", f"找不到配方: {name}")
                continue

            # 获取配方的输出数量（默认为1）
            output_qty = product.get('output', 1)

            # 计算需要生产的批次（向上取整）
            batches = math.ceil(qty / output_qty) * output_qty

            # 获取完整的材料树
            material_tree = self.calculator.calculate_requirements_by_id('product', product['id'], batches,
                                                                         include_all_levels=True)

            # 遍历材料树并收集所有层级的需求
            def traverse_tree(node):
                item_id = node['id']
                item_type = node['type']
                qty = node['quantity']

                # 根据类型更新需求字典
                if item_type == 'product':
                    all_requirements[(item_id, 'product')] += qty
                elif item_type == 'material':
                    all_requirements[(item_id, 'material')] += qty
                elif item_type == 'base':
                    all_requirements[(item_id, 'base')] += qty

                # 递归处理子节点
                for child in node.get('children', []):
                    traverse_tree(child)

            traverse_tree(material_tree)

        # 显示结果
        self.show_calculation_result(all_requirements)

    def show_calculation_result(self, all_requirements):
        # 清除当前界面
        if self.result_window and self.result_window.winfo_exists():
            self.result_window.destroy()
        # 创建新的结果窗口
        self.result_window = tk.Toplevel(self.root)
        self.result_window.title("计算结果")
        self.result_window.geometry("800x600")
        self.result_window.transient(self.root)  # 设置为主窗口的子窗口

        result_frame = tk.Frame(self.result_window)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建三个列的框架
        finished_frame = tk.Frame(result_frame)
        finished_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        semi_finished_frame = tk.Frame(result_frame)
        semi_finished_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        raw_materials_frame = tk.Frame(result_frame)
        raw_materials_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # 创建各列的标题
        tk.Label(finished_frame, text="成品").pack(pady=5)
        tk.Label(semi_finished_frame, text="半成品").pack(pady=5)
        tk.Label(raw_materials_frame, text="原材料").pack(pady=5)

        # 创建各列的滚动条和列表框
        finished_scrollbar = tk.Scrollbar(finished_frame)
        finished_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        finished_listbox = tk.Listbox(finished_frame, width=30, yscrollcommand=finished_scrollbar.set)
        finished_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        finished_scrollbar.config(command=finished_listbox.yview)

        semi_finished_scrollbar = tk.Scrollbar(semi_finished_frame)
        semi_finished_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        semi_finished_listbox = tk.Listbox(semi_finished_frame, width=30, yscrollcommand=semi_finished_scrollbar.set)
        semi_finished_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        semi_finished_scrollbar.config(command=semi_finished_listbox.yview)

        raw_materials_scrollbar = tk.Scrollbar(raw_materials_frame)
        raw_materials_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        raw_materials_listbox = tk.Listbox(raw_materials_frame, width=30, yscrollcommand=raw_materials_scrollbar.set)
        raw_materials_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        raw_materials_scrollbar.config(command=raw_materials_listbox.yview)

        # 分类显示材料需求
        for (item_id, item_type), qty in all_requirements.items():
            # 查找材料名称
            if item_type == 'product':
                item = next((p for p in self.products_data if p['id'] == item_id), None)
                if item:
                    finished_listbox.insert(tk.END, f"- {item['name']}: {int(qty)}")
            elif item_type == 'material':
                item = next((m for m in self.materials_data if m['id'] == item_id), None)
                if item:
                    semi_finished_listbox.insert(tk.END, f"- {item['name']}: {int(qty)}")
            elif item_type == 'base':
                item = next((b for b in self.base_data if b['id'] == item_id), None)
                if item:
                    raw_materials_listbox.insert(tk.END, f"- {item['name']}: {int(qty)}")

        # 返回按钮：关闭结果窗口，不销毁主界面
        tk.Button(
            self.result_window,
            text="返回",
            command=self.result_window.destroy
        ).pack(pady=10)

    def show_recipe_tree(self, recipe_name):
        # 清除当前界面
        if self.recipe_tree_window and self.recipe_tree_window.winfo_exists():
            self.recipe_tree_window.destroy()
        # 创建新的结果窗口
        self.recipe_tree_window = tk.Toplevel(self.root)
        self.recipe_tree_window.title(f"{recipe_name}配方树")
        self.recipe_tree_window.geometry("800x600")
        self.recipe_tree_window.transient(self.root)  # 设置为主窗口的子窗口

        # 创建 Treeview 组件
        tree = ttk.Treeview(self.recipe_tree_window, columns=("quantity", "type"))
        tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 设置列标题
        tree.heading("#0", text="材料名称")
        tree.heading("quantity", text="数量")
        tree.heading("type", text="类型")

        # 设置列宽
        tree.column("#0", width=200)
        tree.column("quantity", width=80, anchor=tk.CENTER)
        tree.column("type", width=80, anchor=tk.CENTER)

        # 查找选定配方的信息
        product = next((p for p in self.products_data if p['name'] == recipe_name), None)
        if product is None:
            tk.messagebox.showerror("错误", f"找不到配方: {recipe_name}")
            return

        # 创建根节点
        root_node = tree.insert("", "end", text=recipe_name, values=(product.get('output', 1), "成品"))

        # 递归函数，用于构建树状结构
        def build_tree(parent_node, item_id, item_type, quantity):
            # 根据类型获取材料信息
            if item_type == 'product':
                item = next((p for p in self.products_data if p['id'] == item_id), None)
            elif item_type == 'material':
                item = next((m for m in self.materials_data if m['id'] == item_id), None)
            else:  # base
                item = next((b for b in self.base_data if b['id'] == item_id), None)

            if not item:
                tree.insert(parent_node, "end", text=f"未知材料(ID:{item_id})", values=(quantity, "未知"))
                return

            # 获取材料的需求
            requirements = item.get('requirements', [])

            # 为每个需求添加子节点
            for req in requirements:
                req_type = 'material' if 'material_id' in req else 'base'
                req_id = req.get('material_id', req.get('base_id'))
                req_qty = req['quantity'] * quantity

                # 查找材料名称
                req_name = ""
                req_item_type = ""

                if req_type == 'material':
                    req_material = next((m for m in self.materials_data if m['id'] == req_id), None)
                    if req_material:
                        req_name = req_material['name']
                        req_item_type = "材料"
                else:  # base
                    req_base = next((b for b in self.base_data if b['id'] == req_id), None)
                    if req_base:
                        req_name = req_base['name']
                        req_item_type = "半成品"

                if not req_name:
                    req_name = f"未知材料(ID:{req_id})"

                # 创建子节点
                child_node = tree.insert(
                    parent_node, "end",
                    text=req_name,
                    values=(req_qty, req_item_type)
                )

                # 如果该材料是成品或材料，继续递归构建子树
                if req_type == 'material':
                    build_tree(child_node, req_id, 'material', req_qty)

        # 开始构建树
        build_tree(root_node, product['id'], 'product', 1)

        # 返回按钮：关闭结果窗口，不销毁主界面
        tk.Button(
            self.recipe_tree_window,
            text="返回",
            command=self.recipe_tree_window.destroy
        ).pack(pady=10)

    def show_add_recipe_page(self):
        # 清除当前界面
        for widget in self.root.winfo_children():
            widget.destroy()

        # 创建标题
        tk.Label(self.root, text="添加新配方", font=("Arial", 16)).pack(pady=10)

        # 创建配方基本信息输入区域
        info_frame = tk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(info_frame, text="配方名称:").grid(row=0, column=0, sticky=tk.W)
        recipe_name_entry = tk.Entry(info_frame, width=30)
        recipe_name_entry.grid(row=0, column=1, sticky=tk.W, padx=5)

        tk.Label(info_frame, text="产出数量:").grid(row=0, column=2, sticky=tk.W)
        output_qty_entry = tk.Entry(info_frame, width=5)
        output_qty_entry.insert(0, "1")
        output_qty_entry.grid(row=0, column=3, sticky=tk.W, padx=5)

        # 创建材料选择区域
        materials_frame = tk.Frame(self.root)
        materials_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 左侧材料列表
        left_frame = tk.Frame(materials_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="可用材料").pack(anchor=tk.W)

        # 创建材料类型选择
        material_type_var = tk.StringVar(value="all")
        material_type_frame = tk.Frame(left_frame)
        material_type_frame.pack(fill=tk.X, pady=5)

        def on_material_type_change():
            self.filter_materials(material_search_entry.get(), material_type_var.get(), material_listbox)

        tk.Radiobutton(material_type_frame, text="所有", variable=material_type_var, value="all",
                       command=on_material_type_change).pack(side=tk.LEFT)
        tk.Radiobutton(material_type_frame, text="原材料", variable=material_type_var, value="base",
                       command=on_material_type_change).pack(side=tk.LEFT)
        tk.Radiobutton(material_type_frame, text="半成品", variable=material_type_var, value="material",
                       command=on_material_type_change).pack(side=tk.LEFT)

        # 创建材料搜索框
        material_search_entry = tk.Entry(left_frame)
        material_search_entry.pack(fill=tk.X, pady=5)
        material_search_entry.bind("<KeyRelease>", lambda event: self.filter_materials(
            material_search_entry.get(), material_type_var.get(), material_listbox))

        # 创建材料列表
        material_listbox = tk.Listbox(left_frame)
        material_listbox.pack(fill=tk.BOTH, expand=True)

        # 填充材料列表
        self.filter_materials("", "all", material_listbox)

        # 右侧配方树
        right_frame = tk.Frame(materials_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(right_frame, text="配方树").pack(anchor=tk.W)

        # 创建配方树 Treeview
        recipe_tree = ttk.Treeview(right_frame, columns=("quantity", "type"))
        recipe_tree.pack(fill=tk.BOTH, expand=True)

        # 设置列标题
        recipe_tree.heading("#0", text="材料名称")
        recipe_tree.heading("quantity", text="数量")
        recipe_tree.heading("type", text="类型")

        # 设置列宽
        recipe_tree.column("#0", width=200)
        recipe_tree.column("quantity", width=80, anchor=tk.CENTER)
        recipe_tree.column("type", width=80, anchor=tk.CENTER)

        # 创建根节点
        recipe_root = recipe_tree.insert("", "end", text="新配方", values=("", "成品"))

        # 操作按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # 添加材料按钮
        def add_material_to_recipe():
            selected_materials = material_listbox.curselection()
            if not selected_materials:
                tk.messagebox.showinfo("提示", "请先选择材料")
                return

            selected_item = recipe_tree.selection()
            if not selected_item:
                parent = recipe_root
            else:
                parent = selected_item[0]

            for i in selected_materials:
                material_name = material_listbox.get(i)
                material_id = None
                material_type = ""

                # 查找材料ID和类型
                material = next((m for m in self.materials_data if m['name'] == material_name), None)
                if material:
                    material_id = material['id']
                    material_type = "材料"
                else:
                    material = next((b for b in self.base_data if b['name'] == material_name), None)
                    if material:
                        material_id = material['id']
                        material_type = "半成品"

                if material_id:
                    recipe_tree.insert(
                        parent, "end",
                        text=material_name,
                        values=("1", material_type),
                        tags=(f"{material_type}_{material_id}",)
                    )

        tk.Button(button_frame, text="添加到配方", command=add_material_to_recipe).pack(side=tk.LEFT, padx=5)

        # 设置数量按钮
        def set_quantity():
            selected_item = recipe_tree.selection()
            if not selected_item:
                tk.messagebox.showinfo("提示", "请先选择材料")
                return

            # 创建对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("设置数量")
            dialog.geometry("300x150")
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(dialog, text="数量:").pack(pady=20)
            quantity_entry = tk.Entry(dialog)
            quantity_entry.insert(0, "1")
            quantity_entry.pack(pady=5)

            def save_quantity():
                try:
                    quantity = int(quantity_entry.get())
                    if quantity <= 0:
                        raise ValueError

                    # 更新数量
                    values = list(recipe_tree.item(selected_item[0], "values"))
                    values[0] = quantity
                    recipe_tree.item(selected_item[0], values=values)

                    dialog.destroy()
                except ValueError:
                    tk.messagebox.showerror("错误", "请输入有效的正整数")

            tk.Button(dialog, text="确定", command=save_quantity).pack(pady=10)

        tk.Button(button_frame, text="设置数量", command=set_quantity).pack(side=tk.LEFT, padx=5)

        # 删除材料按钮
        def delete_material():
            selected_item = recipe_tree.selection()
            if not selected_item or selected_item[0] == recipe_root:
                tk.messagebox.showinfo("提示", "无法删除根节点")
                return

            recipe_tree.delete(selected_item)

        tk.Button(button_frame, text="删除材料", command=delete_material).pack(side=tk.LEFT, padx=5)

        # 保存配方按钮
        def save_recipe():
            recipe_name = recipe_name_entry.get().strip()
            if not recipe_name:
                tk.messagebox.showerror("错误", "请输入配方名称")
                return

            try:
                output_qty = int(output_qty_entry.get())
                if output_qty <= 0:
                    raise ValueError
            except ValueError:
                tk.messagebox.showerror("错误", "请输入有效的产出数量")
                return

            # 构建配方数据
            requirements = []

            # 遍历配方树的子节点
            for child_id in recipe_tree.get_children(recipe_root):
                requirements.extend(build_requirements(child_id))

            if not requirements:
                tk.messagebox.showerror("错误", "配方至少需要一个材料")
                return

            # 创建新配方
            new_id = max((p['id'] for p in self.products_data), default=0) + 1
            new_recipe = {
                "id": new_id,
                "name": recipe_name,
                "output": output_qty,
                "requirements": requirements
            }

            # 添加到成品列表
            self.products_data.append(new_recipe)

            # 保存到文件
            try:
                with open(f'{save_path}/products/index.json', 'w') as f:
                    json.dump(self.products_data, f, indent=2, ensure_ascii=False)
                tk.messagebox.showinfo("成功", f"配方 {recipe_name} 已保存")
                self.show_add_recipe_page()
            except Exception as e:
                tk.messagebox.showerror("错误", f"保存失败: {str(e)}")

        # 递归构建配方需求
        def build_requirements(node_id):
            item = recipe_tree.item(node_id)
            tags = item['tags']
            if not tags:
                return []

            tag = tags[0]
            parts = tag.split('_')
            if len(parts) != 2:
                return []

            material_type, material_id = parts[0], int(parts[1])
            quantity = int(item['values'][0])

            req_key = "material_id" if material_type == "material" else "base_id"
            requirement = {req_key: material_id, "quantity": quantity}

            # 处理子节点
            children = recipe_tree.get_children(node_id)
            if children:
                requirement['children'] = []
                for child_id in children:
                    requirement['children'].extend(build_requirements(child_id))

            return [requirement]

        tk.Button(button_frame, text="保存配方", command=save_recipe).pack(side=tk.RIGHT, padx=5)

        # 返回按钮
        tk.Button(self.root, text="返回", command=self.create_homepage).pack(pady=10)

    def fill_material_listbox(self, listbox, material_type, keyword):
        listbox.delete(0, tk.END)

        # 根据类型和关键字过滤材料
        if material_type == "all":
            materials = self.base_data + self.materials_data
        elif material_type == "base":
            materials = self.base_data
        else:  # material
            materials = self.materials_data

        if keyword:
            materials = [m for m in materials if keyword.lower() in m['name'].lower()]

        # 填充列表
        for material in materials:
            listbox.insert(tk.END, material['name'])

    def filter_materials(self, keyword, material_type, listbox):
        self.fill_material_listbox(listbox, material_type, keyword)

    def show_delete_recipe_page(self):
        # 清除当前界面
        for widget in self.root.winfo_children():
            widget.destroy()

        # 创建标题
        tk.Label(self.root, text="删除配方", font=("Arial", 16)).pack(pady=10)

        # 创建搜索区域
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(search_frame, text="搜索配方:").pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", lambda event: self.filter_delete_recipes(
            search_entry.get(), recipe_listbox))

        # 创建配方列表
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框
        recipe_listbox = tk.Listbox(list_frame, width=50, yscrollcommand=scrollbar.set)
        recipe_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=recipe_listbox.yview)

        # 填充配方列表
        self.fill_recipe_listbox(recipe_listbox)

        # 创建按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # 查看配方按钮
        def view_selected_recipe():
            selection = recipe_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一个配方")
                return

            recipe_name = recipe_listbox.get(selection[0])
            self.show_recipe_tree(recipe_name)  # 指定返回删除页面

        tk.Button(button_frame, text="查看配方", command=view_selected_recipe).pack(side=tk.LEFT, padx=5)

        # 删除配方按钮
        def delete_selected_recipe():
            selection = recipe_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一个配方")
                return

            recipe_name = recipe_listbox.get(selection[0])
            confirm = messagebox.askyesno("确认删除", f"确定要删除配方 '{recipe_name}' 吗？")

            if confirm:
                # 查找并删除配方
                for i, product in enumerate(self.products_data):
                    if product['name'] == recipe_name:
                        del self.products_data[i]
                        break

                # 从列表中删除
                recipe_listbox.delete(selection[0])

                # 保存到文件
                try:
                    with open(f'{save_path}/products/index.json', 'w') as f:
                        json.dump(self.products_data, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("成功", f"配方 '{recipe_name}' 已删除")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {str(e)}")

        tk.Button(button_frame, text="删除配方", command=delete_selected_recipe).pack(side=tk.LEFT, padx=5)

        # 返回按钮
        tk.Button(button_frame, text="返回", command=self.create_homepage).pack(side=tk.RIGHT, padx=5)

    def fill_recipe_listbox(self, listbox):
        listbox.delete(0, tk.END)
        for product in self.products_data:
            listbox.insert(tk.END, product['name'])

    def filter_delete_recipes(self, keyword, listbox):
        listbox.delete(0, tk.END)
        if not keyword:
            for product in self.products_data:
                listbox.insert(tk.END, product['name'])
        else:
            filtered = [p for p in self.products_data if keyword.lower() in p['name'].lower()]
            for product in filtered:
                listbox.insert(tk.END, product['name'])


if __name__ == '__main__':

    with open(f'{save_path}/base/index.json') as f:
        base_data = json.load(f)
    with open(f'{save_path}/materials/index.json') as f:
        materials_data = json.load(f)
    with open(f'{save_path}/products/index.json') as f:
        products_data = json.load(f)
    calculator = BOMCalculator(base_data, materials_data, products_data)
    # 计算需求（修改后的逻辑）
    all_requirements = defaultdict(float)  # 存储所有层级的需求
    selected_recipes = [('盐烤公主鳟', 1), ('煎饼', 1), ('羊奶煮粥', 1)]
    for name, qty in selected_recipes:
        # 查找配方
        product = next((p for p in products_data if p['name'] == name), None)
        if product is None:
            messagebox.showerror("错误", f"找不到配方: {name}")
            continue
        print(product)
        # 获取配方的输出数量（默认为1）
        output_qty = product.get('output', 1)

        # 计算需要生产的批次（向上取整）
        batches = math.ceil(qty / output_qty) * output_qty


        # 递归计算所有层级的需求
        def calculate_all_requirements(product_id, _quantity, level=0):
            # 获取当前产品/材料的需求
            reqs = calculator.calculate_requirements_by_id('product', product_id, _quantity)

            # 记录当前产品的需求
            all_requirements[(product_id, 'product')] += _quantity

            # 递归处理每个需求
            for req_id, req_qty in reqs.items():
                # 检查这个需求是材料还是基础材料
                if next((m for m in materials_data if m['id'] == req_id), None):
                    # 这是一个材料（半成品）
                    all_requirements[(req_id, 'material')] += req_qty
                    calculate_all_requirements(req_id, req_qty, level + 1)
                elif next((b for b in base_data if b['id'] == req_id), None):
                    # 这是一个基础材料
                    all_requirements[(req_id, 'base')] += req_qty


        # 开始递归计算
        calculate_all_requirements(product['id'], batches)

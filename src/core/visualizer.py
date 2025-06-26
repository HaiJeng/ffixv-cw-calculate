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
        with open(f'{save_path}/base/index.json', encoding='UTF-8') as f:
            self.base_data = json.load(f)
        with open(f'{save_path}/materials/index.json', encoding='UTF-8') as f:
            self.materials_data = json.load(f)
        with open(f'{save_path}/products/index.json', encoding='UTF-8') as f:
            self.products_data = json.load(f)
        self.calculator = BOMCalculator(self.base_data, self.materials_data, self.products_data)
        self.generator = BOMGenerator(self.base_data, self.materials_data, self.products_data)
        self.result_window = None
        self.recipe_tree_window = None

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
        self.result_window = self.create_centered_window("计算结果")

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
        self.recipe_tree_window = self.create_centered_window(f"{recipe_name}配方树")

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

        # 材料操作按钮
        button_frame = tk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)

        def create_new_base_material():
            dialog = self.create_centered_window("创建新原材料", 300, 150, True)

            tk.Label(dialog, text="原材料名称:").pack(pady=10)
            name_entry = tk.Entry(dialog)
            name_entry.pack(pady=5)
            name_entry.focus_set()

            def save_new_base():
                name = name_entry.get().strip()
                if not name:
                    tk.messagebox.showerror("错误", "请输入名称")
                    return

                # 检查是否已存在
                if any(b['name'] == name for b in self.base_data):
                    tk.messagebox.showerror("错误", f"原材料 '{name}' 已存在")
                    return

                # 创建新原材料
                new_id = max((b['id'] for b in self.base_data), default=0) + 1
                new_base = {
                    "id": new_id,
                    "name": name
                }
                self.base_data.append(new_base)

                self.save_base()

                # 更新材料列表
                self.filter_materials(material_search_entry.get(), material_type_var.get(), material_listbox)

                dialog.destroy()
                # tk.messagebox.showinfo("成功", f"原材料 '{name}' 已创建")

            # 绑定回车键到保存函数
            name_entry.bind("<Return>", lambda event: save_new_base())
            tk.Button(dialog, text="创建", command=save_new_base).pack(pady=10)

        tk.Button(button_frame, text="创建原材料", command=create_new_base_material).pack(side=tk.LEFT, padx=5)

        def create_new_material():
            dialog = self.create_centered_window("创建新半成品", 300, 150, True)

            # 顶部：半成品名称
            name_frame = tk.Frame(dialog)
            name_frame.pack(fill=tk.X, padx=10, pady=10)

            tk.Label(name_frame, text="半成品名称:").pack(side=tk.LEFT)
            name_entry = tk.Entry(name_frame, width=30)
            name_entry.pack(side=tk.LEFT, padx=5)

            # 中部：材料选择区域
            materials_frame = tk.Frame(dialog)
            materials_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 左侧：原材料列表
            left_frame = tk.Frame(materials_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tk.Label(left_frame, text="原材料").pack(anchor=tk.W)

            # 原材料搜索框
            base_search_var = tk.StringVar()
            base_search_entry = tk.Entry(left_frame, textvariable=base_search_var)
            base_search_entry.pack(fill=tk.X, pady=5)

            # 原材料列表
            base_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE)
            base_listbox.pack(fill=tk.BOTH, expand=True)

            # 填充原材料列表
            for base in self.base_data:
                base_listbox.insert(tk.END, base['name'])

            # 右侧：半成品列表
            right_frame = tk.Frame(materials_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

            tk.Label(right_frame, text="半成品").pack(anchor=tk.W)

            # 半成品搜索框
            material_search_var = tk.StringVar()
            material_search_entry = tk.Entry(right_frame, textvariable=material_search_var)
            material_search_entry.pack(fill=tk.X, pady=5)

            # 半成品列表
            material_listbox = tk.Listbox(right_frame, selectmode=tk.SINGLE)
            material_listbox.pack(fill=tk.BOTH, expand=True)

            # 填充半成品列表
            for material in self.materials_data:
                material_listbox.insert(tk.END, material['name'])

            # 数量设置
            quantity_frame = tk.Frame(dialog)
            quantity_frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(quantity_frame, text="数量:").pack(side=tk.LEFT)
            quantity_entry = tk.Entry(quantity_frame, width=5)
            quantity_entry.insert(0, "1")
            quantity_entry.pack(side=tk.LEFT, padx=5)

            # 添加按钮
            def add_selected_material():
                # 检查是否选择了材料
                base_selected = base_listbox.curselection()
                material_selected = material_listbox.curselection()

                if not base_selected and not material_selected:
                    tk.messagebox.showinfo("提示", "请选择原材料或半成品")
                    return

                try:
                    quantity = int(quantity_entry.get())
                    if quantity <= 0:
                        raise ValueError
                except ValueError:
                    tk.messagebox.showerror("错误", "请输入有效的数量")
                    return

                # 获取选择的材料信息
                if base_selected:
                    material_name = base_listbox.get(base_selected[0])
                    material_id = next(b['id'] for b in self.base_data if b['name'] == material_name)
                    material_type = "原材料"
                else:
                    material_name = material_listbox.get(material_selected[0])
                    material_id = next(m['id'] for m in self.materials_data if m['name'] == material_name)
                    material_type = "半成品"

                # 检查是否已添加
                if any(req.get('base_id') == material_id or req.get('material_id') == material_id for req in
                       requirements):
                    tk.messagebox.showerror("错误", f"{material_type} '{material_name}' 已添加")
                    return

                # 添加到需求列表
                req_key = "base_id" if material_type == "原材料" else "material_id"
                requirements.append({req_key: material_id, "quantity": quantity})

                # 更新显示
                update_requirements_display()

            tk.Button(quantity_frame, text="添加到配方", command=add_selected_material).pack(side=tk.RIGHT)

            # 已选材料显示
            requirements_frame = tk.Frame(dialog)
            requirements_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            tk.Label(requirements_frame, text="已选材料").pack(anchor=tk.W)

            # 已选材料列表
            requirements_listbox = tk.Listbox(requirements_frame)
            requirements_listbox.pack(fill=tk.BOTH, expand=True)

            requirements = []

            def update_requirements_display():
                requirements_listbox.delete(0, tk.END)
                for i, req in enumerate(requirements):
                    material_id = req.get('base_id', req.get('material_id'))
                    material_type = "原材料" if 'base_id' in req else "半成品"

                    # 获取材料名称
                    material_name = ""
                    if material_type == "原材料":
                        material = next((b for b in self.base_data if b['id'] == material_id), None)
                    else:
                        material = next((m for m in self.materials_data if m['id'] == material_id), None)

                    if material:
                        material_name = material['name']
                    else:
                        material_name = f"未知材料(ID:{material_id})"

                    requirements_listbox.insert(tk.END, f"{material_name} x {req['quantity']}")

            # 底部：操作按钮
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)

            # 删除选中的材料
            def delete_selected_material():
                selected = requirements_listbox.curselection()
                if not selected:
                    tk.messagebox.showinfo("提示", "请选择要删除的材料")
                    return

                requirements.pop(selected[0])
                update_requirements_display()

            tk.Button(button_frame, text="删除选中", command=delete_selected_material).pack(side=tk.LEFT)

            # 保存半成品
            def save_new_material():
                name = name_entry.get().strip()
                if not name:
                    tk.messagebox.showerror("错误", "请输入名称")
                    return

                # 检查是否已存在
                if any(m['name'] == name for m in self.materials_data):
                    tk.messagebox.showerror("错误", f"半成品 '{name}' 已存在")
                    return

                if not requirements:
                    tk.messagebox.showerror("错误", "半成品至少需要一个原材料或半成品")
                    return

                # 创建新半成品
                new_id = max((m['id'] for m in self.materials_data), default=0) + 1
                new_material = {
                    "id": new_id,
                    "name": name,
                    "requirements": requirements
                }
                self.materials_data.append(new_material)

                # 保存到文件
                self.save_material()

                # 更新材料列表
                self.filter_materials(material_search_entry.get(), material_type_var.get(), material_listbox)

                dialog.destroy()
                # tk.messagebox.showinfo("成功", f"半成品 '{name}' 已创建")

            tk.Button(button_frame, text="保存", command=save_new_material).pack(side=tk.RIGHT)

            # 调整对话框大小以适应内容
            dialog.update_idletasks()
            width = dialog.winfo_reqwidth() + 50
            height = dialog.winfo_reqheight() + 50
            dialog.geometry(f"{width}x{height}")

        tk.Button(button_frame, text="创建半成品", command=create_new_material).pack(side=tk.LEFT, padx=5)

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

            for i in selected_materials:
                material_name = material_listbox.get(i)
                material_id = None
                material_type = ""

                # 查找材料ID和类型
                material = next((m for m in self.materials_data if m['name'] == material_name), None)
                if material:
                    material_id = material['id']
                    material_type = "半成品"
                else:
                    material = next((b for b in self.base_data if b['name'] == material_name), None)
                    if material:
                        material_id = material['id']
                        material_type = "材料"
                    else:
                        material = next((p for p in self.products_data if p['name'] == material_name), None)
                        if material:
                            material_id = material['id']
                            material_type = "成品"

                if material_id:
                    new_node = recipe_tree.insert(
                        recipe_root, "end",
                        text=material_name,
                        values=("1", material_type),
                        tags=(f"{material_type}_{material_id}",)
                    )
                    if material_type == "半成品":
                        add_material_requirements(new_node, material)

        tk.Button(button_frame, text="添加到配方", command=add_material_to_recipe).pack(side=tk.LEFT, padx=5)

        def add_material_requirements(parent_node, material):
            """递归添加材料的所有层级需求"""
            requirements = material.get('requirements', [])

            for req in requirements:
                req_type = '半成品' if 'material_id' in req else '材料'
                req_id = req.get('material_id', req.get('base_id'))
                req_qty = req['quantity']

                req_name = ""
                req_item_type = ""
                req_data = None

                if req_type == '半成品':
                    req_data = next((m for m in self.materials_data if m['id'] == req_id), None)
                    if req_data:
                        req_name = req_data['name']
                        req_item_type = "半成品"
                else:  # 材料
                    req_data = next((b for b in self.base_data if b['id'] == req_id), None)
                    if req_data:
                        req_name = req_data['name']
                        req_item_type = "材料"

                if not req_name:
                    req_name = f"未知材料(ID:{req_id})"

                child_node = recipe_tree.insert(
                    parent_node, "end",
                    text=req_name,
                    values=(req_qty, req_item_type),
                    tags=(f"{req_item_type}_{req_id}",)
                )

                # 如果是半成品，递归添加其需求
                if req_item_type == "半成品" and req_data:
                    add_material_requirements(child_node, req_data)

        # 设置数量按钮
        def set_quantity():
            selected_item = recipe_tree.selection()
            if not selected_item:
                tk.messagebox.showinfo("提示", "请先选择材料")
                return

            # 创建对话框
            dialog = self.create_centered_window("设置数量", 300, 150, True)

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

            # 判断配方类型并保存到相应的列表
            # 这里假设根节点代表成品配方
            new_id = max((p['id'] for p in self.products_data), default=0) + 1
            new_recipe = {
                "id": new_id,
                "name": recipe_name,
                "output": output_qty,
                "requirements": requirements
            }
            self.products_data.append(new_recipe)
            self.save_product()

            # 检查是否有新的原材料或半成品需要添加
            new_base_materials = []
            new_materials = []

            def check_new_materials(node_id):
                item = recipe_tree.item(node_id)
                tags = item['tags']
                if not tags:
                    return

                tag = tags[0]
                parts = tag.split('_')
                if len(parts) != 2:
                    return

                material_type, material_id = parts[0], int(parts[1])
                material_name = item['text']

                if material_type == "材料":
                    existing_material = next((m for m in self.materials_data if m['id'] == material_id), None)
                    if not existing_material:
                        new_material = {
                            "id": material_id,
                            "name": material_name,
                            "requirements": []
                        }
                        new_materials.append(new_material)
                elif material_type == "半成品":
                    existing_base = next((b for b in self.base_data if b['id'] == material_id), None)
                    if not existing_base:
                        new_base = {
                            "id": material_id,
                            "name": material_name,
                            "requirements": []
                        }
                        new_base_materials.append(new_base)

                children = recipe_tree.get_children(node_id)
                for child_id in children:
                    check_new_materials(child_id)

            for child_id in recipe_tree.get_children(recipe_root):
                check_new_materials(child_id)

            # 添加新的原材料到 base_data
            for new_base in new_base_materials:
                self.base_data.append(new_base)
            self.save_base()

            # 添加新的半成品到 materials_data
            for new_material in new_materials:
                self.materials_data.append(new_material)
            self.save_material()

            tk.messagebox.showinfo("成功", f"配方 {recipe_name} 已保存")
            self.show_add_recipe_page()

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

            req_key = "material_id" if material_type == "材料" else "base_id"
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

        # 创建类型选择器
        type_frame = tk.Frame(self.root)
        type_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(type_frame, text="项目类型:").pack(side=tk.LEFT)
        type_var = tk.StringVar(value="product")  # 默认选择products

        # 类型选择按钮
        tk.Radiobutton(type_frame, text="所有", variable=type_var, value="all").pack(side=tk.LEFT)
        tk.Radiobutton(type_frame, text="成品", variable=type_var, value="product").pack(side=tk.LEFT)
        tk.Radiobutton(type_frame, text="原材料", variable=type_var, value="base").pack(side=tk.LEFT)
        tk.Radiobutton(type_frame, text="半成品", variable=type_var, value="material").pack(side=tk.LEFT)

        # 创建搜索区域
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(search_frame, text="搜索配方:").pack(side=tk.LEFT)
        search_entry = tk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # 当前使用的列表框和数据
        current_listbox = None
        current_data = None

        # 更新列表框内容的函数
        def update_listbox():
            nonlocal current_listbox, current_data
            list_type = type_var.get()

            # 根据选择的类型获取对应数据
            if list_type == 'all':
                current_data = self.products_data + self.base_data + self.materials_data
            if list_type == "product":
                current_data = self.products_data
            elif list_type == "material":
                current_data = self.materials_data
            else:  # base
                current_data = self.base_data

            # 清空列表框
            current_listbox.delete(0, tk.END)

            # 填充列表框
            search_text = search_entry.get()
            for item in current_data:
                if search_text in item['name']:
                    current_listbox.insert(tk.END, item['name'])

        # 绑定搜索框事件和类型选择事件
        search_entry.bind("<KeyRelease>", lambda event: update_listbox())
        type_var.trace_add("write", lambda *args: update_listbox())

        # 创建配方列表
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建列表框
        current_listbox = tk.Listbox(list_frame, width=50, yscrollcommand=scrollbar.set)
        current_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=current_listbox.yview)

        # 填充配方列表
        # 初始填充列表框
        update_listbox()

        # 创建按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # 查看配方按钮
        def view_selected_recipe():
            selection = current_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一个配方")
                return

            item_name = current_listbox.get(selection[0])
            item_type = type_var.get()

            if item_type == "product":
                self.show_recipe_tree(item_name)  # 查看产品配方树
            else:
                # 查看原材料或基础材料信息
                dialog = self.create_centered_window(f"{item_name} 信息", 400, 300, True)

                # 查找项目信息
                item_info = next((item for item in current_data if item['name'] == item_name), None)
                if item_info:
                    # 显示项目信息
                    for key, value in item_info.items():
                        tk.Label(dialog, text=f"{key}: {value}").pack(anchor=tk.W, padx=10, pady=5)
                else:
                    tk.Label(dialog, text="未找到项目信息").pack(padx=10, pady=10)

        tk.Button(button_frame, text="查看配方", command=view_selected_recipe).pack(side=tk.LEFT, padx=5)

        # 删除配方按钮
        def delete_selected_item():
            selection = current_listbox.curselection()
            if not selection:
                messagebox.showinfo("提示", "请先选择一个配方")
                return

            item_name = current_listbox.get(selection[0])
            item_type = type_var.get()
            confirm = messagebox.askyesno("确认删除",
                                          f"确定要删除{item_type == 'products' and '配方' or '项目'} '{item_name}' 吗？")

            if confirm:
                # 查找并删除项目
                data_list = None
                save_method = None

                if item_type == "products":
                    data_list = self.products_data
                    save_method = self.save_product
                elif item_type == "materials":
                    data_list = self.materials_data
                    save_method = self.save_material
                else:  # base
                    data_list = self.base_data
                    save_method = self.save_base

                # 从数据中删除
                for i, item in enumerate(data_list):
                    if item['name'] == item_name:
                        del data_list[i]
                        break

                # 从列表中删除
                current_listbox.delete(selection[0])

                # 保存到文件
                try:
                    if save_method:
                        save_method()
                    messagebox.showinfo("成功", f"{item_type == 'products' and '配方' or '项目'} '{item_name}' 已删除")
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {str(e)}")

        tk.Button(button_frame, text="删除项目", command=delete_selected_item).pack(side=tk.LEFT, padx=5)

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

    def save_base(self):
        with open(f'{save_path}/base/index.json', 'w', encoding='UTF-8') as f:
            json.dump(self.base_data, f, indent=2, ensure_ascii=False)

    def save_material(self):
        with open(f'{save_path}/materials/index.json', 'w', encoding='UTF-8') as f:
            json.dump(self.materials_data, f, indent=2, ensure_ascii=False)

    def save_product(self):
        with open(f'{save_path}/products/index.json', 'w', encoding='UTF-8') as f:
            json.dump(self.products_data, f, indent=2, ensure_ascii=False)

    def create_centered_window(self, title="新窗口", width=800, height=600, modal=False, resizable=(True, True),
                               on_create=None):
        """创建一个居中于主窗口的顶级窗口，可选择是否为模态对话框及是否可调整大小"""
        # 获取主窗口位置和尺寸
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        # 计算新窗口的位置
        new_x = x + (root_width - width) // 2
        new_y = y + (root_height - height) // 2

        # 创建并配置新窗口
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(f"{width}x{height}+{new_x}+{new_y}")
        window.transient(self.root)  # 设置为主窗口的子窗口

        # 设置窗口是否可调整大小
        window.resizable(resizable[0], resizable[1])

        # 如果是模态对话框，添加 grab_set
        if modal:
            window.grab_set()
        # 执行回调函数（如果提供）
        if on_create:
            on_create(window)

        return window  # 返回新创建的窗口

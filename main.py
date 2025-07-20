import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random


#狗屎DF仓库整理算法使我无法放置物品，使我思索1晚上


class BinPackingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DF仓库最优存法    github.com/Rmtix1337")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        #Fix Font
        plt.rcParams["font.family"] = ["SimHei", "Microsoft YaHei"]
        plt.ioff()  # 禁用交互模式，避免线程冲突

        # 物品尺寸列表
        self.item_sizes = [(1,1), (1,2), (1,3), (1,4), (1,5),
                           (2,2), (2,3), (2,4), (2,5),  # 新增2x5
                           (3,3), (3,4),
                           (4,4)]

        # 创建主框架，使用网格布局
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧输入面板
        input_frame = ttk.LabelFrame(main_frame, text="输入参数", padding="10")
        input_frame.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W, padx=(0, 10))

        # 右侧结果面板
        result_frame = ttk.LabelFrame(main_frame, text="装箱结果", padding="10")
        result_frame.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)

        # 设置网格权重，使右侧面板可以扩展
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)

        # 容器尺寸输入
        ttk.Label(input_frame, text="容器宽度:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.width_entry = ttk.Entry(input_frame, width=10)
        self.width_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.width_entry.insert(0, "10")  # 默认值

        ttk.Label(input_frame, text="容器高度:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.height_entry = ttk.Entry(input_frame, width=10)
        self.height_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.height_entry.insert(0, "10")  # 默认值

        # 物品数量输入
        ttk.Label(input_frame, text="物品数量:").grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W)

        self.item_entries = {}
        row, col = 3, 0
        for i, (w, h) in enumerate(self.item_sizes):
            ttk.Label(input_frame, text=f"{w}x{h}:").grid(row=row, column=col*2, padx=5, pady=3, sticky=tk.W)
            entry = ttk.Entry(input_frame, width=8)
            entry.grid(row=row, column=col*2+1, padx=5, pady=3, sticky=tk.W)
            self.item_entries[(w, h)] = entry

            col += 1
            if col >= 2:  # 每行显示2个物品
                col = 0
                row += 1

        #添加分隔线
        separator = ttk.Separator(input_frame, orient="horizontal")
        separator.grid(row=row+1, column=0, columnspan=4, sticky=tk.E+tk.W, pady=10)
        row += 2

        #输出按钮
        self.calculate_btn = ttk.Button(input_frame, text="计算方案", command=self.calculate, width=20)
        self.calculate_btn.grid(row=row, column=0, columnspan=4, padx=5, pady=10)

        #创建mpl方案
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=result_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 初始显示
        self.ax.text(0.5, 0.5, "请传参并点 计算按钮",
                     horizontalalignment='center',
                     verticalalignment='center',
                     transform=self.ax.transAxes)
        self.canvas.draw()

    def get_input_values(self):
        """验证数值合法性   github.com/Rmtix1337"""
        try:
            # get item[size]
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())

            if width <= 0 or height <= 0:
                messagebox.showerror("输入错误", "容器宽高必须为正整数")
                return None

            # get item[num]
            items = []
            for (w, h), entry in self.item_entries.items():
                try:
                    count = int(entry.get()) if entry.get() else 0
                    if count < 0:
                        messagebox.showerror("输入错误", f"{w}x{h}的数量不能为负数")
                        return None
                    for _ in range(count):
                        items.append((w, h))
                except ValueError:
                    messagebox.showerror("输入错误", f"{w}x{h}的数量必须为整数")
                    return None

            return {
                "width": width,
                "height": height,
                "items": items
            }
        except ValueError:
            messagebox.showerror("输入错误", "容器宽高必须为整数")
            return None

    def can_place_item(self, bin_matrix, x, y, width, height):
        """放置物品能否放置检测   github.com/Rmtix1337"""
        bin_height, bin_width = bin_matrix.shape

        # 检查是否超出边界
        if x + width > bin_width or y + height > bin_height:
            return False

        # 检查是否与已有物品重叠
        for i in range(y, y + height):
            for j in range(x, x + width):
                if bin_matrix[i, j] != 0:
                    return False

        return True

    def place_item(self, bin_matrix, x, y, width, height, item_id):
        """指定位置放置物品   github.com/Rmtix1337"""
        for i in range(y, y + height):
            for j in range(x, x + width):
                bin_matrix[i, j] = item_id
        return bin_matrix

    def find_best_position(self, bin_matrix, item_width, item_height):
        """寻找最佳位置（启发式算法）   github.com/Rmtix1337"""
        bin_height, bin_width = bin_matrix.shape

        # 尝试两种方向（原始和旋转）
        for w, h in [(item_width, item_height), (item_height, item_width)]:
            # 从上到下，从左到右寻找第一个可以放置的位置
            for y in range(bin_height - h + 1):
                for x in range(bin_width - w + 1):
                    if self.can_place_item(bin_matrix, x, y, w, h):
                        return x, y, w, h

        return None, None, None, None  # 无法放置

    def pack_items(self, bin_width, bin_height, items):
        """算法：按面积降序排列，优先放置大物品   github.com/Rmtix1337"""
        # 初始化容器矩阵（0表示空，其他值表示物品ID）
        bin_matrix = np.zeros((bin_height, bin_width), dtype=int)

        # 按面积降序排序物品，优先放置大物品
        items_sorted = sorted(items, key=lambda x: x[0]*x[1], reverse=True)

        placed_items = []  # 记录已放置的物品信息 (x, y, width, height, item_id)
        unplaced_items = []  # 记录无法放置的物品

        for item_id, (w, h) in enumerate(items_sorted, 1):
            x, y, placed_w, placed_h = self.find_best_position(bin_matrix, w, h)

            if x is not None:  # 可以放置
                bin_matrix = self.place_item(bin_matrix, x, y, placed_w, placed_h, item_id)
                placed_items.append((x, y, placed_w, placed_h, item_id))
            else:  # 无法放置
                unplaced_items.append((w, h))

        return bin_matrix, placed_items, unplaced_items

    def visualize_result(self, bin_width, bin_height, placed_items, unplaced_items):
        """可视化结果   github.com/Rmtix1337"""
        self.ax.clear()
        self.ax.set_xlim(0, bin_width)
        self.ax.set_ylim(0, bin_height)
        self.ax.set_aspect('equal')
        self.ax.set_xticks(range(bin_width + 1))
        self.ax.set_yticks(range(bin_height + 1))
        self.ax.grid(True, linestyle='--', alpha=0.7)

        # 绘制容器边界
        self.ax.add_patch(Rectangle((0, 0), bin_width, bin_height,
                                    fill=False, edgecolor='black', linewidth=2))

        # 生成随机颜色
        colors = []
        for _ in range(len(placed_items) + 1):
            # 生成柔和的颜色
            r = 0.3 + random.random() * 0.6
            g = 0.3 + random.random() * 0.6
            b = 0.3 + random.random() * 0.6
            colors.append((r, g, b, 0.7))

        # 绘制已放置的物品
        for x, y, w, h, item_id in placed_items:
            # 注意：matplotlib的y轴是从上到下的，而我们的逻辑是从下到上的，所以需要翻转
            self.ax.add_patch(Rectangle(
                (x, bin_height - y - h), w, h,
                fill=True, edgecolor='black',
                facecolor=colors[item_id % len(colors)],
                linewidth=1.5
            ))
            # 在物品中心添加尺寸标签
            self.ax.text(
                x + w/2, bin_height - y - h/2,
                f"{w}x{h}",
                ha='center', va='center',
                fontsize=8, fontweight='bold'
            )

        self.fig.suptitle(f"容器尺寸: {bin_width}x{bin_height}", fontsize=12)

        # 显示无法放置的物品
        if unplaced_items:
            unplaced_text = "无法放置的物品: "
            item_counts = {}
            for w, h in unplaced_items:
                # 考虑旋转，统一为宽<=高的表示
                key = tuple(sorted((w, h)))
                item_counts[key] = item_counts.get(key, 0) + 1

            unplaced_text += ", ".join([f"{w}x{h} ×{count}" for (w, h), count in item_counts.items()])

            # 在图表下方添加文本
            plt.figtext(0.5, 0.01, unplaced_text,
                        ha='center', fontsize=9, color='red')

        self.canvas.draw()

    def calculate(self):
        """show best"""
        input_data = self.get_input_values()
        if not input_data:
            return

        bin_width = input_data["width"]
        bin_height = input_data["height"]
        items = input_data["items"]

        if not items:
            messagebox.showinfo("提示", "请至少输入一个物品")
            return

        # 执行算法
        bin_matrix, placed_items, unplaced_items = self.pack_items(bin_width, bin_height, items)

        # 可视化结果
        self.visualize_result(bin_width, bin_height, placed_items, unplaced_items)

        # 显示统计信息
        total_items = len(items)
        placed_count = len(placed_items)
        unplaced_count = len(unplaced_items)

        # 计算空间利用率
        total_item_area = sum(w*h for _, _, w, h, _ in placed_items)
        bin_area = bin_width * bin_height
        utilization = (total_item_area / bin_area) * 100 if bin_area > 0 else 0

        stats_text = (f"总物品数: {total_items}\n"
                      f"已放置: {placed_count}\n"
                      f"未放置: {unplaced_count}\n"
                      f"空间利用率: {utilization:.2f}%")

        messagebox.showinfo("DF仓库最优存法  github.com/Rmtix1337", stats_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = BinPackingApp(root)
    root.mainloop()
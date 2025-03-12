# -*- coding: utf-8 -*-
import json
import os
import socket
import sys
import tkinter as tk
import tkinter.simpledialog as simpledialog
import webbrowser  # 添加导入webbrowser模块
# 增加剪贴板模块导入
from tkinter import TclError, messagebox, ttk

# 初始化
# 判断环境是exe还是py
if getattr(sys, 'frozen', False):
    quanju_lujin = os.path.dirname(sys.executable)
    quanju_lujin_shang = os.path.abspath(os.path.join(quanju_lujin, os.pardir))
else:
    quanju_lujin = os.path.dirname(os.path.abspath(sys.argv[0]))
    quanju_lujin_shang = os.path.abspath(os.path.join(quanju_lujin, os.pardir))

# 检测数据文件路径
if not os.path.exists(f"{quanju_lujin}/data/orderlist.json"):
    if not os.path.exists(f"{quanju_lujin_shang}/data/orderlist.json"):
        messagebox.showinfo("终端命令编辑器", "未能读取到数据库")
        os._exit(0)
    else:
        zhenque_lujin = (f"{quanju_lujin_shang}/data/orderlist.json")
else:
    zhenque_lujin = (f"{quanju_lujin}/data/orderlist.json")

# 检测图标文件路径
icon_path = None
possible_icon_paths = [
    os.path.join(quanju_lujin, "1.ico"),
    os.path.join(quanju_lujin, "app", "1.ico"),
    os.path.join(quanju_lujin_shang, "1.ico"),
    os.path.join(quanju_lujin_shang, "app", "1.ico")
]

for path in possible_icon_paths:
    if os.path.exists(path):
        icon_path = path
        break


class CustomDialog(tk.Toplevel):
    """自定义对话框，确保窗口大小合适"""
    def __init__(self, parent, title, prompt, initialvalue=None):
        super().__init__(parent)
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        self.title(title)
        self.result = None
        
        # 设置窗口图标
        if icon_path:
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"无法加载图标: {str(e)}")
        
        # 设置窗口大小
        window_width = 400
        window_height = 150
        self.resizable(False, False)
        self.transient(parent)  # 设置为父窗口的临时窗口
        self.grab_set()  # 模态窗口
        
        # 计算屏幕中央位置
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        
        # 设置窗口位置到屏幕中央
        self.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
        
        # 窗口布局
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 提示标签
        ttk.Label(main_frame, text=prompt).pack(anchor="w", pady=(0, 5))
        
        # 输入框
        self.entry = ttk.Entry(main_frame, width=50)
        self.entry.pack(fill="x", pady=5)
        if initialvalue:
            self.entry.insert(0, initialvalue)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", expand=True, pady=(10, 0))
        
        # 添加确定和取消按钮（位置互换）
        ttk.Button(button_frame, text="确定", command=self.ok_command, width=10).pack(side="left", padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel_command, width=10).pack(side="right", padx=5)
        
        # 绑定事件
        self.bind("<Return>", lambda event: self.ok_command())
        self.bind("<Escape>", lambda event: self.cancel_command())
        
        # 确保所有几何计算完成
        self.update_idletasks()
        
        # 完成所有配置后再显示窗口
        self.deiconify()
        
        # 设置焦点
        self.entry.focus_set()
        
        # 等待窗口关闭
        self.wait_window(self)
    
    def ok_command(self):
        """确定按钮点击事件"""
        self.result = self.entry.get()
        self.destroy()
    
    def cancel_command(self):
        """取消按钮点击事件"""
        self.result = None
        self.destroy()


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5, font=('微软雅黑', 10))
        self.style.configure("TLabel", font=('微软雅黑', 10))
        self.style.configure("Title.TLabel", font=('微软雅黑', 16, 'bold'))
        
        # 创建提示文字区域
        self.create_tip_area()
        
        # 加载数据
        with open(zhenque_lujin, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # 创建主界面布局
        self.create_main_layout()
        
        # 初始化菜单列表
        self.init_menu_list()

    def create_tip_area(self):
        """创建提示区域"""
        tip_frame = ttk.Frame(self)
        tip_frame.pack(side="top", fill="x", pady=5)
        
        tip_title = ttk.Label(tip_frame, text="终端命令编辑器", style="Title.TLabel")
        tip_title.pack(side="top", pady=5)
        
        tip_text = ttk.Label(
            tip_frame,
            text="锁定命令条，即可让执行的IP地址固定，不会因为终端的地址变化而变化\n添加自定义命令，就是cmd命令，记得在你的命令前面添加 “cmd.exe /c 你的命令”\n添加URL，任意API链接只支持GET模式\n已锁定未锁定作用是让IP会不会变化，但是新版本已经去除了IP变化功能,所以无意义",
            wraplength=600,
        )
        tip_text.pack(side="top", pady=5)
        
        # 添加分隔线
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill='x', pady=5)

    def create_main_layout(self):
        """创建主界面布局"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建列表框和滚动条的容器
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 创建列表框和滚动条
        self.menu_list = tk.Listbox(list_frame, width=50, height=15, font=("微软雅黑", 11), borderwidth=1, relief="solid")
        self.menu_list.pack(side="left", fill="both", expand=True)
        
        # 删除tag_configure行，Listbox没有此方法
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.menu_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.menu_list.config(yscrollcommand=scrollbar.set)
        
        # 绑定事件
        self.menu_list.bind("<ButtonRelease-1>", self.on_select)
        
        # 按钮区域 - 使用网格布局分组排列
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side="left", fill="y", padx=(10, 0))
        
        # 第一组按钮：操作当前命令
        operation_frame = ttk.LabelFrame(button_frame, text="当前命令操作")
        operation_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        self.lock_button = ttk.Button(operation_frame, text="锁定状态", command=self.toggle_lock)
        self.lock_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.modify_command_button = ttk.Button(
            operation_frame, text="编辑", command=self.modify_command, state="disabled"
        )
        self.modify_command_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.delete_command_button = ttk.Button(
            operation_frame, text="删除命令", command=self.delete_command, state="disabled"
        )
        self.delete_command_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        # 第二组按钮：添加新命令
        add_frame = ttk.LabelFrame(button_frame, text="添加新命令")
        add_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        self.custom_command_button = ttk.Button(add_frame, text="添加自定义命令", command=self.add_custom_command)
        self.custom_command_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.add_url_button = ttk.Button(add_frame, text="添加URL", command=self.add_url)
        self.add_url_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 添加导入剪贴板按钮
        self.import_clipboard_button = ttk.Button(add_frame, text="从剪贴板导入", command=self.import_from_clipboard)
        self.import_clipboard_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # 添加自定义命令社区按钮
        self.community_button = ttk.Button(add_frame, text="自定义命令社区", command=self.open_community_website)
        self.community_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # 第三组按钮：移动命令
        move_frame = ttk.LabelFrame(button_frame, text="调整顺序")
        move_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        self.move_up_button = ttk.Button(move_frame, text="上移", command=self.move_up, state="disabled")
        self.move_up_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.move_down_button = ttk.Button(move_frame, text="下移", command=self.move_down, state="disabled")
        self.move_down_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def toggle_lock(self):
        """切换锁定状态"""
        selection = self.menu_list.curselection()
        if not selection:
            return
        
        index = selection[0]
        item = self.data[index]
        if item["guding"] == "y":
            item["guding"] = "n"
            self.lock_button.config(text="未锁定")
        else:
            item["guding"] = "y"
            self.lock_button.config(text="已锁定")
        self.save_data()

    def save_data(self):
        """保存数据到文件"""
        try:
            with open(zhenque_lujin, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存数据: {str(e)}")

    def init_menu_list(self):
        """初始化菜单列表"""
        self.menu_list.delete(0, tk.END)
        for i, item in enumerate(self.data):
            title = item["title"]
            
            if "datacommand" in item:
                title += " [自定义命令]"
                self.menu_list.insert(tk.END, title)
                self.menu_list.itemconfig(i, foreground="green")
            elif "apiUrlCommand" in item:
                title += " [API链接]"
                self.menu_list.insert(tk.END, title)
                self.menu_list.itemconfig(i, foreground="red")
            else:
                self.menu_list.insert(tk.END, title)

    def on_select(self, event):
        """列表选择事件处理"""
        if not self.menu_list.curselection():
            self.reset_buttons()
            return

        index = self.menu_list.curselection()[0]
        item = self.data[index]
        
        # 更新按钮状态 - 修改逻辑以处理所有类型的项目
        can_edit = "datacommand" in item or ("apiUrlCommand" in item and item["apiUrlCommand"] == "yes")
        can_delete = can_edit or ("url" in item and item["url"] == "yes")
        
        self.modify_command_button.config(state="normal" if can_edit else "disabled")
        self.delete_command_button.config(state="normal" if can_delete else "disabled")

        # 设置锁定按钮文本
        lock_text = "已锁定" if item["guding"] == "y" else "未锁定"
        self.lock_button.config(text=lock_text)

        # 更新移动按钮状态
        self.update_move_buttons()

    def reset_buttons(self):
        """重置按钮状态"""
        self.modify_command_button.config(state="disabled")
        self.delete_command_button.config(state="disabled")
        self.lock_button.config(text="锁定状态")
        self.move_up_button.config(state="disabled")
        self.move_down_button.config(state="disabled")

    def modify_command(self):
        """修改命令"""
        selection = self.menu_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        item = self.data[index]
        
        if "datacommand" in item:
            dialog_title = "修改命令"
            dialog_text = "请输入新命令"
            initial_value = item["datacommand"]
            
            dialog = CustomDialog(self.master, dialog_title, dialog_text, initial_value)
            new_command = dialog.result
            
            if new_command is not None:
                item["datacommand"] = new_command
                self.save_data()
                
        elif "apiUrlCommand" in item and item["apiUrlCommand"] == "yes":
            dialog_title = "修改API URL"
            dialog_text = "请输入新的API URL"
            initial_value = item["apiUrl"]
            
            dialog = CustomDialog(self.master, dialog_title, dialog_text, initial_value)
            new_url = dialog.result
            
            if new_url is not None:
                item["apiUrl"] = new_url
                self.save_data()

    def add_custom_command(self):
        """添加自定义命令"""
        dialog = CustomDialog(self.master, "添加自定义命令", "请输入标题")
        title = dialog.result
        
        if title is not None:
            dialog = CustomDialog(self.master, "添加自定义命令", "请输入命令")
            datacommand = dialog.result
            
            if datacommand is not None:
                self.data.append({
                    "title": title,
                    "apiUrl": f"http://*hanhanip*:5202/command",
                    "guding": "n",
                    "datacommand": datacommand,
                })
                
                # 更新列表并选中新项目
                index = len(self.data) - 1
                self.menu_list.insert(tk.END, title + " [自定义命令]")
                self.menu_list.itemconfig(index, foreground="green")  # 直接设置颜色
                self.menu_list.selection_clear(0, tk.END)
                self.menu_list.select_set(index)
                self.menu_list.see(index)  # 确保新项目可见
                
                # 更新按钮状态并保存
                self.on_select(None)
                self.save_data()

    def delete_command(self):
        """删除命令"""
        selection = self.menu_list.curselection()
        if not selection:
            return
            
        index = selection[0]
        item = self.data[index]
        
        confirm = messagebox.askyesno("确认删除", f"确定要删除命令 {item['title']} 吗？")
        if confirm:
            self.menu_list.delete(index)
            del self.data[index]
            self.save_data()
            self.reset_buttons()

    def add_url(self):
        """添加URL"""
        dialog = CustomDialog(self.master, "添加URL", "请输入标题")
        title = dialog.result
        
        if title is not None:
            dialog = CustomDialog(self.master, "添加URL", "请输入API URL")
            apiUrl = dialog.result
            
            if apiUrl is not None:
                self.data.append({
                    "title": title, 
                    "apiUrl": apiUrl, 
                    "guding": "y", 
                    "url": "yes"
                })
                
                # 更新列表并选中新项目
                index = len(self.data) - 1
                self.menu_list.insert(tk.END, title + " [API链接]")
                self.menu_list.itemconfig(index, foreground="red")
                self.menu_list.selection_clear(0, tk.END)
                self.menu_list.select_set(index)
                self.menu_list.see(index)  # 确保新项目可见
                
                # 更新按钮状态并保存
                self.on_select(None)
                self.save_data()

    def move_up(self):
        """上移命令"""
        index = self.menu_list.curselection()[0]
        if index > 0:
            self.data[index], self.data[index - 1] = self.data[index - 1], self.data[index]
            self.init_menu_list()
            self.save_data()
            
            # 保持选择在移动后的项目上
            self.menu_list.selection_clear(0, tk.END)
            self.menu_list.select_set(index - 1)
            self.menu_list.see(index - 1)
            self.update_move_buttons()

    def move_down(self):
        """下移命令"""
        index = self.menu_list.curselection()[0]
        if index < len(self.data) - 1:
            self.data[index], self.data[index + 1] = self.data[index + 1], self.data[index]
            self.init_menu_list()
            self.save_data()
            
            # 保持选择在移动后的项目上
            self.menu_list.selection_clear(0, tk.END)
            self.menu_list.select_set(index + 1)
            self.menu_list.see(index + 1)
            self.update_move_buttons()

    def update_move_buttons(self):
        """更新移动按钮状态"""
        if not self.menu_list.curselection():
            self.move_up_button.config(state="disabled")
            self.move_down_button.config(state="disabled")
            return
            
        index = self.menu_list.curselection()[0]
        self.move_up_button.config(state="normal" if index > 0 else "disabled")
        self.move_down_button.config(state="normal" if index < len(self.data) - 1 else "disabled")

    def import_from_clipboard(self):
        """从剪贴板导入命令"""
        try:
            # 获取剪贴板内容
            clipboard_content = self.master.clipboard_get()
            
            # 移除开头和结尾的多余字符，确保是有效的JSON
            clipboard_content = clipboard_content.strip()
            if clipboard_content.startswith("'''") and clipboard_content.endswith("'''"):
                clipboard_content = clipboard_content[3:-3].strip()
            
            # 处理最后可能有的逗号
            if clipboard_content.endswith(","):
                clipboard_content = clipboard_content[:-1]
                
            # 尝试解析JSON
            try:
                item = json.loads(clipboard_content)
                
                # 检查是自定义命令还是URL类型
                if "datacommand" in item:
                    # 自定义命令类型
                    new_item = {
                        "title": item.get("title", "未命名命令"),
                        "apiUrl": "http://*hanhanip*:5202/command",
                        "guding": item.get("guding", "n"),
                        "datacommand": item.get("datacommand", "")
                    }
                    display_text = f"{new_item['title']} [自定义命令]"
                    color = "green"
                elif "apiUrlCommand" in item and item["apiUrlCommand"] == "yes":
                    # URL类型
                    new_item = {
                        "title": item.get("title", "未命名URL"),
                        "apiUrl": item.get("apiUrl", ""),
                        "guding": item.get("guding", "y"),
                        "apiUrlCommand": "yes"
                    }
                    display_text = f"{new_item['title']} [API链接]"
                    color = "red"
                else:
                    messagebox.showerror("导入失败", "剪贴板中的数据格式不正确")
                    return
                
                # 添加到数据列表
                self.data.append(new_item)
                
                # 更新列表并选中新项目
                index = len(self.data) - 1
                self.menu_list.insert(tk.END, display_text)
                self.menu_list.itemconfig(index, foreground=color)
                self.menu_list.selection_clear(0, tk.END)
                self.menu_list.select_set(index)
                self.menu_list.see(index)  # 确保新项目可见
                
                # 更新按钮状态并保存
                self.on_select(None)
                self.save_data()
                messagebox.showinfo("导入成功", f"已成功导入命令: {new_item['title']}")
                
            except json.JSONDecodeError:
                messagebox.showerror("导入失败", "剪贴板中的内容不是有效的JSON格式")
        except TclError:
            messagebox.showerror("导入失败", "剪贴板为空或内容无法读取")

    def open_community_website(self):
        """打开自定义命令社区网站"""
        url_file_path = f"{quanju_lujin}{os.sep}url.json"
        
        try:
            if os.path.exists(url_file_path):
                with open(url_file_path, "r", encoding="utf-8") as f:
                    url_data = json.load(f)
                    if "url" in url_data:
                        webbrowser.open(url_data["url"])
                    else:
                        messagebox.showerror("错误", "URL文件中未找到url元素")
            else:
                messagebox.showerror("错误", f"未找到URL文件：{url_file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"打开社区网站失败: {str(e)}")


def main():
    root = tk.Tk()
    root.title("终端命令编辑器")
    
    # 设置窗口图标
    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"无法加载图标: {str(e)}")
    
    # 设置窗口大小
    window_width = 780
    window_height = 550
    root.minsize(600, 400)
    
    # 计算屏幕中央位置
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    
    # 设置窗口位置到屏幕中央
    root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")
    
    app = App(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()

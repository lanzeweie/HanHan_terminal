import tkinter as tk
import json
import tkinter.simpledialog as simpledialog
from tkinter import messagebox
import os
import sys

# 初始化
# 判断环境是exe还是py
if getattr(sys, 'frozen', False):
    quanju_lujin = os.path.dirname(sys.executable)
    quanju_lujin_shang = os.path.abspath(os.path.join(quanju_lujin, os.pardir))
else:
    quanju_lujin = os.path.dirname(os.path.abspath(__file__))
    quanju_lujin_shang = os.path.abspath(os.path.join(quanju_lujin, os.pardir))

if not os.path.exists(f"{quanju_lujin}/data/orderlist.json"):
    if not os.path.exists(f"{quanju_lujin_shang}/data/orderlist.json"):
        messagebox.showinfo("终端命令编辑器", "未能读取到数据库")
        os._exit(0)
    else:
        zhenque_lujin = (f"{quanju_lujin_shang}/data/orderlist.json")
else:
    zhenque_lujin = (f"{quanju_lujin}/data/orderlist.json")


class App(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        # 创建提示文字区域
        self.tip_frame = tk.Frame(self, width=400, height=40)
        self.tip_frame.pack(side="top", padx=10, pady=10)
        self.tip_title = tk.Label(self.tip_frame, text="终端命令编辑器", font=("Arial", 16, "bold"))
        self.tip_title.pack(side="top", padx=5, pady=5)
        self.tip_text = tk.Label(
            self.tip_frame,
            text="锁定命令条，即可让执行的IP地址固定，不会因为终端的地址变化而变化\n添加自定义命令，只能添加执行cmd命令\n添加URL，任意API链接只支持GET模式",
            font=("Arial", 9),
        )
        self.tip_text.pack(side="top", padx=5, pady=5)

        # 加载数据
        with open(zhenque_lujin, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # 创建菜单列表
        self.menu_list = tk.Listbox(self, width=50, height=10, font=("Arial", 11))
        self.menu_list.pack(side="left", padx=10, pady=10)

        # 创建按钮区域
        self.button_frame = tk.Frame(self, width=200, height=100)
        self.button_frame.pack(side="left", padx=10, pady=10)

        # 创建按钮
        self.menu_list.selection_set(0)
        if self.menu_list.curselection():
            index = self.menu_list.curselection()[0]
        else:
            index = 0
        item = self.data[index]
        lock_text = "已锁定" if item["guding"] == "y" else "未锁定"
        self.lock_button = tk.Button(self.button_frame, text=lock_text, command=self.toggle_lock)
        self.lock_button.pack(side="left", padx=10, pady=10)
        self.custom_command_button = tk.Button(self.button_frame, text="添加自定义命令", command=self.add_custom_command)
        self.custom_command_button.pack(side="left", padx=10, pady=10)
        self.modify_command_button = tk.Button(
            self.button_frame, text="修改命令", command=self.modify_command, state="disabled"
        )
        self.modify_command_button.pack(side="left", padx=10, pady=10)
        self.add_url_button = tk.Button(self.button_frame, text="添加URL", command=self.add_url)
        self.add_url_button.pack(side="left", padx=10, pady=10)

        # 上移和下移按钮
        self.move_up_button = tk.Button(self.button_frame, text="上移", command=self.move_up, state="disabled")
        self.move_up_button.pack(side="left", padx=10, pady=10)
        self.move_down_button = tk.Button(self.button_frame, text="下移", command=self.move_down, state="disabled")
        self.move_down_button.pack(side="left", padx=10, pady=10)

        # 绑定事件
        self.menu_list.bind("<ButtonRelease-1>", self.on_select)
        self.delete_command_button = tk.Button(
            self.button_frame, text="删除命令", command=self.delete_command, state="disabled"
        )
        self.delete_command_button.pack(side="left", padx=10, pady=10)

        # 初始化菜单列表
        self.init_menu_list()

    def toggle_lock(self):
        index = self.menu_list.curselection()[0]
        item = self.data[index]
        if item["guding"] == "y":
            item["guding"] = "n"
            self.lock_button.config(text="未锁定")
        else:
            item["guding"] = "y"
            self.lock_button.config(text="已锁定")
        self.save_data()

    def save_data(self):
        with open(zhenque_lujin, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def init_menu_list(self):
        for item in self.data:
            title = item["title"]

            if "datacommand" in item:
                title += " [自定义命令]"
            if "apiUrlCommand" in item:
                title += " [API链接]"
            self.menu_list.insert(tk.END, title)

    def on_select(self, event):
        if event is None:
            # no event, clear the selection
            self.modify_command_button.config(state="disabled")
            self.lock_button.config(text="")
            self.move_up_button.config(state="disabled")
            self.move_down_button.config(state="disabled")
            return

        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            item = self.data[index]
            if "datacommand" in item or ("apiUrlCommand" in item and item["apiUrlCommand"] == "yes"):
                self.modify_command_button.config(state="normal")
                self.delete_command_button.config(state="normal")
            else:
                self.modify_command_button.config(state="disabled")
                self.delete_command_button.config(state="disabled")

            # 设置锁定按钮文本
            lock_text = "已锁定" if item["guding"] == "y" else "未锁定"
            self.lock_button.config(text=lock_text)

            # 设置上移和下移按钮状态
            if index > 0:
                self.move_up_button.config(state="normal")
            if index < len(self.data) - 1:
                self.move_down_button.config(state="normal")

    def modify_command(self):
        selection = self.menu_list.curselection()
        if selection:
            index = selection[0]
            item = self.data[index]
            if "datacommand" in item:
                dialog_title = "修改命令"
                dialog_text = "请输入新命令"
                dialog = Dialog(self.master, dialog_title, dialog_text, item["datacommand"])
                new_command = dialog.result
                if new_command is not None:
                    item["datacommand"] = new_command
                    self.save_data()
            elif "apiUrlCommand" in item and item["apiUrlCommand"] == "yes":
                dialog_title = "修改API URL"
                dialog_text = "请输入新的API URL"
                dialog = Dialog(self.master, dialog_title, dialog_text, item["apiUrl"])
                new_url = dialog.result
                if new_url is not None:
                    item["apiUrl"] = new_url
                    self.save_data()

    def add_custom_command(self):
        dialog = Dialog(self.master, "添加自定义命令", "请输入标题", "")
        title = dialog.result
        if title is not None:
            dialog = Dialog(self.master, "添加自定义命令", "请输入命令", "")
            datacommand = dialog.result
            if datacommand is not None:
                self.data.append(
                    {
                        "title": title,
                        "apiUrl": "http://192.168.208.17:5202/command",
                        "guding": "n",
                        "datacommand": datacommand,
                    }
                )
                index = len(self.data) - 1
                self.menu_list.insert(tk.END, title + " [自定义命令]")
                self.menu_list.selection_clear(0, tk.END)
                self.menu_list.select_set(index)
                self.on_select(None)  # clear the selection
                with open(zhenque_lujin, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)

    def delete_command(self):
        selection = self.menu_list.curselection()
        if selection:
            index = selection[0]
            item = self.data[index]
            confirm = messagebox.askyesno("确认删除", f"确定要删除命令 {item['title']} 吗？")
            if confirm:
                self.menu_list.delete(index)
                del self.data[index]
                self.save_data()
                self.on_select(None)  # clear the selection

    def add_url(self):
        dialog = Dialog(self.master, "添加URL", "请输入标题", "")
        title = dialog.result
        if title is not None:
            dialog = Dialog(self.master, "添加URL", "请输入API URL", "")
            apiUrl = dialog.result
            if apiUrl is not None:
                self.data.append(
                    {"title": title, "apiUrl": apiUrl, "guding": "y", "url": "yes"}
                )
                index = len(self.data) - 1
                self.menu_list.insert(tk.END, title + " [API链接]")
                self.menu_list.selection_clear(0, tk.END)
                self.menu_list.select_set(index)
                self.on_select(None)  # clear the selection
                with open(zhenque_lujin, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)

    def move_up(self):
        index = self.menu_list.curselection()[0]
        if index > 0:
            self.data[index], self.data[index - 1] = self.data[index - 1], self.data[index]
            self.menu_list.delete(0, tk.END)
            self.init_menu_list()
            self.save_data()
            self.menu_list.selection_clear(0, tk.END)
            self.menu_list.select_set(index - 1)
            self.on_select(None)
            self.update_move_buttons()  # 更新上移和下移按钮状态

    def move_down(self):
        index = self.menu_list.curselection()[0]
        if index < len(self.data) - 1:
            self.data[index], self.data[index + 1] = self.data[index + 1], self.data[index]
            self.menu_list.delete(0, tk.END)
            self.init_menu_list()
            self.save_data()
            self.menu_list.selection_clear(0, tk.END)
            self.menu_list.select_set(index + 1)
            self.on_select(None)
            self.update_move_buttons()  # 更新上移和下移按钮状态

    def update_move_buttons(self):
        index = self.menu_list.curselection()[0]
        self.move_up_button.config(state="normal" if index > 0 else "disabled")
        self.move_down_button.config(state="normal" if index < len(self.data) - 1 else "disabled")

class Dialog(simpledialog.Dialog):
    def __init__(self, parent, title, text, initialvalue=None):
        self.text = text
        self.initialvalue = initialvalue
        super().__init__(parent, title=title)

    def body(self, master):
        tk.Label(master, text=self.text).grid(row=0, sticky="w")
        self.entry = tk.Entry(master, width=60)
        self.entry.grid(row=1, padx=5, pady=5)
        self.entry.insert(0, self.initialvalue)
        return self.entry

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text="取消", command=self.cancel).pack(side="right", padx=5, pady=5)
        tk.Button(box, text="确定", command=self.ok, default="active").pack(side="right", padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def apply(self):
        self.result = self.entry.get()


root = tk.Tk()
root.title("终端命令编辑器")
app = App(master=root)

app.mainloop()

# Windows 的小任务栏
import json
import os
import subprocess
import threading
import tkinter as tk
import webbrowser  # 添加此行
import winreg
from tkinter import messagebox  # 确保导入了Toplevel

import pystray
from PIL import Image

from update import VersionChecker


def center_window(window, window_width, window_height, icon_path="data/zhou.png"):
    # 居中创建tk 窗口
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # 设置窗口图标
    try:
        icon = tk.PhotoImage(file=icon_path)
        window.iconphoto(False, icon)
    except tk.TclError:
        print("图标文件加载失败，确保路径正确且文件存在。")

class Taskbar():
    def __init__(self,server_lujin,app_name,app_file,ipv4_ip,port):
        self.server_lujin = server_lujin
        self.app_name = app_name
        self.app_file = app_file
        self.ipv4_ip = ipv4_ip
        self.port = port

    #初始化
    def chushihua(self):
        global app_name_taskbar,server_lujin_taskbar,app_file_taskbar
        app_name_taskbar = self.app_name
        server_lujin_taskbar = self.server_lujin
        app_file_taskbar = self.app_file

        #固定菜单选项
        app_open_custom_menu = pystray.MenuItem(f"自定义命令菜单", lambda item: Taskbar.app_open_customeditor_menu(server_lujin_taskbar))
        open_catalogue_menu = pystray.MenuItem("打开目录", lambda item: Taskbar.open_current_directory(self.server_lujin))
        command_exit_menu = pystray.MenuItem("退出", lambda item: Taskbar.command_exit_menu())

        #动态菜单选项
        # 当前设备
        name_menu = pystray.MenuItem(f"当前设备：{Taskbar.shebei_name(self.server_lujin)}", lambda item: Taskbar.shebei_name_xiugai(app_name_taskbar, server_lujin_taskbar,app_file_taskbar))  
        # 开机启动
        command_bootup_menu = pystray.MenuItem(Taskbar.command_bootup_menu_name(self.app_name), lambda item: Taskbar.command_bootup_menu_startup_shifouqidong(app_name_taskbar,server_lujin_taskbar,app_file_taskbar))
        # 亮度控制
        command_AudioBrightnes_menu = pystray.MenuItem(Taskbar.command_AudioBrightnes_menu_name(self.app_name,self.server_lujin), lambda item: Taskbar.command_AudioBrightnes_menu_startup_shifouqidong(app_name_taskbar,server_lujin_taskbar,app_file_taskbar))
        # 仅授权设备
        command_Devices_menu = pystray.MenuItem(Taskbar.command_devices_menu_name(self.app_name,self.server_lujin), lambda item: Taskbar.command_devices_menu_startup_shifouqidong(app_name_taskbar,server_lujin_taskbar,app_file_taskbar))
        # 添加检查更新菜单项
        check_update_menu = pystray.MenuItem(f"检查更新(v{VersionChecker().CURRENT_VERSION})", lambda item: threading.Thread(target=Taskbar.check_for_updates).start())

        menu = (
            name_menu,
            app_open_custom_menu,
            command_Devices_menu,
            command_AudioBrightnes_menu,
            command_bootup_menu,
            open_catalogue_menu,
            pystray.Menu.SEPARATOR,  # 添加分隔符
            check_update_menu,  # 添加此行
            command_exit_menu,
        )
        #声明 global serve_windows_mix_icon 是全局变量
        image = Image.open(f"{self.server_lujin}/data/zhou.png")
        global serve_windows_mix_icon
        serve_windows_mix_icon = pystray.Icon("name", image, f"终端服务\n地址：{self.ipv4_ip}\n已激活服务，端口：{self.port}/{self.port+1}", menu)
        serve_windows_mix_icon.run()

    @staticmethod
    def check_for_updates():
        from update import VersionChecker
        checker = VersionChecker()
        if not checker.check_for_updates():
            Taskbar.show_update_links()
        else:
            window = tk.Tk()
            window.title("版本检查")
            window_width = 240
            window_height = 40
            center_window(window, window_width, window_height)
            label = tk.Label(window, text="当前已是最新版本")
            label.pack(pady=10)
            window.mainloop()

    def show_update_links():
        def open_github():
            webbrowser.open("https://github.com/lanzeweie/HanHan_terminal/releases")

        def open_gitee():
            webbrowser.open("https://gitee.com/buxiangqumingzi/han-han_terminal/releases")

        def open_lanzou():
            webbrowser.open("https://wwpp.lanzouv.com/b0foy1bkb")

        window = tk.Tk()
        window.title("版本检查")
        window_width = 400
        window_height = 200
        center_window(window, window_width, window_height)
        label = tk.Label(window, text="发现新版本，请选择下载链接：")
        label.pack(pady=10)
        button_style = {"font": ("Helvetica", 12), "bg": "#007AFF", "fg": "white", "relief": "flat", "bd": 0}
        button_github = tk.Button(window, text="GitHub", command=open_github, **button_style)
        button_github.pack(pady=5)
        button_gitee = tk.Button(window, text="Gitee", command=open_gitee, **button_style)
        button_gitee.pack(pady=5)
        button_lanzou = tk.Button(window, text="蓝奏云", command=open_lanzou, **button_style)
        button_lanzou.pack(pady=5)
        window.mainloop()

    #更新小任务图标的文字信息
    def icon_dongtai(self,ipv4_ip,port):
        serve_windows_mix_icon.title = f"终端服务\n地址：{ipv4_ip}\n已激活服务，端口：{port}/{port+1}"

    #刷新菜单选项 如果有菜单选项某值需要修改字 则启动此函数，菜单动态字符必须使用外部函数形式 lambad匿名函数必须使用固定变量不能使用 self
    def meun_dongtai(app_name, server_lujin,app_file):
        app_open_custom_menu = pystray.MenuItem(f"自定义命令菜单", lambda item: Taskbar.app_open_customeditor_menu(server_lujin))
        open_catalogue_menu = pystray.MenuItem("打开目录", lambda item: Taskbar.open_current_directory(server_lujin))
        command_exit_menu = pystray.MenuItem("退出", lambda item: Taskbar.command_exit_menu())
        name_menu = pystray.MenuItem(f"当前设备：{Taskbar.shebei_name(server_lujin)}", lambda item: Taskbar.shebei_name_xiugai(app_name, server_lujin,app_file))  
        command_bootup_menu = pystray.MenuItem(Taskbar.command_bootup_menu_name(app_name), lambda item: Taskbar.command_bootup_menu_startup_shifouqidong(app_name, server_lujin, app_file),)
        command_AudioBrightnes_menu = pystray.MenuItem(Taskbar.command_AudioBrightnes_menu_name(app_name,server_lujin), lambda item: Taskbar.command_AudioBrightnes_menu_startup_shifouqidong(app_name, server_lujin, app_file),)
        command_Devices_menu = pystray.MenuItem(Taskbar.command_devices_menu_name(app_name,server_lujin), lambda item: Taskbar.command_devices_menu_startup_shifouqidong(app_name_taskbar,server_lujin_taskbar,app_file_taskbar))
        menu = (
            name_menu,
            app_open_custom_menu,
            command_Devices_menu,
            command_AudioBrightnes_menu,
            command_bootup_menu,
            open_catalogue_menu,
            command_exit_menu,
        )
        serve_windows_mix_icon.menu = menu

    ##--------------------------------------------基础功能-------------------------------------------------------------

    def app_open_customeditor_menu(server_lujin):
        if not os.path.exists(f"{server_lujin}/Custom_command_editor.exe"):
            if not os.path.exists(f"{server_lujin}/app/Custom_command_editor.exe"):
                messagebox.showinfo("终端命令编辑器", "应用程序不存在，请勿删除自带文件")
                return "not"
            else:
                Custom_command_editor_start = subprocess.Popen(f'{server_lujin}/app/Custom_command_editor.exe', shell=True)
        else:
            Custom_command_editor_start = subprocess.Popen(f'{server_lujin}/Custom_command_editor.exe', shell=True)

    def open_current_directory(server_lujin):
        current_directory = server_lujin
        os.startfile(current_directory)

    #退出程序
    def command_exit_menu():
        serve_windows_mix_icon.stop()
        os._exit(0)

    #--------------------------------------------获得设备名字与修改设备名-------------------------------------------------------------
    def shebei_name(server_lujin):
        with open(fr'{server_lujin}/data/orderlist.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        title = data[0]['title']
        return title
    
    def shebei_name_xiugai(app_name, server_lujin, app_file):
        def create_window():
            def get_input():
                user_input = entry.get()
                if user_input.strip() == "":
                    messagebox.showinfo("涵涵的控制终端", "不能输入空值")
                else:
                    with open(f'{server_lujin}/data/orderlist.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data[0]['title'] = f"{user_input}"
                    with open(f'{server_lujin}/data/orderlist.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    messagebox.showinfo("涵涵的控制终端", "设备名已修改成功！")
                    window.destroy()
                    Taskbar.meun_dongtai(app_name, server_lujin, app_file)  # 这里调用
            window = tk.Tk()
            window.title("涵涵的控制终端")
            window_width, window_height = 260, 120
            center_window(window, window_width, window_height)
            label = tk.Label(window, text="请输入新的设备名：")
            label.pack(pady=10)
            entry = tk.Entry(window)
            entry.pack(pady=10)
            entry.focus_set()
            button = tk.Button(window, text="确定", command=get_input)
            button.pack(pady=10)
            window.mainloop()
    
        thread = threading.Thread(target=create_window)
        thread.start()

    #--------------------------------------------设置开机启动-------------------------------------------------------------
    def command_bootup_menu_name(app_name):
        startup_wenbenzhi = Taskbar.command_bootup_menu_check_startup(app_name)
        if startup_wenbenzhi == "surr":
            startup_wenbenzhi_wenben = "开机启动 【√】"
        elif startup_wenbenzhi == "null":
            startup_wenbenzhi_wenben = "开机启动 【X】"
        return startup_wenbenzhi_wenben
    
    def command_bootup_menu_check_startup(app_name):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(reg_key, app_name)
            print(f"应用程序 {app_name} 已添加到启动项中")
            return "surr"
        except FileNotFoundError:
            print(f"应用程序 {app_name} 未添加到启动项中")
        winreg.CloseKey(reg_key)
        return "null"
    
    #更新小任务栏程序的右键菜单
    def command_bootup_menu_startup_shifouqidong(app_name, server_lujin,app_file):
        if Taskbar.command_bootup_menu_check_startup(app_name) == "surr":
            Taskbar.command_bootup_menu_remove_from_startup(app_name)
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)
        elif Taskbar.command_bootup_menu_check_startup(app_name) == "null":
            Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}{os.sep}{app_file}")
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)


    #删除
    def command_bootup_menu_remove_from_startup(app_name):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(reg_key, app_name)
            print("已删除开机自启")
        except FileNotFoundError:
            print(f"启动项中不存在应用程序: {app_name}")
        winreg.CloseKey(reg_key)
    #新增
    def command_bootup_menu_add_to_startup(app_name, app_path):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(reg_key)
    #---------------------------------------------------------------------------------------------------------
        
    #屏幕亮度
    def command_AudioBrightnes_menu_name(app_name,server_lujin):
        startup_wenbenzhi = Taskbar.command_AudioBrightnes_menu_check_startup(app_name,server_lujin)
        if startup_wenbenzhi == "surr":
            startup_wenbenzhi_wenben = "亮度控制 【√】"
        elif startup_wenbenzhi == "null":
            startup_wenbenzhi_wenben = "亮度控制 【X】"
        return startup_wenbenzhi_wenben
    
    def command_AudioBrightnes_menu_check_startup(app_name,server_lujin):
        with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        for item in data:
            if item['title'] == "亮度控制":
                return "surr"
        return "null"

    #更新小任务栏程序的右键菜单
    def command_AudioBrightnes_menu_startup_shifouqidong(app_name, server_lujin,app_file):
        if Taskbar.command_AudioBrightnes_menu_check_startup(app_name,server_lujin) == "surr":
            Taskbar.command_AudioBrightnes_menu_remove_from_startup(app_name,server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)
        elif Taskbar.command_AudioBrightnes_menu_check_startup(app_name,server_lujin) == "null":
            Taskbar.command_AudioBrightnes_menu_add_to_startup(server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)

    def command_AudioBrightnes_menu_remove_from_startup(app_name, server_lujin):
        with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        item_to_remove = None
        for item in data:
            if item['title'] == '亮度控制':
                item_to_remove = item
                break
        if item_to_remove:
            data.remove(item_to_remove)
        with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
                

    def command_AudioBrightnes_menu_add_to_startup(server_lujin):
        new_item = {
            "title": "亮度控制",
            "apiUrl": "http://192.168.1.6:5202/command",
            "guding": "n",
            "datacommand": "nircmd.exe setbrightness {value}",
            "value": 50
        }
        
        with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        found_audio_control = False
        for index, item in enumerate(data):
            if item['title'] == '音量控制':
                data.insert(index + 1, new_item)
                found_audio_control = True
                break
        
        if not found_audio_control:
            data.append(new_item)
        
        with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    #-陌生设备接入-----------------------------------------------------------------------------------------------
    # 加载设备配置文件width
    def show_custom_alert(model_id, device_id, command, result_queue):
        def on_trust():
            result_queue.put("trust")
            root.destroy()

        def on_allow_once():
            result_queue.put("allow_once")
            root.destroy()

        def on_reject():
            result_queue.put("reject")
            root.destroy()

        def on_blacklist():
            result_queue.put("blacklist")
            root.destroy()

        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        alert_window = tk.Toplevel(root)
        alert_window.title("陌生设备发起请求")
        alert_window.attributes("-topmost", True)
        # 设置窗口图标
        try:
            icon = tk.PhotoImage(file="data/zhou.png")
            alert_window.iconphoto(False, icon)
        except tk.TclError:
            print("图标文件加载失败，确保路径正确且文件存在。")
            
        window_width = 335
        window_height = 200
        center_window(alert_window, window_width, window_height)
        if command == None:
            command = "发起获得远程使用命令授权请求"
        label_info = tk.Label(alert_window, text=f"设备型号: {model_id}\n设备ID: {device_id}\n请求命令: {command}",
                            font=("Helvetica", 13), pady=10)
        label_info.pack()

        button_frame = tk.Frame(alert_window)
        button_frame.pack(pady=20)
        button_style = {"font": ("Helvetica", 12), "bg": "#007AFF", "fg": "white", "relief": "flat", "bd": 0}

        def create_button(text, command):
            width = max(12, min(24, len(text) + 4))
            return tk.Button(button_frame, text=text, command=command, width=width, **button_style)

        button_trust = create_button("信任", on_trust)
        button_trust.grid(row=0, column=0, padx=5, pady=5)
        button_allow_once = create_button("同意一次", on_allow_once)
        button_allow_once.grid(row=0, column=1, padx=5, pady=5)
        button_reject = create_button("拒绝", on_reject)
        button_reject.grid(row=1, column=0, padx=5, pady=5)
        button_blacklist = create_button("加入黑名单", on_blacklist)
        button_blacklist.grid(row=1, column=1, padx=5, pady=5)

        def on_close():
            result_queue.put("reject")  # 默认返回拒绝
            root.destroy()

        alert_window.protocol("WM_DELETE_WINDOW", on_close)
        root.mainloop()
    #---------------------------------------------------------------------------------------------------------
    #--------------------------------------------设置设备来源-------------------------------------------------------------
    def command_devices_menu_name(app_name,server_lujin):
        startup_wenbenzhi = Taskbar.command_devices_menu_check_startup(app_name,server_lujin)
        if startup_wenbenzhi == "surr":
            startup_wenbenzhi_wenben = "仅授权设备 【√】"
        elif startup_wenbenzhi == "null":
            startup_wenbenzhi_wenben = "仅授权设备 【X】"
        return startup_wenbenzhi_wenben
    
    def command_devices_menu_check_startup(app_name,server_lujin):
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        if data['enable'] == "true":
            return "surr"
        return "null"

    #更新小任务栏程序的右键菜单
    def command_devices_menu_startup_shifouqidong(app_name, server_lujin,app_file):
        if Taskbar.command_devices_menu_check_startup(app_name,server_lujin) == "surr":
            Taskbar.command_devices_menu_remove_from_startup(app_name,server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)
        elif Taskbar.command_devices_menu_check_startup(app_name,server_lujin) == "null":
            Taskbar.command_devices_menu_add_to_startup(server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin,app_file)

    def command_devices_menu_remove_from_startup(app_name, server_lujin):
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['enable'] = "false"
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
                

    def command_devices_menu_add_to_startup(server_lujin):
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['enable'] = "true"
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

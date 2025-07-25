# Windows 的小任务栏
import asyncio
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
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls._instance
    def __init__(self, server_lujin, app_name, app_file, ipv4_ip, port):
        if not hasattr(self, '_initialized'):  # 防止重复初始化
            self.server_lujin = server_lujin
            self.app_name = app_name
            self.app_file = app_file
            self.ipv4_ip = ipv4_ip
            self.port = port
            self.serve_windows_mix_icon = None  # 实例变量
            self._initialized = True

    #初始化
    def chushihua(self):
        global app_name_taskbar,server_lujin_taskbar,app_file_taskbar
        app_name_taskbar = self.app_name
        server_lujin_taskbar = self.server_lujin
        app_file_taskbar = self.app_file

        #固定菜单选项
        app_open_custom_menu = pystray.MenuItem(f"自定义命令菜单编辑器", lambda item: Taskbar.app_open_customeditor_menu(server_lujin_taskbar))
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
        # 仅执行列表命令
        command_OrderlistAuth_menu = pystray.MenuItem(Taskbar.command_orderlist_auth_menu_name(self.app_name,self.server_lujin), lambda item: Taskbar.command_orderlist_auth_startup_shifouqidong(app_name_taskbar,server_lujin_taskbar,app_file_taskbar))
        # 添加检查更新菜单项
        check_update_menu = pystray.MenuItem(f"检查更新(v{VersionChecker().CURRENT_VERSION})", lambda item: threading.Thread(target=Taskbar.check_for_updates).start())

        menu = (
            name_menu,
            app_open_custom_menu,
            pystray.Menu.SEPARATOR,  # 添加安全选项分隔符
            command_Devices_menu,
            command_OrderlistAuth_menu,
            pystray.Menu.SEPARATOR,  # 添加分隔符
            command_AudioBrightnes_menu,
            command_bootup_menu,
            open_catalogue_menu,
            pystray.Menu.SEPARATOR,  # 添加分隔符
            check_update_menu,  # 添加此行
            command_exit_menu,
        )
        #声明 global serve_windows_mix_icon 是全局变量
        image = Image.open(f"{self.server_lujin}/data/zhou.png")
        self.serve_windows_mix_icon = pystray.Icon("name", image, 
            f"终端服务\n地址：{self.ipv4_ip}\n已激活服务，端口：{self.port}/{self.port+1}", 
            menu)
        self.serve_windows_mix_icon.run()

    async def chushihua_async(self, loop):
        """异步版本的初始化方法"""
        try:
            # 使用run_in_executor将阻塞式方法转为异步方法
            # 第一个参数是执行器(None表示使用默认的ThreadPoolExecutor)
            await loop.run_in_executor(None, self.chushihua)
        except Exception as e:
            print(f"任务栏异步初始化异常: {str(e)}")
        
        # 保持事件循环运行，处理未来可能的异步任务
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次，保持循环运行

    @staticmethod
    # 版本更新，调用 update
    def check_for_updates():
        def run_check():
            from update import VersionChecker
            checker = VersionChecker()
            checker.check_for_updates()
        
        thread = threading.Thread(target=run_check)
        thread.start()
        
    @staticmethod
    def show_custom_alert(model_id, device_id, command, result_queue):
        def show_alert_window():
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
            
        thread = threading.Thread(target=show_alert_window)
        thread.start()

    #更新小任务图标的文字信息
    def icon_dongtai(self, ipv4_ip, port):
        # 添加空值检查和异常处理
        if self.serve_windows_mix_icon:
            try:
                self.serve_windows_mix_icon.title = f"终端服务\n地址：{ipv4_ip}\n已激活服务，端口：{port}/{port+1}"
            except AttributeError:
                print("任务栏图标尚未初始化完成")
        else:
            print("任务栏图标实例不存在")

    #刷新菜单选项 如果有菜单选项某值需要修改字 则启动此函数，菜单动态字符必须使用外部函数形式 lambad匿名函数必须使用固定变量不能使用 self
    @classmethod  # 修改为类方法
    def meun_dongtai(cls, app_name, server_lujin, app_file):  # 添加cls参数
        # 动态菜单选项（原有代码保持不动）
        name_menu = pystray.MenuItem(f"当前设备：{Taskbar.shebei_name(server_lujin)}", lambda item: Taskbar.shebei_name_xiugai(app_name, server_lujin, app_file))  
        command_bootup_menu = pystray.MenuItem(Taskbar.command_bootup_menu_name(app_name), lambda item: Taskbar.command_bootup_menu_startup_shifouqidong(app_name, server_lujin, app_file))
        command_AudioBrightnes_menu = pystray.MenuItem(Taskbar.command_AudioBrightnes_menu_name(app_name,server_lujin), lambda item: Taskbar.command_AudioBrightnes_menu_startup_shifouqidong(app_name, server_lujin, app_file))
        command_Devices_menu = pystray.MenuItem(Taskbar.command_devices_menu_name(app_name,server_lujin), lambda item: Taskbar.command_devices_menu_startup_shifouqidong(app_name, server_lujin, app_file))
        command_OrderlistAuth_menu = pystray.MenuItem(Taskbar.command_orderlist_auth_menu_name(app_name,server_lujin), lambda item: Taskbar.command_orderlist_auth_startup_shifouqidong(app_name, server_lujin, app_file))
        
        # 更新菜单结构，添加分隔符和新选项
        menu = (
            name_menu,
            pystray.MenuItem(f"自定义命令菜单", lambda item: Taskbar.app_open_customeditor_menu(server_lujin)),
            pystray.Menu.SEPARATOR,  # 添加安全选项分隔符
            command_Devices_menu,
            command_OrderlistAuth_menu,
            pystray.Menu.SEPARATOR,  # 添加分隔符
            command_AudioBrightnes_menu,
            command_bootup_menu,
            pystray.MenuItem("打开目录", lambda item: Taskbar.open_current_directory(server_lujin)),
            pystray.Menu.SEPARATOR,  # 添加分隔符
            pystray.MenuItem("退出", lambda item: Taskbar.command_exit_menu()),
        )

        # 通过单例实例访问
        instance = cls.get_instance()  # 新增此行
        if instance and instance.serve_windows_mix_icon:  # 添加安全校验
            instance.serve_windows_mix_icon.menu = menu

    ##--------------------------------------------基础功能-------------------------------------------------------------

    def app_open_customeditor_menu(server_lujin):
        def run_editor():
            try:
                # 首先检查exe文件是否存在
                if os.path.exists(f"{server_lujin}/Custom_command_editor.exe"):
                    subprocess.Popen(f'{server_lujin}/Custom_command_editor.exe', shell=True)
                    return
                elif os.path.exists(f"{server_lujin}/app/Custom_command_editor.exe"):
                    subprocess.Popen(f'{server_lujin}/app/Custom_command_editor.exe', shell=True)
                    return
                
                # 检查模块文件是否存在
                module_path = os.path.join(server_lujin, "app", "Custom_command_editor.py")
                
                # 检查py文件
                if not os.path.exists(module_path):
                    # 兼容旧版本，检查根目录下的py文件
                    module_path = os.path.join(server_lujin, "Custom_command_editor.py")
                    
                    # 如果py文件不存在
                    if not os.path.exists(module_path):
                        # 在主线程中显示消息
                        tk.messagebox.showinfo("终端命令编辑器", "自定义命令编辑器模块不存在，请勿删除自带文件")
                        return "not"
            
                # 动态导入并运行py模块
                import importlib.util
                import sys

                # 将模块所在目录添加到sys.path
                module_dir = os.path.dirname(module_path)
                if module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
            
                # 动态加载模块
                spec = importlib.util.spec_from_file_location("custom_command_editor", module_path)
                if spec is None:
                    tk.messagebox.showinfo("终端命令编辑器", "无法加载自定义命令编辑器模块")
                    return "not"
            
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            
                # 运行主函数
                if hasattr(module, 'main'):
                    module.main()
                else:
                    tk.messagebox.showinfo("终端命令编辑器", "自定义命令编辑器模块格式错误")
                
            except Exception as e:
                # 在主线程中安全地显示错误消息
                def show_error():
                    tk.messagebox.showinfo("终端命令编辑器", f"启动自定义命令编辑器时发生错误：{str(e)}")
                if threading.current_thread() is threading.main_thread():
                    show_error()
                else:
                    # 如果在子线程中，将消息框操作调度到主线程
                    try:
                        root = tk.Tk()
                        root.withdraw()
                        root.after(0, lambda: [show_error(), root.destroy()])
                        root.mainloop()
                    except:
                        print(f"启动自定义命令编辑器时发生错误：{str(e)}")
        
        thread = threading.Thread(target=run_editor)
        thread.daemon = True  # 设置为守护线程，这样主程序退出时线程也会退出
        thread.start()

    def open_current_directory(server_lujin):
        current_directory = server_lujin
        os.startfile(current_directory)

    #退出程序
    @classmethod
    def command_exit_menu(cls):
        # 通过单例实例访问图标
        instance = cls.get_instance()
        if instance and instance.serve_windows_mix_icon:
            instance.serve_windows_mix_icon.stop()
        os._exit(0)

    #--------------------------------------------获得设备名字与修改设备名-------------------------------------------------------------
    def shebei_name(server_lujin):
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        id_path = os.path.join(config_dir, 'id.json')
        with open(id_path, 'r', encoding='utf-8') as f:
            id_data = json.load(f)
        title = id_data['name']
        return title
    
    def shebei_name_xiugai(app_name, server_lujin, app_file):
        def create_window():
            def get_input():
                user_input = entry.get()
                if user_input.strip() == "":
                    messagebox.showinfo("涵涵的控制终端", "不能输入空值")
                else:
                    from WinDC import init_config_directory
                    config_dir = init_config_directory()
                    
                    # 修改 orderlist.json
                    orderlist_path = os.path.join(config_dir, 'orderlist.json')
                    with open(orderlist_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # 添加 try 是为了让 orderlist 中显示设备名 可以不存在 因为新版本添加了 id.json 专门用来储存设备名  用户可以选择去除 orderlist 当然，默认是存在的
                    try:
                        if data[0]['//1'] == '以上是标题,可以在任务栏中修改':
                            data[0]['title'] = f"{user_input}"
                            with open(orderlist_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                    except:
                        pass
                    # 修改 id.json
                    id_path = os.path.join(config_dir, 'id.json')
                    with open(id_path, 'r', encoding='utf-8') as id_file:
                        id_data = json.load(id_file)
                    id_data['name'] = user_input  # 更新name字段
                    with open(id_path, 'w', encoding='utf-8') as id_file:
                        json.dump(id_data, id_file, indent=2, ensure_ascii=False)
                    
                    messagebox.showinfo("涵涵的控制终端", "设备名已修改成功！")
                    window.destroy()
                    Taskbar.meun_dongtai(app_name, server_lujin, app_file)

            window = tk.Tk()
            window.title("修改设备名称")
            window_width, window_height = 320, 180
            center_window(window, window_width, window_height)
            
            # 创建一个主框架来容纳所有控件
            main_frame = tk.Frame(window, padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 标题标签
            title_label = tk.Label(main_frame, text="设置新的设备名称", font=("Helvetica", 14, "bold"))
            title_label.pack(pady=(0, 15))
            
            # 创建输入框
            entry_frame = tk.Frame(main_frame)
            entry_frame.pack(fill=tk.X, pady=5)
            
            entry = tk.Entry(entry_frame, font=("Helvetica", 12), bd=2, relief=tk.GROOVE)
            entry.pack(fill=tk.X, ipady=5)
            entry.focus_set()
            
            # 获取当前设备名以预填充输入框
            try:
                from WinDC import init_config_directory
                config_dir = init_config_directory()
                id_path = os.path.join(config_dir, 'id.json')
                with open(id_path, 'r', encoding='utf-8') as id_file:
                    id_data = json.load(id_file)
                    current_name = id_data.get('name', '')
                    if current_name:
                        entry.insert(0, current_name)
                        # 全选文本以便用户可以直接输入覆盖
                        entry.select_range(0, tk.END)
            except:
                pass
            
            # 创建按钮框架
            button_frame = tk.Frame(main_frame)
            button_frame.pack(pady=15)
            
            # 美化按钮样式
            button_style = {
                "font": ("Helvetica", 12),
                "bg": "#007AFF",
                "fg": "white",
                "relief": tk.FLAT,
                "bd": 0,
                "padx": 15,
                "pady": 5,
                "cursor": "hand2"  # 鼠标悬停时显示手型光标
            }
            
            # 确认按钮
            confirm_button = tk.Button(button_frame, text="确定", command=get_input, **button_style)
            confirm_button.pack(side=tk.LEFT, padx=5)
            
            # 取消按钮
            cancel_button = tk.Button(button_frame, text="取消", command=window.destroy,
                                      bg="#E0E0E0", fg="#333333", font=("Helvetica", 12),
                                      relief=tk.FLAT, bd=0, padx=15, pady=5, cursor="hand2")
            cancel_button.pack(side=tk.LEFT, padx=5)
            
            # 绑定回车键进行提交
            window.bind("<Return>", lambda event: get_input())
            
            # 绑定Esc键关闭窗口
            window.bind("<Escape>", lambda event: window.destroy())
            
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
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        file_path = os.path.join(config_dir, 'orderlist.json')
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return "null"
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    if item['title'] == "亮度控制":
                        return "surr"
                return "null"
        except json.JSONDecodeError as e:
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
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        orderlist_path = os.path.join(config_dir, 'orderlist.json')
        with open(orderlist_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        item_to_remove = None
        for item in data:
            if item['title'] == '亮度控制':
                item_to_remove = item
                break
        if item_to_remove:
            data.remove(item_to_remove)
        with open(orderlist_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
                

    def command_AudioBrightnes_menu_add_to_startup(server_lujin):
        def check_and_add_brightness_control():
            # 检查屏幕是否支持亮度控制
            try:
                # 避免循环导入，在函数内部导入
                from WinDC import (BRIGHTNESS_AVAILABLE, PPowerShell,
                                   init_config_directory)

                # 首先检查必要的库是否已安装
                if not BRIGHTNESS_AVAILABLE:
                    messagebox.showinfo("亮度控制", "无法添加亮度控制：缺少所需的库支持。\n请确保已安装 screen_brightness_control 和 wmi 库。")
                    return
                # 检查亮度控制支持，但不实际改变亮度
                try:
                    import screen_brightness_control as sbc

                    # 只获取当前亮度而不设置值
                    current_brightness = sbc.get_brightness()
                    if isinstance(current_brightness, list) and not current_brightness:
                        messagebox.showinfo("亮度控制", "当前屏幕不支持亮度调节功能。")
                        return
                except Exception as e:
                    error_msg = str(e).lower()
                    if "unsupported" in error_msg or "not supported" in error_msg or "error" in error_msg:
                        messagebox.showinfo("亮度控制", f"当前屏幕不支持亮度调节功能。\n错误信息：{str(e)}")
                        return
            except Exception as e:
                # 处理可能的导入或其他错误
                messagebox.showinfo("亮度控制", f"无法检查亮度控制支持: {str(e)}")
                return
            
            # 屏幕支持亮度控制，添加功能
            try:
                config_dir = init_config_directory()
                orderlist_path = os.path.join(config_dir, 'orderlist.json')
                
                # 先检查是否已存在亮度控制命令
                with open(orderlist_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # 检查是否已存在亮度控制
                for item in data:
                    if item['title'] == '亮度控制':
                        # 已存在，不需要添加
                        return
                
                # 不存在，添加新项目
                new_item = {
                    "title": "亮度控制",
                    "apiUrl": "http://*hanhanip*:5202/command",
                    "guding": "n",
                    "datacommand": "setbrightness {value}",
                    "value": 50
                }
                
                found_audio_control = False
                for index, item in enumerate(data):
                    if item['title'] == '音量控制':
                        data.insert(index + 1, new_item)
                        found_audio_control = True
                        break
                
                if not found_audio_control:
                    data.append(new_item)
                
                with open(orderlist_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                    
                # 添加成功后更新菜单状态并显示消息
                # 获取全局变量
                global app_name_taskbar, app_file_taskbar
                
                def update_menu():
                    try:
                        # 在主线程中执行更新
                        Taskbar.meun_dongtai(app_name_taskbar, server_lujin, app_file_taskbar)
                        # 显示成功消息
                        #messagebox.showinfo("亮度控制", "亮度控制功能已成功添加！")
                    except Exception as e:
                        print(f"更新菜单时出错: {str(e)}")
                
                # 在主线程中执行UI更新
                threading.Thread(target=update_menu).start()
                    
            except Exception as e:
                messagebox.showinfo("亮度控制", f"添加亮度控制时出错: {str(e)}")
        
        # 使用线程运行检查和添加亮度控制的函数，防止UI卡死
        thread = threading.Thread(target=check_and_add_brightness_control)
        thread.start()

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
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        with open(devices_path, 'r', encoding='utf-8') as file:
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
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        with open(devices_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['enable'] = "false"
        with open(devices_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
                

    def command_devices_menu_add_to_startup(server_lujin):
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        with open(devices_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['enable'] = "true"
        with open(devices_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    #--------------------------------------------仅执行列表命令-------------------------------------------------------------
    def command_orderlist_auth_menu_name(app_name,server_lujin):
        startup_wenbenzhi = Taskbar.command_orderlist_auth_check_startup(app_name,server_lujin)
        if startup_wenbenzhi == "surr":
            startup_wenbenzhi_wenben = "仅执行列表命令 【√】"
        elif startup_wenbenzhi == "null":
            startup_wenbenzhi_wenben = "仅执行列表命令 【X】"
        return startup_wenbenzhi_wenben
    
    def command_orderlist_auth_check_startup(app_name,server_lujin):
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        try:
            with open(devices_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get('enable_orderlist_shouquan') == "true":
                    return "surr"
                return "null"
        except Exception as e:
            print(f"读取配置时出错: {str(e)}")
            return "null"

    #更新小任务栏程序的右键菜单
    def command_orderlist_auth_startup_shifouqidong(app_name, server_lujin, app_file):
        if Taskbar.command_orderlist_auth_check_startup(app_name, server_lujin) == "surr":
            Taskbar.command_orderlist_auth_remove_from_startup(app_name, server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin, app_file)
        elif Taskbar.command_orderlist_auth_check_startup(app_name, server_lujin) == "null":
            Taskbar.command_orderlist_auth_add_to_startup(server_lujin)
            Taskbar.meun_dongtai(app_name, server_lujin, app_file)

    def command_orderlist_auth_remove_from_startup(app_name, server_lujin):
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        try:
            with open(devices_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['enable_orderlist_shouquan'] = "false"
            with open(devices_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新配置时出错: {str(e)}")
            messagebox.showinfo("配置更新", f"更新配置时出错: {str(e)}")

    def command_orderlist_auth_add_to_startup(server_lujin):
        from WinDC import init_config_directory
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        try:
            with open(devices_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['enable_orderlist_shouquan'] = "true"
            with open(devices_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新配置时出错: {str(e)}")
            messagebox.showinfo("配置更新", f"更新配置时出错: {str(e)}")
        devices_path = os.path.join(config_dir, 'Devices.json')
        try:
            with open(devices_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            data['enable_orderlist_shouquan'] = "true"
            with open(devices_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"更新配置时出错: {str(e)}")
            messagebox.showinfo("配置更新", f"更新配置时出错: {str(e)}")

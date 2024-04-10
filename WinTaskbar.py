# Windows 的小任务栏
import pystray,json,winreg,os
from PIL import Image  
from tkinter import messagebox  
import tkinter as tk
import subprocess

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

        menu = (
            name_menu,
            app_open_custom_menu,
            command_AudioBrightnes_menu,
            command_bootup_menu,
            open_catalogue_menu,
            command_exit_menu,
        )
        #声明 global serve_windows_mix_icon 是全局变量
        image = Image.open(f"{self.server_lujin}/data/zhou.png")
        global serve_windows_mix_icon
        serve_windows_mix_icon = pystray.Icon("name", image, f"终端服务\n地址：{self.ipv4_ip}\n已激活服务，端口：{self.port}/{self.port+1}", menu)
        serve_windows_mix_icon.run()
        
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
        menu = (
            name_menu,
            app_open_custom_menu,
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
    
    def shebei_name_xiugai(app_name, server_lujin,app_file):
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

        window = tk.Tk()
        window.title("涵涵的控制终端")
        window.geometry("400x300")  # 设置窗口大小为400x300像素
        label = tk.Label(window, text="请输入新的设备名：")
        label.pack()
        entry = tk.Entry(window)
        entry.pack()
        button = tk.Button(window, text="确定", command=get_input)
        button.pack()
        window.mainloop()
        Taskbar.meun_dongtai(app_name, server_lujin,app_file)

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
            Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}\{app_file}")
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
        with open(f'{server_lujin}\\data\\orderlist.json', 'r', encoding='utf-8') as file:
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
        with open(f'{server_lujin}\\data\\orderlist.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        item_to_remove = None
        for item in data:
            if item['title'] == '亮度控制':
                item_to_remove = item
                break
        if item_to_remove:
            data.remove(item_to_remove)
        with open(f'{server_lujin}\\data\\orderlist.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
                

    def command_AudioBrightnes_menu_add_to_startup(server_lujin):
        new_item = {
            "title": "亮度控制",
            "apiUrl": "http://192.168.1.6:5202/command",
            "guding": "n",
            "datacommand": "nircmd.exe setbrightness {value}",
            "value": 50
        }
        
        with open(f'{server_lujin}\\data\\orderlist.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        found_audio_control = False
        for index, item in enumerate(data):
            if item['title'] == '音量控制':
                data.insert(index + 1, new_item)
                found_audio_control = True
                break
        
        if not found_audio_control:
            data.append(new_item)
        
        with open(f'{server_lujin}\\data\\orderlist.json', 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        

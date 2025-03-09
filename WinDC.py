#调用 Windows PowerShell
import asyncio  # 添加asyncio导入
import datetime
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk  # 添加tkinter导入
from tkinter import messagebox

from flask import jsonify, request

from WinTaskbar import Taskbar


def center_window(window, width, height):
    """将窗口居中显示"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_coordinate = (screen_width - width) // 2
    y_coordinate = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")

############################
#配置文件
config_orderlist = "data\\orderlist.json"
############################
if getattr(sys, 'frozen', False):
    server_lujin = os.path.dirname(sys.executable)
else:
    server_lujin = os.path.dirname(os.path.abspath(__file__))

class PPowerShell():
    def __init__(self):
        pass

    def file_json_Audio():
        need_update = False
        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        for item in data:
            if item['title'] == '音量控制':
                Audio_value = PPowerShell.ps1_get('AudioVolume')
                if Audio_value is not None:
                    Audio_value_True = float(Audio_value) * 100
                    item['value'] = int(Audio_value_True)
                    need_update = True
            elif item['title'] == '亮度控制':
                Audio_value = PPowerShell.ps1_get('AudioBrightnes')
                if Audio_value is not None:
                    try:
                        Audio_value_True = Audio_value
                        item['value'] = int(Audio_value_True)
                        need_update = True
                    except:
                        try:
                            Audio_value_True = Audio_value[0]
                            item['value'] = int(Audio_value_True)
                            need_update = True
                        except:
                            print("亮度值转换失败")
        
        # 只有在需要更新时才写入文件
        if need_update:
            with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print("配置文件已更新音量和亮度值")

    def file_json_geshihua(ipv4,port):
        #格式化data json数据，设置为当机地址
        #----------历史屎坑--------如果去除它则无法运行
        PPowerShell.get_ipv4_address()
        #----------历史屎坑--------如果去除它则无法运行
        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
            data = json.load(file)
        for item in data:
            if item['guding'] == 'n':
                url_parts = item['apiUrl'].split('//')
                if len(url_parts) > 1:
                    address = url_parts[1].split('/')[0]
                    formatted_address = address.replace(address, f'{ipv4}:{port+1}')
                    item['apiUrl'] = item['apiUrl'].replace(address, formatted_address)

        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print("读取了配置文件")

    def file_json_geshihua_prot(port):
         #格式化data json数据，设置为启动端口
        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
            data = json.load(file)
        for item in data:
            if item['guding'] == 'n':
                url = item['apiUrl']
                target = '*hanhanip*:'
                if target in url:
                    start_index = url.find(target) + len(target)
                    end_index = url.find('/', start_index)
                    if end_index == -1:
                        end_index = len(url)
                    new_url = url[:start_index] + f"{port+1}" + url[end_index:]
                    item['apiUrl'] = new_url
        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print("配置文件更新完成")
    def check_files_and_dirs(app_name, app_file):
        files_and_dirs = [f"{server_lujin}/data"]
        for item in files_and_dirs:  
            if os.path.exists(item):  
                pass  
            else:  
                print(f"缺失{item}")
                messagebox.showinfo("涵涵的控制终端核心", f"缺失{item}")  
                os._exit(1)  # 添加退出代码
        print("\n环境已检查：正常")
        # 是否第一次启动 设置第一次启动自行开启开机启动
        if os.path.exists(f"{server_lujin}/data/one"):
            pass
        else:
            with open(f"{server_lujin}/data/one", "w") as file:
                pass
            Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}{os.sep}{app_file}")
        print(f"{server_lujin}{os.sep}{app_file}")
        # 检查是否需要设置设备名
        with open(f"{server_lujin}/data/id.json", "r", encoding='utf-8') as file:
            data = json.load(file)

        if data.get('name', '') == '':
            # 使用单线程方式处理设备名设置
            def create_device_name_window():
                def save_device_name():
                    user_input = entry.get().strip()
                    if not user_input:
                        messagebox.showinfo("涵涵的控制终端", "设备名不能为空，请重新输入")
                        return
                    
                    try:
                        # 修改 id.json
                        with open(f'{server_lujin}/data/id.json', 'r', encoding='utf-8') as id_file:
                            id_data = json.load(id_file)
                        id_data['name'] = user_input
                        with open(f'{server_lujin}/data/id.json', 'w', encoding='utf-8') as id_file:
                            json.dump(id_data, id_file, indent=2, ensure_ascii=False)
                        
                        # 修改 orderlist.json
                        try:
                            with open(f'{server_lujin}/data/orderlist.json', 'r', encoding='utf-8') as f:
                                orderlist_data = json.load(f)
                            # 添加 try 是为了让 orderlist 中显示设备名 
                            try:
                                if orderlist_data[0]['//1'] != '以上是标题,可以在任务栏中修改':
                                    orderlist_data[0]['title'] = f"{user_input}"
                                    with open(f'{server_lujin}/data/orderlist.json', 'w', encoding='utf-8') as f:
                                        json.dump(orderlist_data, f, indent=2, ensure_ascii=False)
                            except:
                                pass
                        except Exception as e:
                            print(f"更新orderlist.json时出错: {str(e)}")
                            # 错误可以忽略，因为orderlist.json是可选的
                        
                        messagebox.showinfo("涵涵的控制终端", "设备名设置成功！")
                        window.destroy()
                        # 设置一个标志，指示已完成设置
                        window.device_name_set = True
                    except Exception as e:
                        messagebox.showerror("涵涵的控制终端", f"保存设备名时出错: {str(e)}")
                
                window = tk.Tk()
                window.title("涵涵的控制终端")
                window_width, window_height = 350, 180
                center_window(window, window_width, window_height)
                window.configure(bg="#f0f0f0")
                # 设置标志属性
                window.device_name_set = False
                # 设置窗口图标
                try:
                    icon_path = f"{server_lujin}{os.sep}data{os.sep}zhou.png"
                    if os.path.exists(icon_path):
                        icon_image = tk.PhotoImage(file=icon_path)
                        window.iconphoto(True, icon_image)
                except Exception as e:
                    print(f"设置窗口图标时出错: {str(e)}")
                # 创建一个主框架来容纳所有控件
                main_frame = tk.Frame(window, bg="#f0f0f0", padx=20, pady=20)
                main_frame.pack(fill=tk.BOTH, expand=True)
                # 欢迎文本
                welcome_label = tk.Label(
                    main_frame, 
                    text="欢迎使用小涵的软件，请为你的设备取个名字吧~",
                    font=("微软雅黑", 10),
                    wraplength=300,
                )
                welcome_label.pack(pady=(0, 15))
                # 输入框
                entry_frame = tk.Frame(main_frame, bg="#f0f0f0")
                entry_frame.pack(fill=tk.X, pady=5)
                entry = tk.Entry(entry_frame, font=("微软雅黑", 10), width=30)
                entry.pack(pady=5)
                entry.focus_set()
                # 确定按钮
                button_frame = tk.Frame(main_frame, bg="#f0f0f0")
                button_frame.pack(pady=10)
                button = tk.Button(
                    button_frame, 
                    text="确定", 
                    command=save_device_name,
                    width=10,
                    bg="#282c34",
                    fg="white",
                    relief=tk.FLAT,
                    font=("微软雅黑", 9)
                )
                button.pack(pady=5)
                # 绑定回车键
                window.bind('<Return>', lambda event: save_device_name())
                # 阻塞主线程直到窗口关闭
                window.mainloop()
                # 窗口关闭后，返回设置状态
                return window.device_name_set
            # 执行设备名设置窗口并获取结果
            device_name_set = create_device_name_window()
            # 设置完成后，再次检查设备名是否已成功设置
            try:
                with open(f"{server_lujin}/data/id.json", "r", encoding='utf-8') as file:
                    data = json.load(file)
                
                if data.get('name', '') == '':
                    print("设备名设置失败或被取消")
                    # 可以决定是否继续程序执行或退出
                    os._exit(1)  # 如果需要强制退出，可以取消此注释
                else:
                    print(f"设备名已成功设置为: {data['name']}")
                    Taskbar.meun_dongtai(app_name, server_lujin, app_file)
            except Exception as e:
                print(f"检查设备名设置状态时出错: {str(e)}")

    #--------------------------------屎坑 删除则无法运行 不知道作用-----------------------
    def get_ipv4_address():  
        ip_address = None  
        output = subprocess.check_output('ipconfig', shell=True).decode('gbk')  
        wireless_ip_address = PPowerShell.get_ip_address(output, 'Wireless LAN adapter')  
        if wireless_ip_address:  
            return wireless_ip_address  
        ethernet_ip_address = PPowerShell.get_ip_address(output, 'Ethernet adapter')  
        if ethernet_ip_address:  
            return ethernet_ip_address  
        any_ip_address = PPowerShell.get_any_ip_address(output, '192.168')  
        if any_ip_address:  
            return any_ip_address  
        any_ip_address = PPowerShell.get_any_ip_address(output)  
        return any_ip_address  
    
    def get_ip_address(output, adapter_type):  
        for line in output.split('\n'):  
            line = line.strip()  
            if line.startswith(adapter_type) or line.startswith('无线局域网适配器'):  
                interface_name = line.split(':')[1].strip()  
                if line.startswith('IPv4 Address') or line.startswith('IPv4 地址'):  
                    ip_address = line.split(':')[1].strip().split('(')[0]  
                    if ip_address.startswith('192.168'):  
                        return ip_address  
        return None  
    
    def get_any_ip_address(output, prefix=None):  
        for line in output.split('\n'):  
            line = line.strip()  
            if line.startswith('IPv4 Address') or line.startswith('IPv4 地址'):  
                ip_address = line.split(':')[1].strip().split('(')[0]  
                if not prefix or ip_address.startswith(prefix):  
                    return ip_address  
        return None
    #--------------------------------屎坑 删除则无法运行 不知道作用-----------------------

    def get_ipv4_now():
        ip_address = None
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.error:
            pass
        return ip_address

    def check_ipv4_Dynamic_state(port,Taskbar_start):
        previous_address = None
        while True:
            current_address = PPowerShell.get_ipv4_now()
            if (current_address and current_address != previous_address):
                print("IPv4 地址发生变化：", current_address)
                previous_address = current_address
                #更改json地址
                #PPowerShell.file_json_geshihua(current_address,port)
                #更改Windows小任务栏的地址
                Taskbar_start.icon_dongtai(current_address,port)
                #首先检查是否有 “音量控制、亮度控制” json配置信息，如果有则调用 Windows PowerShell 来查询数值并更新到配置文件中
            PPowerShell.file_json_Audio()
            time.sleep(60)

    @staticmethod
    async def check_ipv4_Dynamic_state_async(port, taskbar_instance, loop):
        """异步版本的IP地址变化检测函数"""
        last_ip = PPowerShell.get_ipv4_now()
        while True:
            try:
                current_ip = PPowerShell.get_ipv4_now()
                if (current_ip != last_ip):
                    print(f"IP地址已变更: {last_ip} -> {current_ip}")
                    # 更新任务栏IP地址
                    taskbar_instance.update_ip(current_ip)
                    # 调用格式化函数更新配置
                    PPowerShell.file_json_geshihua(current_ip, port)
                    last_ip = current_ip
                # 异步等待10秒
                await asyncio.sleep(10)
            except Exception as e:
                print(f"IP检测异常: {str(e)}")
                await asyncio.sleep(30)  # 出错时延长等待时间

    def ps1_get(name):
        ps_script_path = f"{server_lujin}{os.sep}app{os.sep}{name}.ps1"
        result = subprocess.run(['powershell', '-File', ps_script_path], capture_output=True, text=True, shell=True)
        stdout = result.stdout
        stderr = result.stderr
        
        if stdout is not None and stdout.strip().replace('\n\n', '\n') != '':
            if stdout is not None:
                stdout = stdout.strip().replace('\n\n', '\n')
                print("值为:"+stdout)
                return stdout
        elif stderr is not None and stderr.strip().replace('\n\n', '\n') != '':
            error_send = None
            if name == 'AudioBrightnes':
                error_send = "【控制台】系统不支持亮度"
            if name == 'AudioVolume':
                error_send = "【控制台】系统不支持声音"            
            #print(stderr)
            return None
        else:
            return None

    def verify_device(json_data, device_lock):
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        enable = config.get("enable", "false").lower() == "true"

        if not enable:
            return True

        device_id = json_data.get('deviceID')
        model_id = json_data.get('modelID')

        blacklisted_devices = config.get("blacklistedDevices", [])
        for device in blacklisted_devices:
            if device.get("deviceId") == device_id:
                response = {
                    "title": "命令返回状态",
                    "execution_time": current_time,
                    "success": False,
                    "cmd_back": "设备在黑名单中，不允许执行命令"
                }
                return jsonify(response)

        authorized_devices = config.get("authorizedDevices", [])
        authorized = any(device.get("deviceId") == device_id for device in authorized_devices)

        if not authorized:
            if not device_lock.acquire(blocking=False):
                response = {
                    "title": "命令返回状态",
                    "execution_time": current_time,
                    "success": False,
                    "cmd_back": "系统正忙，请稍后再试"
                }
                return jsonify(response)

            try:
                result_queue = queue.Queue()
                alert_thread = threading.Thread(target=Taskbar.show_custom_alert, args=(model_id, device_id, json_data.get("command"), result_queue))
                alert_thread.start()
                alert_thread.join(timeout=15)

                if alert_thread.is_alive():
                    response = {
                        "title": "命令返回状态",
                        "execution_time": current_time,
                        "success": False,
                        "cmd_back": "设备授权超时，不允许执行命令"
                    }
                    return jsonify(response)
                else:
                    choice = result_queue.get()
                    if choice == "trust":
                        authorized_devices.append({"deviceId": device_id, "deviceName": model_id})
                        config["authorizedDevices"] = authorized_devices
                        with open('data/Devices.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                    elif choice == "blacklist":
                        blacklisted_devices.append({"deviceId": device_id, "deviceName": model_id})
                        config["blacklistedDevices"] = blacklisted_devices
                        with open('data/Devices.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                        response = {
                            "title": "命令返回状态",
                            "execution_time": current_time,
                            "success": False,
                            "cmd_back": "设备已加入黑名单，不允许执行命令"
                        }
                        return jsonify(response)
                    elif choice == "reject":
                        response = {
                            "title": "命令返回状态",
                            "execution_time": current_time,
                            "success": False,
                            "cmd_back": "设备未授权，不允许执行命令"
                        }
                        return jsonify(response)
                    elif choice == "allow_once":
                        return True

                authorized_devices = config.get("authorizedDevices", [])
                authorized = any(device.get("deviceId") == device_id for device in authorized_devices)
                if authorized:
                    return True
                else:
                    response = {
                        "title": "命令返回状态",
                        "execution_time": current_time,
                        "success": False,
                        "cmd_back": "设备未授权，不允许执行命令"
                    }
                    return jsonify(response)
            finally:
                device_lock.release()
        else:
            return True

        
if __name__ == "__main__":
    print(PPowerShell.file_json_Audio())

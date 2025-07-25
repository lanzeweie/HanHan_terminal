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
import uuid  # 添加uuid导入用于获取MAC地址
from tkinter import messagebox

import psutil  # 添加psutil导入用于获取网络接口信息

# 使用新的COM保护系统
try:
    from COM.com_protection_system import (get_protection_system,
                                           safe_get_brightness,
                                           safe_get_volume,
                                           safe_set_brightness,
                                           safe_set_volume)
    COM_PROTECTION_AVAILABLE = True
    
    # 添加亮度控制可用性检查
    def _check_brightness_available():
        try:
            result = safe_get_brightness()
            return result.get("success", False)
        except Exception:
            return False
    
    # 检查亮度控制是否可用
    BRIGHTNESS_AVAILABLE = _check_brightness_available()
    print(f"亮度控制功能: {'可用' if BRIGHTNESS_AVAILABLE else '不可用'}")
except ImportError:
    COM_PROTECTION_AVAILABLE = False
    BRIGHTNESS_AVAILABLE = False
    print("警告: COM保护系统不可用，音量和亮度控制功能将受限")

from flask import jsonify, request

from WinTaskbar import Taskbar

# 全局文件锁，确保线程安全的文件操作
file_locks = {
    'orderlist.json': threading.RLock(),
    'audio_brightness_cache.json': threading.RLock(),
    'Devices.json': threading.RLock(),
    'id.json': threading.RLock()
}


def safe_json_read(file_path, filename_key, default_value=None):
    """
    线程安全的JSON文件读取
    :param file_path: 文件完整路径
    :param filename_key: 文件名作为锁的键
    :param default_value: 文件不存在时的默认值
    :return: JSON数据
    """
    lock = file_locks.get(filename_key, threading.RLock())
    with lock:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return default_value
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {str(e)}")
            return default_value

def safe_json_write(file_path, filename_key, data):
    """
    线程安全的JSON文件写入
    :param file_path: 文件完整路径
    :param filename_key: 文件名作为锁的键
    :param data: 要写入的数据
    :return: 是否成功
    """
    lock = file_locks.get(filename_key, threading.RLock())
    with lock:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"写入文件 {file_path} 失败: {str(e)}")
            return False

def center_window(window, width, height):
    """将窗口居中显示"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_coordinate = (screen_width - width) // 2
    y_coordinate = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x_coordinate}+{y_coordinate}")

def get_config_directory():
    """
    获取配置文件目录，优先使用用户文档目录，失败时使用data目录
    """
    try:
        # 尝试获取用户文档目录
        documents_path = os.path.join(os.path.expanduser("~"), "Documents")
        config_dir = os.path.join(documents_path, "HanHan_ZDserver", "data")
        
        # 尝试创建目录
        os.makedirs(config_dir, exist_ok=True)
        
        # 测试目录是否可写
        test_file = os.path.join(config_dir, "test_write.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"使用配置目录: {config_dir}")
            return config_dir
        except:
            pass
    except Exception as e:
        print(f"无法使用用户文档目录: {str(e)}")
    
    # 回退到data目录
    fallback_dir = os.path.join(server_lujin, "data")
    os.makedirs(fallback_dir, exist_ok=True)
    print(f"回退到配置目录: {fallback_dir}")
    return fallback_dir

def migrate_old_config():
    """
    迁移旧的data目录配置到新的用户文档目录
    """
    try:
        old_data_dir = os.path.join(server_lujin, "data")
        new_config_dir = get_config_directory()
        
        # 如果新目录就是data目录，不需要迁移
        if os.path.abspath(old_data_dir) == os.path.abspath(new_config_dir):
            return
        
        # 如果旧目录不存在，不需要迁移
        if not os.path.exists(old_data_dir):
            return
        
        # 迁移文件列表
        files_to_migrate = [
            "orderlist.json",
            "id.json", 
            "Devices.json",
            "audio_brightness_cache.json",
            "config.json"
        ]
        
        migrated_files = []
        for filename in files_to_migrate:
            old_file = os.path.join(old_data_dir, filename)
            new_file = os.path.join(new_config_dir, filename)
            
            # 只有当旧文件存在且新文件不存在时才迁移
            if os.path.exists(old_file) and not os.path.exists(new_file):
                try:
                    import shutil
                    shutil.copy2(old_file, new_file)
                    migrated_files.append(filename)
                except Exception as e:
                    print(f"迁移文件 {filename} 失败: {str(e)}")
        
        if migrated_files:
            print(f"已迁移配置文件: {', '.join(migrated_files)}")
    except Exception as e:
        print(f"配置迁移过程出错: {str(e)}")

############################
#配置文件
config_orderlist = "orderlist.json"
############################
if getattr(sys, 'frozen', False):
    server_lujin = os.path.dirname(sys.executable)
else:
    server_lujin = os.path.dirname(os.path.abspath(sys.argv[0]))

# 初始化配置目录
config_directory = None

def init_config_directory():
    """初始化配置目录"""
    global config_directory
    if config_directory is None:
        migrate_old_config()  # 先迁移旧配置
        config_directory = get_config_directory()
    return config_directory

class PPowerShell():
    # 添加静态变量跟踪上次更新时间
    last_volume_brightness_update = 0
    # 设置最小更新间隔(秒)
    MIN_UPDATE_INTERVAL = 5
    
    def __init__(self):
        pass

    # 添加缺失的IP地址获取方法
    @staticmethod
    def get_ipv4_now():
        """获取当前主机的IPv4地址"""
        try:
            # 使用socket获取本机IP地址
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个公共地址，不需要实际发送数据
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"获取IP地址失败: {str(e)}")
            return "127.0.0.1"  # 失败时返回本地回环地址
    
    @staticmethod
    def get_ipv4_address():
        """兼容性方法，返回当前IP地址"""
        return PPowerShell.get_ipv4_now()

    def file_json_Audio():
        """
        读取并更新音量亮度配置，避免直接使用COM
        改为使用COM保护系统读取音量和亮度值
        """
        if not COM_PROTECTION_AVAILABLE:
            print("COM保护系统不可用，跳过音量亮度更新")
            return
            
        need_update = False
        try:
            # 使用COM保护系统获取当前值
            current_volume = None
            current_brightness = None
            
            # 获取音量（使用缓存）
            volume_result = safe_get_volume(use_cache=True)
            if volume_result.get("success"):
                current_volume = volume_result.get("volume")
            
            # 获取亮度（使用缓存）
            brightness_result = safe_get_brightness(use_cache=True)
            if brightness_result.get("success"):
                current_brightness = brightness_result.get("brightness")
            
            # 读取orderlist数据
            config_dir = init_config_directory()
            orderlist_path = os.path.join(config_dir, config_orderlist)
            data = safe_json_read(orderlist_path, config_orderlist, [])
            
            # 更新数据项
            for item in data:
                if item.get('title') == '音量控制' and current_volume is not None:
                    if item.get('value') != current_volume:
                        item['value'] = current_volume
                        need_update = True
                
                elif item.get('title') == '亮度控制' and current_brightness is not None:
                    if item.get('value') != current_brightness:
                        item['value'] = current_brightness
                        need_update = True
            
            # 只有在需要更新时才写入文件
            if need_update:
                if safe_json_write(orderlist_path, config_orderlist, data):
                    print("配置文件已更新音量和亮度值")
        except Exception as e:
            print(f"更新音量和亮度值时出错: {str(e)}")
    
    @staticmethod
    def update_audio_brightness_cache(volume=None, brightness=None):
        """
        更新音量亮度缓存 - 现在由COM保护系统自动处理
        保留此方法以维持兼容性
        """
        try:
            config_dir = init_config_directory()
            cache_path = os.path.join(config_dir, 'audio_brightness_cache.json')
            
            # 使用线程安全的文件操作
            cache_data = safe_json_read(cache_path, 'audio_brightness_cache.json', {})
            
            # 只更新提供的值
            if volume is not None:
                cache_data["volume"] = volume
            if brightness is not None:
                cache_data["brightness"] = brightness
            
            # 添加更新时间戳
            cache_data["last_update"] = time.time()
            
            # 线程安全地保存缓存文件
            if not safe_json_write(cache_path, 'audio_brightness_cache.json', cache_data):
                print("更新音量亮度缓存失败")
                
        except Exception as e:
            print(f"更新音量亮度缓存出错: {str(e)}")

    def file_json_geshihua(ipv4,port):
        #格式化data json数据，设置为当机地址
        #----------历史屎坑--------如果去除它则无法运行
        PPowerShell.get_ipv4_address()
        #----------历史屎坑--------如果去除它则无法运行
        config_dir = init_config_directory()
        orderlist_path = os.path.join(config_dir, config_orderlist)
        with open(orderlist_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        for item in data:
            if item['guding'] == 'n':
                url_parts = item['apiUrl'].split('//')
                if len(url_parts) > 1:
                    address = url_parts[1].split('/')[0]
                    formatted_address = address.replace(address, f'{ipv4}:{port+1}')
                    item['apiUrl'] = item['apiUrl'].replace(address, formatted_address)

        with open(orderlist_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print("读取了配置文件")

    def file_json_geshihua_prot(port):
         #格式化data json数据，设置为启动端口
        config_dir = init_config_directory()
        orderlist_path = os.path.join(config_dir, config_orderlist)
        with open(orderlist_path, 'r', encoding='utf-8') as file:
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
        with open(orderlist_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print("配置文件更新完成")

    def check_files_and_dirs(app_name, app_file,server_lujin):
        # 初始化配置目录
        config_dir = init_config_directory()
        
        print(f"\n环境已检查：正常，配置目录: {config_dir}")
        
        # 检查id.json文件是否存在，不存在则创建
        id_json_path = os.path.join(config_dir, "id.json")
        if not os.path.exists(id_json_path):
            print(f"创建{id_json_path}")
            try:
                with open(id_json_path, 'w', encoding='utf-8') as file:
                    json.dump({"name": ""}, file, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"创建{id_json_path}失败: {str(e)}")
                messagebox.showinfo("涵涵的控制终端核心", f"创建{id_json_path}失败: {str(e)}")
                os._exit(1)
                
        # 是否第一次启动 设置第一次启动自行开启开机启动
        one_file_path = os.path.join(config_dir, "one")
        if os.path.exists(one_file_path):
            pass
        else:
            with open(one_file_path, "w") as file:
                pass
            Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}{os.sep}{app_file}")
        print(f"{server_lujin}{os.sep}{app_file}")
        # 检查是否需要设置设备名
        with open(id_json_path, 'r', encoding='utf-8') as file:
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
                        with open(id_json_path, 'r', encoding='utf-8') as id_file:
                            id_data = json.load(id_file)
                        id_data['name'] = user_input
                        with open(id_json_path, 'w', encoding='utf-8') as id_file:
                            json.dump(id_data, id_file, indent=2, ensure_ascii=False)
                        
                        # 修改 orderlist.json
                        try:
                            orderlist_path = os.path.join(config_dir, 'orderlist.json')
                            with open(orderlist_path, 'r', encoding='utf-8') as f:
                                orderlist_data = json.load(f)
                            # 添加 try 是为了让 orderlist 中显示设备名 
                            try:
                                if orderlist_data[0]['//1'] == '以上是标题,可以在任务栏中修改':
                                    orderlist_data[0]['title'] = f"{user_input}"
                                    with open(orderlist_path, 'w', encoding='utf-8') as f:
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
                
                # 添加显示App介绍图片的函数
                def show_app_intro():
                    try:
                        intro_path = f"{server_lujin}{os.sep}LookMe.png"
                        if not os.path.exists(intro_path):
                            messagebox.showinfo("涵涵的控制终端", "找不到介绍图片")
                            return
                            
                        # 使用Windows默认应用打开图片
                        os.startfile(intro_path)
                    except Exception as e:
                        messagebox.showerror("涵涵的控制终端", f"打开介绍图片时出错: {str(e)}")
                
                window = tk.Tk()
                window.title("涵涵的控制终端")
                window_width, window_height = 365, 220
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
                    text="欢迎使用小涵的软件，请为你的设备取个名字吧~\n\n记得在后续弹出的窗口点击允许哦",
                    font=("微软雅黑", 11),
                    wraplength=340,
                )
                welcome_label.pack(pady=(0, 15))
                # 输入框
                entry_frame = tk.Frame(main_frame, bg="#f0f0f0")
                entry_frame.pack(fill=tk.X, pady=5)
                entry = tk.Entry(entry_frame, font=("微软雅黑", 10), width=30)
                entry.pack(pady=5)
                entry.focus_set()
                
                # 修改按钮框架为水平布局
                button_frame = tk.Frame(main_frame, bg="#f0f0f0")
                button_frame.pack(pady=10)
                
                # 确定按钮
                confirm_button = tk.Button(
                    button_frame, 
                    text="确定", 
                    command=save_device_name,
                    width=10,
                    bg="#282c34",
                    fg="white",
                    relief=tk.FLAT,
                    font=("微软雅黑", 11)
                )
                confirm_button.pack(side=tk.LEFT, padx=5, pady=5)
                
                # 添加"app介绍"按钮
                intro_button = tk.Button(
                    button_frame, 
                    text="app介绍", 
                    command=show_app_intro,
                    width=10,
                    bg="#282c34",
                    fg="white",
                    relief=tk.FLAT,
                    font=("微软雅黑", 11)
                )
                intro_button.pack(side=tk.LEFT, padx=5, pady=5)
                
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
                with open(id_json_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                if data.get('name', '') == '':
                    print("设备名设置失败或被取消")
                    os._exit(1)
            except:
                pass
        
        # 修改返回值，获取并返回IP地址
        ip_address = PPowerShell.get_ipv4_now()
        return ip_address

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
                
                # 定期更新音量和亮度值到配置文件
                PPowerShell.file_json_Audio()
                
                # 异步等待10秒
                await asyncio.sleep(10)
            except Exception as e:
                print(f"IP检测异常: {str(e)}")
                await asyncio.sleep(30)  # 出错时延长等待时间

    def verify_device(json_data, device_lock):
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        config_dir = init_config_directory()
        devices_path = os.path.join(config_dir, 'Devices.json')
        with open(devices_path, 'r', encoding='utf-8') as file:
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
                        with open(devices_path, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                    elif choice == "blacklist":
                        blacklisted_devices.append({"deviceId": device_id, "deviceName": model_id})
                        config["blacklistedDevices"] = blacklisted_devices
                        with open(devices_path, 'w', encoding='utf-8') as f:
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

    # 修改音量控制函数，使用进程隔离
    @staticmethod
    def control_system_volume(volume_percent):
        """
        使用COM保护系统设置系统音量
        :param volume_percent: 音量百分比，范围0-100
        :return: 成功返回True和当前音量，失败返回False和错误信息
        """
        if not COM_PROTECTION_AVAILABLE:
            return False, "COM保护系统不可用"
        
        try:
            result = safe_set_volume(volume_percent)
            
            if result.get("success"):
                current_percent = result.get("volume", volume_percent)
                # 保持兼容性，更新旧缓存
                PPowerShell.update_audio_brightness_cache(volume=current_percent)
                return True, f"已设置音量至: {current_percent}%"
            else:
                error_msg = result.get("error", "未知错误")
                return False, f"设置音量失败: {error_msg}"
        except Exception as e:
            return False, f"设置音量异常: {str(e)}"
        
    # 修改亮度控制功能，使用进程隔离
    @staticmethod
    def control_system_brightness(brightness_percent):
        """
        使用COM保护系统设置屏幕亮度
        :param brightness_percent: 亮度百分比，范围0-100
        :return: 成功返回True和当前亮度，失败返回False和错误信息
        """
        if not COM_PROTECTION_AVAILABLE:
            return False, "COM保护系统不可用"
        
        try:
            result = safe_set_brightness(brightness_percent)
            
            if result.get("success"):
                current_percent = result.get("brightness", brightness_percent)
                # 保持兼容性，更新旧缓存
                PPowerShell.update_audio_brightness_cache(brightness=current_percent)
                return True, f"已设置亮度至: {current_percent}%"
            else:
                error_msg = result.get("error", "未知错误")
                return False, f"设置亮度失败: {error_msg}"
        except Exception as e:
            return False, f"设置亮度异常: {str(e)}"

    @staticmethod
    def update_volume_brightness_safe():
        """
        使用COM保护系统安全更新音量和亮度信息到orderlist
        """
        if not COM_PROTECTION_AVAILABLE:
            print("COM保护系统不可用，跳过音量亮度更新")
            return False
            
        # 添加高频访问限制
        current_time = time.time()
        if current_time - PPowerShell.last_volume_brightness_update < PPowerShell.MIN_UPDATE_INTERVAL:
            print(f"更新音量和亮度过于频繁，已跳过本次更新 (间隔: {current_time - PPowerShell.last_volume_brightness_update:.2f}秒)")
            return False
            
        # 更新时间戳
        PPowerShell.last_volume_brightness_update = current_time
        
        try:
            # 使用COM保护系统获取音量和亮度
            current_volume = None
            current_brightness = None
            
            # 获取音量（优先使用缓存，减少COM调用）
            volume_result = safe_get_volume(use_cache=True)
            if volume_result.get("success"):
                current_volume = volume_result.get("volume")
                if volume_result.get("from_cache"):
                    print("使用缓存的音量值")
                        
            # 获取亮度（优先使用缓存，减少COM调用）
            brightness_result = safe_get_brightness(use_cache=True)
            if brightness_result.get("success"):
                current_brightness = brightness_result.get("brightness")
                if brightness_result.get("from_cache"):
                    print("使用缓存的亮度值")
            
            # 更新COM保护系统缓存到旧缓存（兼容性）
            if current_volume is not None or current_brightness is not None:
                PPowerShell.update_audio_brightness_cache(
                    volume=current_volume, 
                    brightness=current_brightness
                )
            
            # 更新orderlist数据
            need_update = False
            try:
                config_dir = init_config_directory()
                orderlist_path = os.path.join(config_dir, config_orderlist)
                data = safe_json_read(orderlist_path, config_orderlist, [])
                
                for item in data:
                    if item.get('title') == '音量控制' and current_volume is not None:
                        if item.get('value') != current_volume:
                            item['value'] = current_volume
                            need_update = True
                    
                    elif item.get('title') == '亮度控制' and current_brightness is not None:
                        if item.get('value') != current_brightness:
                            item['value'] = current_brightness
                            need_update = True
                
                if need_update:
                    if safe_json_write(orderlist_path, config_orderlist, data):
                        print("配置文件已更新音量和亮度值")
                    
            except Exception as e:
                print(f"更新音量亮度配置文件时出错: {str(e)}")
                
        except Exception as e:
            print(f"更新音量亮度总体出错: {str(e)}")
    
    # 只保留获取当前活动网络接口MAC地址的方法
    @staticmethod
    def get_mac_address():
        try:
            current_ip = PPowerShell.get_ipv4_now()
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                has_current_ip = False
                mac_address = None
                
                for addr in addresses:
                    if addr.family == socket.AF_INET and addr.address == current_ip:
                        has_current_ip = True
                    elif addr.family == psutil.AF_LINK:  # MAC地址
                        mac_address = addr.address
                if has_current_ip and mac_address:
                    mac_formatted = mac_address.lower().replace('-', ':')
                    return mac_formatted
            return "00:00:00:00:00:00"
        except Exception as e:
            print(f"获取活动网络接口MAC地址失败: {str(e)}")
            return "00:00:00:00:00:00"  # 失败时返回默认值

if __name__ == "__main__":
    # 初始化崩溃监控系统
    monitor = init_crash_monitor()
    monitor.log_info("=== 涵涵终端控制核心启动 ===")
    monitor.log_info("崩溃监控系统已启动")
    
    # 初始化COM保护系统
    if COM_PROTECTION_AVAILABLE:
        protection_system = get_protection_system()
        monitor.log_info("COM保护系统已启动")
        
        # 显示系统统计
        stats = protection_system.get_system_stats()
        monitor.log_info(f"COM保护系统统计: {stats}")
    else:
        monitor.log_warning("COM保护系统不可用，音量和亮度功能受限")
    
    try:
        #print(PPowerShell.file_json_Audio())
        print(f"当前活动网络接口MAC地址: {PPowerShell.get_mac_address()}")
        print(f"当前IP地址: {PPowerShell.get_ipv4_now()}")
        monitor.log_info(f"系统初始化完成 - MAC: {PPowerShell.get_mac_address()}, IP: {PPowerShell.get_ipv4_now()}")
        
        # 测试COM保护系统功能
        if COM_PROTECTION_AVAILABLE:
            try:
                volume_info = safe_get_volume()
                brightness_info = safe_get_brightness()
                monitor.log_info(f"音量状态: {volume_info.get('success', False)}, 亮度状态: {brightness_info.get('success', False)}")
            except Exception as e:
                monitor.log_warning(f"COM功能测试异常: {str(e)}")
                
    except Exception as e:
        monitor.log_critical(f"主程序启动失败: {str(e)}")
        raise
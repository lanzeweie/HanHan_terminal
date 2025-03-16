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
# 添加音量控制所需的库
from ctypes import POINTER, cast
from tkinter import messagebox

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

# 添加亮度控制相关的导入
try:
    import screen_brightness_control as sbc
    import wmi
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False

from flask import jsonify, request

from WinTaskbar import Taskbar


# 添加节流控制器类
class ThrottleController:
    def __init__(self, cooldown_time=0.3):  # 默认冷却时间300ms
        self.last_call_time = {}  # 存储各个函数的上次调用时间
        self.cooldown_time = cooldown_time
        self.lock = threading.Lock()
        
    def can_execute(self, function_name):
        """检查函数是否可以执行，基于冷却时间"""
        with self.lock:
            current_time = time.time()
            last_time = self.last_call_time.get(function_name, 0)
            
            if current_time - last_time >= self.cooldown_time:
                self.last_call_time[function_name] = current_time
                return True
            return False

# 创建全局节流控制器实例
throttle_controller = ThrottleController(cooldown_time=0.3)  # 300ms冷却时间

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
    server_lujin = os.path.dirname(os.path.abspath(sys.argv[0]))

class PPowerShell():
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
        改为从缓存文件中读取最近的音量和亮度值
        """
        need_update = False
        try:
            # 使用配置文件缓存的方式而非直接COM调用
            config_cache_path = f'{server_lujin}{os.sep}data{os.sep}audio_brightness_cache.json'
            
            # 尝试读取缓存文件中的值
            current_volume = None
            current_brightness = None
            
            if os.path.exists(config_cache_path):
                try:
                    with open(config_cache_path, 'r', encoding='utf-8') as cache_file:
                        cache_data = json.load(cache_file)
                        current_volume = cache_data.get("volume")
                        current_brightness = cache_data.get("brightness")
                        last_update = cache_data.get("last_update", 0)
                        
                        # 如果缓存是最近10秒内更新的，直接使用缓存值
                        if time.time() - last_update < 10:
                            print("使用缓存的音量亮度值，避免COM操作")
                except Exception as e:
                    print(f"读取音量亮度缓存出错: {str(e)}")
            
            # 读取orderlist数据
            with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # 更新数据项
            for item in data:
                if item['title'] == '音量控制' and current_volume is not None:
                    if item['value'] != current_volume:
                        item['value'] = current_volume
                        need_update = True
                
                elif item['title'] == '亮度控制' and current_brightness is not None:
                    if item['value'] != current_brightness:
                        item['value'] = current_brightness
                        need_update = True
            
            # 只有在需要更新时才写入文件
            if need_update:
                with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=2, ensure_ascii=False)
                print("配置文件已更新音量和亮度值")
        except Exception as e:
            print(f"更新音量和亮度值时出错: {str(e)}")
    
    @staticmethod
    def update_audio_brightness_cache(volume=None, brightness=None):
        """
        更新音量亮度缓存文件，在成功控制音量亮度后调用
        同时更新orderlist文件确保UI及时反映
        """
        try:
            cache_path = f'{server_lujin}{os.sep}data{os.sep}audio_brightness_cache.json'
            cache_data = {}
            
            # 先读取现有缓存
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                except:
                    pass
            
            # 只更新提供的值
            if volume is not None:
                cache_data["volume"] = volume
            if brightness is not None:
                cache_data["brightness"] = brightness
            
            # 添加更新时间戳
            cache_data["last_update"] = time.time()
            
            # 保存缓存文件
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            # 立即更新orderlist文件，确保UI显示最新值
            try:
                with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                need_update = False
                for item in data:
                    if item['title'] == '音量控制' and volume is not None:
                        if item['value'] != volume:
                            item['value'] = volume
                            need_update = True
                    
                    elif item['title'] == '亮度控制' and brightness is not None:
                        if item['value'] != brightness:
                            item['value'] = brightness
                            need_update = True
                
                if need_update:
                    with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                        json.dump(data, file, indent=2, ensure_ascii=False)
                    print(f"实时更新音量/亮度: {'音量'+str(volume) if volume is not None else ''} {'亮度'+str(brightness) if brightness is not None else ''}")
            except Exception as e:
                print(f"实时更新orderlist失败: {str(e)}")
                
        except Exception as e:
            print(f"更新音量亮度缓存出错: {str(e)}")

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

    def check_files_and_dirs(app_name, app_file,server_lujin):
        files_and_dirs = [f"{server_lujin}{os.sep}data"]
        for item in files_and_dirs:  
            if os.path.exists(item):  
                pass  
            else:  
                print(f"缺失{item}")
                messagebox.showinfo("涵涵的控制终端核心", f"缺失{item}")  
                os._exit(1)  # 添加退出代码
        print("\n环境已检查：正常")
        # 是否第一次启动 设置第一次启动自行开启开机启动
        if os.path.exists(f"{server_lujin}{os.sep}data{os.sep}one"):
            pass
        else:
            with open(f"{server_lujin}{os.sep}data{os.sep}one", "w") as file:
                pass
            Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}{os.sep}{app_file}")
        print(f"{server_lujin}{os.sep}{app_file}")
        # 检查是否需要设置设备名
        with open(f"{server_lujin}{os.sep}data{os.sep}id.json", 'r', encoding='utf-8') as file:
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
                        with open(f'{server_lujin}{os.sep}data{os.sep}id.json', 'r', encoding='utf-8') as id_file:
                            id_data = json.load(id_file)
                        id_data['name'] = user_input
                        with open(f'{server_lujin}{os.sep}data{os.sep}id.json', 'w', encoding='utf-8') as id_file:
                            json.dump(id_data, id_file, indent=2, ensure_ascii=False)
                        
                        # 修改 orderlist.json
                        try:
                            with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'r', encoding='utf-8') as f:
                                orderlist_data = json.load(f)
                            # 添加 try 是为了让 orderlist 中显示设备名 
                            try:
                                if orderlist_data[0]['//1'] != '以上是标题,可以在任务栏中修改':
                                    orderlist_data[0]['title'] = f"{user_input}"
                                    with open(f'{server_lujin}{os.sep}data{os.sep}orderlist.json', 'w', encoding='utf-8') as f:
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
                        intro_path = f"{server_lujin}{os.sep}介绍.png"
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
                with open(f"{server_lujin}{os.sep}data{id.json}", 'r', encoding='utf-8') as file:
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

    @staticmethod
    def _execute_volume_control_in_subprocess(volume_percent):
        """控制系统音量，使用直接方法而非临时脚本"""
        try:
            if not PYCAW_AVAILABLE:
                return False, "pycaw库未安装，无法控制音量"
                
            # 规范化音量值到0-100范围内
            volume_percent = max(0, min(100, volume_percent))
            
            # 使用pycaw库直接设置音量
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # 将百分比转换为0-1范围
            target_volume = volume_percent / 100.0
            
            # 设置音量
            volume.SetMasterVolumeLevelScalar(target_volume, None)
            
            # 读取当前音量确认
            current_volume = volume.GetMasterVolumeLevelScalar()
            current_percent = int(current_volume * 100)
            
            return True, current_percent
            
        except Exception as e:
            return False, f"执行音量控制失败: {str(e)}"

    @staticmethod
    def _execute_brightness_control_in_subprocess(brightness_percent):
        """控制屏幕亮度，使用直接方法而非临时脚本"""
        try:
            if not BRIGHTNESS_AVAILABLE:
                return False, "screen_brightness_control库未安装，无法控制亮度"
            
            # 规范化亮度值到0-100范围内
            brightness_level = max(0, min(100, brightness_percent))
            
            # 直接设置亮度
            sbc.set_brightness(brightness_level)
            
            # 读取设置后的亮度确认
            try:
                current_brightness = sbc.get_brightness()
                # 处理返回值可能是列表的情况
                if isinstance(current_brightness, list):
                    current_percent = current_brightness[0] if current_brightness else brightness_level
                else:
                    current_percent = current_brightness
            except:
                current_percent = brightness_level  # 如果获取失败，返回设置值
                
            return True, current_percent
            
        except Exception as e:
            return False, f"执行亮度控制失败: {str(e)}"

    @staticmethod
    def control_system_volume(volume_percent):
        """
        通过直接方法设置系统音量，避免COM初始化问题
        :param volume_percent: 音量百分比，范围0-100
        :return: 成功返回True和当前音量，失败返回False和错误信息
        """
        function_name = "control_system_volume"
        
        # 检查是否可以执行(节流控制)
        if not throttle_controller.can_execute(function_name):
            # 如果在冷却期间，读取并返回缓存值
            try:
                cache_path = f'{server_lujin}{os.sep}data{os.sep}audio_brightness_cache.json'
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if "volume" in cache_data and cache_data["volume"] == volume_percent:
                            return True, f"音量已经是 {volume_percent}%，无需调整"
            except:
                pass
            
            return False, "音量控制操作过于频繁，请稍后再试"
        
        if not PYCAW_AVAILABLE:
            return False, "pycaw库未安装，无法控制音量"
        
        # 直接调用控制方法
        success, result = PPowerShell._execute_volume_control_in_subprocess(volume_percent)
        
        if success:
            # 如果是整数，表示当前音量
            if isinstance(result, int):
                current_percent = result
                # 更新缓存
                PPowerShell.update_audio_brightness_cache(volume=current_percent)
                # 返回成功和当前音量
                return True, f"已设置音量至: {current_percent}%"
            else:
                # 更新缓存为目标值
                PPowerShell.update_audio_brightness_cache(volume=volume_percent)
                return True, f"已设置音量至约: {volume_percent}%"
        else:
            return False, f"设置音量失败: {result}"

    @staticmethod
    def control_system_brightness(brightness_percent):
        """
        通过直接方法设置屏幕亮度，避免COM初始化问题
        :param brightness_percent: 亮度百分比，范围0-100
        :return: 成功返回True和当前亮度，失败返回False和错误信息
        """
        function_name = "control_system_brightness"
        
        # 检查是否可以执行(节流控制)
        if not throttle_controller.can_execute(function_name):
            # 如果在冷却期间，读取并返回缓存值
            try:
                cache_path = f'{server_lujin}{os.sep}data{os.sep}audio_brightness_cache.json'
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if "brightness" in cache_data and cache_data["brightness"] == brightness_percent:
                            return True, f"亮度已经是 {brightness_percent}%，无需调整"
            except:
                pass
            
            return False, "亮度控制操作过于频繁，请稍后再试"
        
        if not BRIGHTNESS_AVAILABLE:
            return False, "screen_brightness_control库未安装，无法控制亮度"
        
        # 直接调用控制方法
        success, result = PPowerShell._execute_brightness_control_in_subprocess(brightness_percent)
        
        if success:
            # 如果是整数，表示当前亮度
            if isinstance(result, int):
                current_percent = result
                # 更新缓存
                PPowerShell.update_audio_brightness_cache(brightness=current_percent)
                # 返回成功和当前亮度
                return True, f"已设置亮度至: {current_percent}%"
            else:
                # 更新缓存为目标值
                PPowerShell.update_audio_brightness_cache(brightness=brightness_percent)
                return True, f"已设置亮度至约: {brightness_percent}%"
        else:
            return False, f"设置亮度失败: {result}"

    @staticmethod
    def update_volume_brightness_safe():
        """
        安全方式更新音量和亮度信息到orderlist，使用直接类方法而非子进程
        """
        function_name = "update_volume_brightness_safe"
        
        # 检查是否可以执行(节流控制)
        if not throttle_controller.can_execute(function_name):
            return
        
        try:
            # 获取系统音量和亮度
            current_volume = None
            current_brightness = None
            
            # 1. 尝试从缓存读取最后的值
            try:
                cache_path = f'{server_lujin}{os.sep}data{os.sep}audio_brightness_cache.json'
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        last_update_time = cache_data.get("last_update", 0)
                        # 如果缓存是最近10秒内的，直接使用缓存值
                        if time.time() - last_update_time < 10:
                            current_volume = cache_data.get("volume")
                            current_brightness = cache_data.get("brightness")
                            print("使用缓存的音量亮度值，避免频繁请求")
            except Exception as e:
                print(f"读取音量亮度缓存出错: {str(e)}")
            
            # 2. 如果缓存中没有值或缓存太旧，则尝试直接获取
            if current_volume is None and PYCAW_AVAILABLE:
                try:
                    # 直接获取当前音量
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    current_volume = int(volume.GetMasterVolumeLevelScalar() * 100)
                except Exception as e:
                    print(f"获取音量信息失败: {str(e)}")
                    
            if current_brightness is None and BRIGHTNESS_AVAILABLE:
                try:
                    # 直接获取当前亮度
                    current_brightness_value = sbc.get_brightness()
                    if isinstance(current_brightness_value, list):
                        current_brightness = current_brightness_value[0] if current_brightness_value else 50
                    else:
                        current_brightness = current_brightness_value
                except Exception as e:
                    print(f"获取亮度信息失败: {str(e)}")
            
            # 3. 更新缓存和orderlist
            if current_volume is not None or current_brightness is not None:
                # 更新缓存
                PPowerShell.update_audio_brightness_cache(
                    volume=current_volume,
                    brightness=current_brightness
                )
                
                # 更新orderlist
                need_update = False
                try:
                    with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    for item in data:
                        if item['title'] == '音量控制' and current_volume is not None:
                            if item['value'] != current_volume:
                                item['value'] = current_volume
                                need_update = True
                        
                        elif item['title'] == '亮度控制' and current_brightness is not None:
                            if item['value'] != current_brightness:
                                item['value'] = current_brightness
                                need_update = True
                    
                    if need_update:
                        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                            json.dump(data, file, indent=2, ensure_ascii=False)
                        print("配置文件已更新音量和亮度值")
                except Exception as e:
                    print(f"更新音量亮度配置文件时出错: {str(e)}")
                
        except Exception as e:
            print(f"更新音量亮度总体出错: {str(e)}")

if __name__ == "__main__":
    print(PPowerShell.file_json_Audio())

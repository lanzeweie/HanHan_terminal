import asyncio
import datetime
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import winreg
import zipfile

# 新增：导入Win_Check的检查函数
from Win_Check import check_required_files

# 设置screen_brightness_control的日志级别为ERROR，屏蔽WARNING
logging.getLogger('screen_brightness_control.windows').setLevel(logging.ERROR)
from tkinter import messagebox

from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve

from WinDC import PPowerShell, init_config_directory
from WinTaskbar import Taskbar

# 初始化环境判断
if getattr(sys, 'frozen', False):
    server_lujin = os.path.dirname(sys.executable)
else:
    server_lujin = os.path.dirname(os.path.abspath(sys.argv[0]))

print(f"当前工作目录: {server_lujin}")

# 检查是否为Windows商店应用路径
is_windows_store_app = "WindowsApps" in server_lujin
if is_windows_store_app:
    print("检测到Windows商店应用路径，禁用日志写入功能")
else:
    print("检测到正常应用路径，启用日志写入功能")

# 日志压缩处理
log_file = "last.log"
app_file = os.path.basename(sys.argv[0])
zip_file_name = time.strftime("%Y_%m_%d_%H_%M_%S") + ".zip"
log_dir = f"{server_lujin}{os.sep}log"

# 根据路径判断是否启用日志功能
if not is_windows_store_app:
    os.makedirs(log_dir, exist_ok=True)
    if os.path.exists(f"{log_dir}{os.sep}{log_file}"):
        with zipfile.ZipFile(f"{log_dir}{os.sep}{zip_file_name}", 'w') as zf:
            zf.write(f"{log_dir}{os.sep}{log_file}", arcname=log_file)
    else:
        with open(f"{log_dir}{os.sep}{log_file}", "w") as f:
            f.write("")
    log_file_name = f"{log_dir}{os.sep}{log_file}"
else:
    # Windows商店应用不使用日志文件
    log_file_name = None
    print("Windows商店应用模式：跳过日志文件创建")

app = Flask(__name__)
CORS(app)

# 全局锁
device_lock = threading.Lock()

class FlaskAPIWeb:
    @app.before_request
    def check_headers():
        if request.method != "OPTIONS":
            required_headers = {'Authorization': 'i am Han Han'}
            for header, value in required_headers.items():
                if header not in request.headers or request.headers[header] != value:
                    return jsonify({
                        "error": "不允许你访问",
                        "message": "禁止你访问此内容"
                    }), 401

    @app.route('/hello', methods=['GET'])
    def hello():
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nrong = f"【{current_time}】\n[控制台]: 设备 {client_ip} 进行访问hello\n"
        print(nrong)
        if log_file_name:
            with open(log_file_name, "a", encoding="utf-8") as f:
                f.write(nrong)
        return jsonify({
            "title": "欢迎连接至终端",
            "execution_time": current_time,
            "success": True
        })

    @app.route('/name', methods=['GET'])
    def get_name():
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"【{current_time}】[控制台]: 设备 {client_ip} 访问name接口\n"
        print(log_msg)
        if log_file_name:
            with open(log_file_name, "a", encoding="utf-8") as f:
                f.write(log_msg)
        config_dir = init_config_directory()
        id_path = os.path.join(config_dir, "id.json")
        with open(id_path, "r", encoding="utf-8") as f:
            id_data = json.load(f)
            name = id_data.get("name", "")
        mac_address = PPowerShell.get_mac_address()
        return jsonify({
            "title": name,
            "execution_time": current_time,
            "mac": mac_address,
            "success": True
        })

    @app.route('/orderlist', methods=['POST'])
    def orderlist():
        client_ip = request.remote_addr
        json_data = request.get_json()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"【{current_time}】\n[控制台]: 设备 {client_ip} 询问链接")
        print("JSON 数据:", json_data)

        verify_result = PPowerShell.verify_device(json_data, device_lock)
        if verify_result is not True:
            return verify_result

        try:
            update_thread = threading.Thread(target=PPowerShell.update_volume_brightness_safe)
            update_thread.daemon = True
            update_thread.start()
            update_thread.join(timeout=1.0)

            config_dir = init_config_directory()
            json_file_path = os.path.join(config_dir, "orderlist.json")
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                response = json.load(json_file)
                return jsonify(response)
        except Exception as e:
            print(f"处理orderlist请求时出错: {str(e)}")
            return jsonify({"error": "服务器内部错误"}), 500

    @app.route('/command', methods=['POST'])
    def run_command_zdy():
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_data = request.get_json()

        print(f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令 【自定义命令】")
        print("JSON 数据:", json_data)

        if log_file_name:
            with open(log_file_name, "a", encoding="utf-8") as f:
                f.write(f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令 【自定义命令】\nJSON 数据: {json_data}\n")

        verify_result = PPowerShell.verify_device(json_data, device_lock)
        if verify_result is not True:
            return verify_result

        cmd_back = ""
        if json_data.get("name") == "han han":
            data_command = json_data.get("command")
            
            # 检查是否启用了命令授权验证
            config_dir = init_config_directory()
            devices_path = os.path.join(config_dir, "Devices.json")
            
            # 检查Devices.json是否存在，以及授权设置
            enable_auth = False
            if os.path.exists(devices_path):
                try:
                    with open(devices_path, "r", encoding="utf-8") as f:
                        devices_data = json.load(f)
                        enable_auth = devices_data.get("enable_orderlist_shouquan") == "true"
                except Exception as e:
                    print(f"读取Devices.json出错: {str(e)}")
            
            # 如果启用了授权验证，验证命令是否在orderlist.json中
            if enable_auth:
                orderlist_path = os.path.join(config_dir, "orderlist.json")
                command_authorized = False
                try:
                    if os.path.exists(orderlist_path):
                        with open(orderlist_path, "r", encoding="utf-8") as f:
                            orderlist_data = json.load(f)
                            for item in orderlist_data:
                                # 检查命令是否在命令列表中（使用datacommand字段）
                                if item.get("datacommand") == data_command:
                                    command_authorized = True
                                    break
                    
                    if not command_authorized:
                        print(f"命令在列表中不存在: {data_command}")
                        return jsonify({
                            "title": "命令拒绝执行",
                            "execution_time": current_time,
                            "success": False,
                            "cmd_back": "拒绝执行陌生命令，此命令未在命令列表中"
                        })
                except Exception as e:
                    print(f"验证命令授权时出错: {str(e)}")
            
            app_files = os.listdir(f"{server_lujin}{os.sep}app")
            
            # 处理应用程序路径
            for file in app_files:
                if file in data_command:
                    absolute_path = os.path.join(f"{server_lujin}//app", file)
                    data_command = data_command.replace(file, absolute_path)
                    print("【控制台】发现命令的程序存在于[app/目录]中，将强行使用 [app/目录]中的程序作为程序源")

            # 处理带参数的指令
            if json_data.get("value") is not None:
                data_value = json_data.get("value")
                def data_intstat(cmd, val):
                    if cmd == "setsysvolume {value}":
                        volume = int(val)
                        success, message = PPowerShell.control_system_volume(volume)
                        if not success:
                            print(f"音量控制失败: {message}")
                            if log_file_name:
                                with open(log_file_name, "a", encoding="utf-8") as f:
                                    f.write(f"【{current_time}】\n[控制台]: 音量控制失败: {message}\n")
                        return "python_volume_control_success" if success else f"python_volume_control_failed:{message}"
                    elif cmd == "setbrightness {value}":
                        brightness = int(val)
                        success, message = PPowerShell.control_system_brightness(brightness)
                        if not success:
                            print(f"亮度控制失败: {message}")
                            if log_file_name:
                                with open(log_file_name, "a", encoding="utf-8") as f:
                                    f.write(f"【{current_time}】\n[控制台]: 亮度控制失败: {message}\n")
                        return "python_brightness_control_success" if success else f"python_brightness_control_failed:{message}"
                    else:
                        return cmd.replace('{value}', str(val))
                
                data_command = data_intstat(data_command, data_value)

            # 处理命令执行结果
            try:
                if data_command == "python_volume_control_success":
                    cmd_back = f"已成功将系统音量设置为{data_value}%"
                    # 更新orderlist数据
                    orderlist_path = os.path.join(config_dir, "orderlist.json")
                    with open(orderlist_path, 'r+', encoding='utf-8') as f:
                        orderlist_data = json.load(f)
                        for item in orderlist_data:
                            if item.get('title') == '音量控制':
                                item['value'] = int(data_value)
                        f.seek(0)
                        json.dump(orderlist_data, f, indent=2, ensure_ascii=False)
                        f.truncate()
                elif data_command.startswith("python_volume_control_failed"):
                    error_detail = data_command.split(":", 1)[1] if ":" in data_command else "未知错误"
                    cmd_back = f"设置系统音量为{data_value}%失败: {error_detail}"
                    print(f"详细错误: {error_detail}")
                elif data_command == "python_brightness_control_success":
                    cmd_back = f"已成功将屏幕亮度设置为{data_value}%"
                    orderlist_path = os.path.join(config_dir, "orderlist.json")
                    with open(orderlist_path, 'r+', encoding='utf-8') as f:
                        orderlist_data = json.load(f)
                        for item in orderlist_data:
                            if item.get('title') == '亮度控制':
                                item['value'] = int(data_value)
                        f.seek(0)
                        json.dump(orderlist_data, f, indent=2, ensure_ascii=False)
                        f.truncate()
                elif data_command.startswith("python_brightness_control_failed"):
                    error_detail = data_command.split(":", 1)[1] if ":" in data_command else "未知错误"
                    cmd_back = f"设置屏幕亮度为{data_value}%失败: {error_detail}"
                    print(f"详细错误: {error_detail}")
                else:
                    output = subprocess.check_output(data_command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
                    cmd_back = output
            except subprocess.CalledProcessError as e:
                cmd_back = f"命令执行错误: {e.output}"
                if "系统找不到指定的文件" in str(e):
                    cmd_back += "\n可能原因: 命令文件不存在或路径错误"
                elif "拒绝访问" in str(e):
                    cmd_back += "\n可能原因: 没有足够的权限执行此命令"

        return jsonify({
            "title": "命令返回状态",
            "execution_time": current_time,
            "success": True,
            "cmd_back": cmd_back
        })

    @staticmethod
    def add_to_startup(app_name, app_path):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)

    @staticmethod
    async def check_ipv4_dynamic_state_async(port, taskbar_instance, loop):
        """异步IP地址变化检测"""
        last_ip = PPowerShell.get_ipv4_now()
        config_dir = init_config_directory()
        cache_path = os.path.join(config_dir, 'audio_brightness_cache.json')
        
        if not os.path.exists(cache_path):
            try:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "volume": 50,
                        "brightness": 50,
                        "last_update": time.time()
                    }, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"创建缓存文件失败: {str(e)}")

        while True:
            try:
                current_ip = PPowerShell.get_ipv4_now()
                if current_ip != last_ip:
                    print(f"IP地址变更: {last_ip} -> {current_ip}")
                    taskbar_instance.update_ip(current_ip)
                    PPowerShell.file_json_geshihua(current_ip, port)
                    last_ip = current_ip
                await asyncio.sleep(10)
            except Exception as e:
                print(f"IP检测异常: {str(e)}")
                await asyncio.sleep(30)

class ServerBasics:
    @staticmethod
    def run_socket(host, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 改为UDP
        try:
            server_socket.bind((host, port))
            print(f"Socket服务已启动在 {host}:{port}")
            server_socket.settimeout(1.0)  # 设置超时以允许优雅关闭
            while True:
                try:
                    data, client_address = server_socket.recvfrom(1024)  # UDP接收数据
                    current_time = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S')
                    print(f"【{current_time}】已被设备 {client_address} 发现")
                    # UDP响应设备名称
                    config_dir = init_config_directory()
                    id_path = os.path.join(config_dir, "id.json")
                    with open(id_path, "r", encoding="utf-8") as f:
                        id_data = json.load(f)
                    name = id_data.get("name", "")
                    response = name.encode('utf-8')
                    server_socket.sendto(response, client_address)
                except socket.timeout:
                    continue  # 超时后继续循环
                except Exception as e:
                    print(f"UDP接收数据异常: {str(e)}")
                    continue
        except Exception as e:
            print(f"Socket服务启动失败: {str(e)}")
            messagebox.showinfo("错误", f"端口绑定失败: {str(e)}")
            os._exit(1)
        finally:
            server_socket.close()

if __name__ == '__main__':
    print("------------------------------\n涵的涵涵的控制终端核心\n------------------------------")

    # 新增：启动时检查依赖文件
    check_required_files(server_lujin)

    # 函数补丁
    original_volume_control = PPowerShell.control_system_volume
    original_brightness_control = PPowerShell.control_system_brightness

    def patched_volume_control(volume):
        config_dir = init_config_directory()
        config_path = os.path.join(config_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if config.get("volume") == volume:
                    return True, "音量未变化"
        return original_volume_control(volume)

    def patched_brightness_control(brightness):
        config_dir = init_config_directory()
        config_path = os.path.join(config_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if config.get("brightness") == brightness:
                    return True, "亮度未变化"
        return original_brightness_control(brightness)

    PPowerShell.control_system_volume = patched_volume_control
    PPowerShell.control_system_brightness = patched_brightness_control

    # 初始化配置
    host = '0.0.0.0'
    port = 5201
    app_name = "涵的控制终端"
    PPowerShell.check_files_and_dirs(app_name, app_file, server_lujin)

    # 任务栏初始化
    print("启动Windows任务栏组件")
    Taskbar_start = Taskbar(server_lujin, app_name, app_file, PPowerShell.get_ipv4_now(), port)
    
    # 添加 update_ip 方法到 Taskbar 类（如果不存在）
    if not hasattr(Taskbar_start, 'update_ip'):
        def update_ip(self, new_ip):
            """更新IP地址并刷新任务栏显示"""
            self.ipv4_ip = new_ip
            self.icon_dongtai(new_ip, self.port)
        
        # 动态添加方法
        import types
        Taskbar_start.update_ip = types.MethodType(update_ip, Taskbar_start)
    
    taskbar_loop = asyncio.new_event_loop()
    taskbar_thread = threading.Thread(
        target=lambda: taskbar_loop.run_until_complete(Taskbar_start.chushihua_async(taskbar_loop)),
        daemon=True
    )
    taskbar_thread.start()

    # IP检测线程
    ipv4_loop = asyncio.new_event_loop()
    asyncio_thread = threading.Thread(
        target=lambda: ipv4_loop.run_until_complete(FlaskAPIWeb.check_ipv4_dynamic_state_async(port, Taskbar_start, ipv4_loop)),
        daemon=True
    )
    asyncio_thread.start()

    # 网络服务
    print("初始化网络服务...")
    socket_thread = threading.Thread(target=ServerBasics.run_socket, args=(host, port))
    socket_thread.daemon = True
    socket_thread.start()
    socket_thread.join(1)

    # 启动Flask服务
    try:
        print(f"\n服务地址：{PPowerShell.get_ipv4_now()}:{port}/{port+1}")
        print(f"启动Flask服务在 {host}:{port+1}")
        serve(app, host=host, port=port + 1)
    except Exception as e:
        print(f"服务启动失败: {str(e)}")
        messagebox.showinfo("错误", f"端口 {port+1} 被占用")
        os._exit(0)

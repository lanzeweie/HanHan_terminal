import datetime
import json
import os
import socket
import subprocess
import sys
import threading
import time
import winreg
import zipfile
# 任务栏小图标
from tkinter import messagebox

from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve

# PPowerShell库
from WinDC import PPowerShell
from WinTaskbar import Taskbar

#初始化
#判断环境是exe还是py
if getattr(sys, 'frozen', False):
    server_lujin = os.path.dirname(sys.executable)
else:
    server_lujin = os.path.dirname(os.path.abspath(__file__))
#压缩日志
log_file = "last.log" 
app_file = os.path.basename(sys.argv[0])
zip_file_name = time.strftime("%Y_%m_%d_%H_%M_%S") + ".zip"  
if os.path.exists(f"{server_lujin}{os.sep}log{os.sep}{log_file}"):
    with zipfile.ZipFile(f"{server_lujin}{os.sep}log{os.sep}{zip_file_name}", 'w') as zf:
        zf.write(f"{server_lujin}{os.sep}log{os.sep}{log_file}", arcname=log_file)
else:
    os.makedirs(f"{server_lujin}{os.sep}log", exist_ok=True)
    with open(f"{server_lujin}{os.sep}log{os.sep}{log_file}", "w") as f:
        f.write("")
log_file_name = (f"{server_lujin}{os.sep}log{os.sep}{log_file}")

app = Flask(__name__)
CORS(app)

# 全局锁
device_lock = threading.Lock()
class flask_api_web():
    @app.before_request
    def check_headers():
        if request.method != "OPTIONS":
            required_headers = {
                'Authorization': 'i am Han Han', 
            }

            for header, value in required_headers.items():
                if header not in request.headers or request.headers[header] != value:
                    response = {
                        "error": "不允许你访问",
                        "message": f"禁止你访问此内容"
                    }
                    return jsonify(response), 401  # Unauthorized status code


    @app.route('/hello', methods=['GET'])
    def hello():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nrong = (f"【{current_time}】\n[控制台]: 设备 {client_ip} 进行访问hello\n")
        print(nrong)
        with open(f"{server_lujin}{os.sep}log{os.sep}{log_file}", "a", encoding="utf-8") as f:
            f.write(nrong)

        response = {
            "title": "欢迎连接至终端",
            "execution_time": current_time,
            "success": True
        }
        return jsonify(response)

    @app.route('/orderlist', methods=['POST'])
    def orderlist():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        json_data = request.get_json()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"【{current_time}】\n[控制台]: 设备 {client_ip} 询问链接")
        print("JSON 数据:", json_data)
        
        verify_result = PPowerShell.verify_device(json_data, device_lock)
        if verify_result is not True:
            return verify_result

        current_directory = server_lujin
        json_file_path = os.path.join(current_directory, "data", "orderlist.json")
        try:
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                response = json.load(json_file)
                return jsonify(response)
        except FileNotFoundError:
            print("文件不存在")
            return None
        except json.JSONDecodeError:
            print("JSON解码错误")
            return None

    @app.route('/command', methods=['POST'])
    def run_command_zdy():
        client_ip = request.remote_addr
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_data = request.get_json()

        print(f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令 【自定义命令】")
        print("JSON 数据:", json_data)

        nrong = f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令 【自定义命令】\nJSON 数据: {json_data}\n"
        with open(log_file_name, "a", encoding="utf-8") as f:
            f.write(nrong)

        verify_result = PPowerShell.verify_device(json_data, device_lock)
        if verify_result is not True:
            return verify_result

        if json_data.get("name") == "han han":
            data_command = json_data.get("command")
            app_files = os.listdir(f"{server_lujin}{os.sep}app")
            for file in app_files:
                if file in data_command:
                    absolute_path = os.path.join(f"{server_lujin}//app", file)
                    data_command = data_command.replace(file, absolute_path)
                    print("【控制台】发现命令的程序存在于[app/目录]中，将强行使用 [app/目录]中的程序作为程序源")

            if json_data.get("value") is not None:
                data_value = json_data.get("value")
                def data_intstat(data_command, data_value):
                    if "nircmd.exe setsysvolume" in data_command:
                        volume = int(data_value)
                        converted_value = int(volume * 655.35)
                        data_command = data_command.replace('{value}', str(converted_value))
                        return data_command
                    else:
                        formatted_command = data_command.replace('{value}', str(data_value))
                        return formatted_command
                data_command = data_intstat(data_command, data_value)
            
            try:
                output = subprocess.check_output(data_command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
                cmd_back = output
            except subprocess.CalledProcessError as e:
                cmd_back = e.output
            if cmd_back == '':
                cmd_back = "命令成功发出\n返回结果为空"
        else:
            cmd_back = ""

        response = {
            "title": "命令返回状态",
            "execution_time": current_time,
            "success": True,
            "cmd_back": cmd_back
        }
        return jsonify(response)
     
class Basics():
    def run_socket(host, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind((host, port))
        except:
            messagebox.showinfo("控制终端核心", f"Flask 服务 无法启动 \n未开放或被占用")  
            os._exit(0)
        server_socket.listen(20)
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                current_time = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
                print(f"【{current_time}】\n已被设备 {client_address} 发现\n")
                client_socket.close()
        except KeyboardInterrupt:
            pass
        finally:
            server_socket.close()
    #新增
    def add_to_startup(app_name, app_path):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(reg_key)
        
    def load_device_config():
        with open(f'{server_lujin}{os.sep}data{os.sep}Devices.json', 'r', encoding='utf-8') as file:
            return json.load(file)
        
if __name__ == '__main__':
    print("------------------------------\n")
    print("涵的涵涵的控制终端核心")
    print("------------------------------")

    host = '0.0.0.0'
    port = 5201
    #判断是否缺失文件
    PPowerShell.check_files_and_dirs()

    #格式化文件，并实时检测ip地址是否变化，变化则根据新地址格式化文件

    #-----------------------实时检测地址是否变化-----------------------
    

    app_name = "涵的控制终端"
    #是否第一次启动 设置第一次启动自行开启开机启动
    if os.path.exists(f"{server_lujin}/data/one"):
        pass
    else:
        with open(f"{server_lujin}/data/one", "w") as file:
            pass
        Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}{os.sep}{app_file}")
    print(f"{server_lujin}{os.sep}{app_file}")

    #-----------------------Windows 小任务栏
    print("启动 Windows 小任务栏应用")
    Taskbar_start = Taskbar(server_lujin, app_name, app_file, PPowerShell.get_ipv4_now(), port)
    serve_windows_mix_icon_duoxianc = threading.Thread(target=Taskbar_start.chushihua)
    serve_windows_mix_icon_duoxianc.daemon = True
    serve_windows_mix_icon_duoxianc.start()

    #-----------------------实时检测地址是否变化-----------------------
    check_ipv4_Dynamic_state_duoxiancheng = threading.Thread(target=PPowerShell.check_ipv4_Dynamic_state, args=(port,Taskbar_start,))
    check_ipv4_Dynamic_state_duoxiancheng.daemon = True
    check_ipv4_Dynamic_state_duoxiancheng.start()

    #-----------------------开放检测到的端口-----------------------
    socket_thread = threading.Thread(target=Basics.run_socket, args=(host, port))
    socket_thread.daemon = True
    socket_thread.start()
    #-----------------------开放检测到的端口-----------------------
    
    #messagebox.showinfo("涵涵的控制终端核心", f"\n涵涵的控制终端核心 已成功启动 当前地址：{host}:{port}/{port+1}")  
    try:
        print(f"\n涵涵的控制终端核心 已成功启动 当前地址：{PPowerShell.get_ipv4_now()}:{port}/{port+1}")
        serve(app, host=host, port=port + 1)
    except:
        print(f"Flask 服务 无法启动 端口：{port}:{port + 1} 未开放或被占用")
        messagebox.showinfo("涵涵的控制终端核心", f"Flask 服务 无法启动 端口：{port}:{port + 1} 未开放或被占用")  
        os._exit(0)

    

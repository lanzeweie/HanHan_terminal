from waitress import serve
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime,socket,threading,json,sys,os,subprocess,winreg
from Localcommand import windows_command
import time  
import zipfile
# 任务栏小图标
from tkinter import messagebox  
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
if os.path.exists(f"{server_lujin}\log\{log_file}"):
    with zipfile.ZipFile(f"{server_lujin}\log\{zip_file_name}", 'w') as zf:
        zf.write(f"{server_lujin}\log\{log_file}")
else:
    with open(f"{server_lujin}\log\{log_file}", "w") as f:
        f.write("")
log_file_name = (f"{server_lujin}\log\{log_file}")

def file_json_geshihua(ipv4,port):
    #格式化dataj json数据，设置为当机地址
    #----------历史屎坑--------如果去除它则无法运行
    get_ipv4_address()
    #----------历史屎坑--------如果去除它则无法运行
    with open(f'{server_lujin}\data\orderlist.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    for item in data:
        if item['guding'] == 'n':
            url_parts = item['apiUrl'].split('//')
            if len(url_parts) > 1:
                address = url_parts[1].split('/')[0]
                formatted_address = address.replace(address, f'{ipv4}:{port+1}')
                item['apiUrl'] = item['apiUrl'].replace(address, formatted_address)

    with open(f'{server_lujin}\data\orderlist.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    print("读取了配置文件")

def check_files_and_dirs():
    files_and_dirs = [f"{server_lujin}/data"]
    for item in files_and_dirs:  
        if os.path.exists(item):  
            pass  
        else:  
            print(f"缺失{item}")
            messagebox.showinfo("涵涵的控制终端核心", f"缺失{item}")  
            os._exit()
    print("\n环境已检查：正常")


#--------------------------------屎坑 删除则无法运行 不知道作用-----------------------
def get_ipv4_address():  
    ip_address = None  
    output = subprocess.check_output('ipconfig', shell=True).decode('gbk')  
    wireless_ip_address = get_ip_address(output, 'Wireless LAN adapter')  
    if wireless_ip_address:  
        return wireless_ip_address  
    ethernet_ip_address = get_ip_address(output, 'Ethernet adapter')  
    if ethernet_ip_address:  
        return ethernet_ip_address  
    any_ip_address = get_any_ip_address(output, '192.168')  
    if any_ip_address:  
        return any_ip_address  
    any_ip_address = get_any_ip_address(output)  
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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip_address = s.getsockname()[0]
        s.close()
    except socket.error:
        pass
    return ip_address

def check_ipv4_Dynamic_state(port):
    previous_address = None
    while True:
        current_address = get_ipv4_now()
        if current_address and current_address != previous_address:
            print("IPv4 地址发生变化：", current_address)
            previous_address = current_address
            #更改json地址
            file_json_geshihua(current_address,port)
            #更改Windows小任务栏的地址
            Taskbar_start.icon_dongtai(current_address,port)
        time.sleep(20)

app = Flask(__name__)
CORS(app)

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
        with open(f"{server_lujin}\log\{log_file}", "a", encoding="utf-8") as f:
            f.write(nrong)

        response = {
            "title": "欢迎连接至终端",
            "execution_time": current_time,
            "success": True
        }
        return jsonify(response)

    @app.route('/orderlist', methods=['GET'])
    def orderlist():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        print (client_ip)
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
    
    @app.route('/stop', methods=['GET'])
    def run_stop():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nrong = (f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起关机命令\n")
        print(nrong)
        with open(log_file_name, "a", encoding="utf-8") as f:
            f.write(nrong)
        windows_command.shutdonw()
        response = {
            "title": "命令返回状态",
            "execution_time": current_time,
            "success": True
        }
        return jsonify(response)

    @app.route('/suoping', methods=['GET'])
    def run_suoping():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nrong = (f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起锁屏命令\n")
        print(nrong)
        with open(log_file_name, "a", encoding="utf-8") as f:
            f.write(nrong)
        windows_command.suoping()
        response = {
            "title": "命令返回状态",
            "execution_time": current_time,
            "success": True
        }
        return jsonify(response)

    @app.route('/command', methods=['POST'])
    def run_commandhh():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        json_data = request.get_json()  # 获取请求中的 JSON 数据

        # 打印 JSON 内容和时间
        print(f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令hh")
        print("JSON 数据:", json_data)

        nrong = f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起命令hh\nJSON 数据: {json_data}\n"
        with open(log_file_name, "a", encoding="utf-8") as f:
            f.write(nrong)

        # 检查 name 字段是否为 "han han"，提取 data 字段的值
        if json_data.get("name") == "han han":
            data_value = json_data.get("command")
            print("data 值:", data_value)

            # 执行命令hh的逻辑
            try:
                output = subprocess.check_output(data_value, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
                print("命令执行结果:", output)
                cmd_back = output
            except subprocess.CalledProcessError as e:
                print("命令执行出错:", e.output)
                cmd_back = e.output
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

if __name__ == '__main__':
    print("------------------------------\n")
    print("涵的涵涵的控制终端核心")
    print("------------------------------")

    host = '0.0.0.0'
    port = 5201
    #判断是否缺失文件
    check_files_and_dirs()

    #格式化文件，并实时检测ip地址是否变化，变化则根据新地址格式化文件
    #-----------------------实时检测地址是否变化-----------------------
    check_ipv4_Dynamic_state_duoxiancheng = threading.Thread(target=check_ipv4_Dynamic_state, args=(port,))
    check_ipv4_Dynamic_state_duoxiancheng.daemon = True
    check_ipv4_Dynamic_state_duoxiancheng.start()
    #-----------------------实时检测地址是否变化-----------------------
    

    app_name = "涵的控制终端"
    #是否第一次启动 设置第一次启动自行开启开机启动
    if os.path.exists(f"{server_lujin}/data/one"):
        pass
    else:
        with open(f"{server_lujin}/data/one", "w") as file:
            pass
        Taskbar.command_bootup_menu_add_to_startup(app_name, f"{server_lujin}\{app_file}")
    print(f"{server_lujin}\{app_file}")

    #-----------------------Windows 小任务栏
    print("启动 Windows 小任务栏应用")
    Taskbar_start = Taskbar(server_lujin, app_name, app_file, get_ipv4_now(), port)
    serve_windows_mix_icon_duoxianc = threading.Thread(target=Taskbar_start.chushihua)
    serve_windows_mix_icon_duoxianc.daemon = True
    serve_windows_mix_icon_duoxianc.start()
    #-----------------------Windows 小任务栏

    #-----------------------开放检测到的端口-----------------------
    socket_thread = threading.Thread(target=Basics.run_socket, args=(host, port))
    socket_thread.daemon = True
    socket_thread.start()
    #-----------------------开放检测到的端口-----------------------
    
    #messagebox.showinfo("涵涵的控制终端核心", f"\n涵涵的控制终端核心 已成功启动 当前地址：{host}:{port}/{port+1}")  
    try:
        print(f"\n涵涵的控制终端核心 已成功启动 当前地址：{get_ipv4_now()}:{port}/{port+1}")
        serve(app, host=host, port=port + 1)
    except:
        print(f"Flask 服务 无法启动 端口：{port}:{port + 1} 未开放或被占用")
        messagebox.showinfo("涵涵的控制终端核心", f"Flask 服务 无法启动 端口：{port}:{port + 1} 未开放或被占用")  
        os._exit(0)

    
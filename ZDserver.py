from waitress import serve
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime,socket,threading,json,sys,os,subprocess,winreg
from bendi import windows_command
import time  
import zipfile
# 任务栏小图标
import pystray  
from PIL import Image  
from tkinter import messagebox  
import tkinter as tk

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

def file_json_geshihua(port):
    #格式化dataj json数据，设置为当机地址
    ipv4_ip = get_ipv4_address()
    with open(f'{server_lujin}\data\orderlist.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    for item in data:
        if item['guding'] == 'n':
            url_parts = item['apiUrl'].split('//')
            if len(url_parts) > 1:
                address = url_parts[1].split('/')[0]
                formatted_address = address.replace(address, f'{ipv4_ip}:{port+1}')
                item['apiUrl'] = item['apiUrl'].replace(address, formatted_address)

    with open(f'{server_lujin}\data\orderlist.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    print("已读取配置文件")

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

def get_ipv4_bianhua():
    ip_address = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip_address = s.getsockname()[0]
        s.close()
    except socket.error:
        pass
    return ip_address

def check_ipv4_bianhua(port):
    previous_address = None
    while True:
        current_address = get_ipv4_bianhua()
        if current_address and current_address != previous_address:
            print("IPv4 地址发生变化：", current_address)
            previous_address = current_address
            file_json_geshihua(port)

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

    @app.route('/lanping', methods=['GET'])
    def run_lanping():
        client_ip = request.remote_addr  # 获取客户端的 IP 地址
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nrong = (f"【{current_time}】\n[控制台]: 设备 {client_ip} 发起蓝屏命令")
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

    def windowsn_xiaocx():
        serve_windows_mix_icon.run()
    def windows_exit():
        serve_windows_mix_icon.stop()
        os._exit(0)
    def open_current_directory():
        current_directory = server_lujin
        os.startfile(current_directory)
    #新增
    def add_to_startup(app_name, app_path):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)
        winreg.CloseKey(reg_key)
    #删除
    def remove_from_startup(app_name):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(reg_key, app_name)
            print("已删除开机自启")
        except FileNotFoundError:
            print(f"启动项中不存在应用程序: {app_name}")
        winreg.CloseKey(reg_key)
    #查询
    def check_startup(app_name):
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(reg_key, app_name)
            print(f"应用程序 {app_name} 已添加到启动项中")
            return "surr"
        except FileNotFoundError:
            print(f"应用程序 {app_name} 未添加到启动项中")
        winreg.CloseKey(reg_key)
        return "null"
    #开启开启自启或关闭
    def startup_shifouqidong(app_name, app_path):
        if Basics.check_startup(app_name) == "surr":
            Basics.remove_from_startup(app_name)
        elif Basics.check_startup(app_name) == "null":
            Basics.add_to_startup(app_name, app_path)
        os._exit(0)
    #设备名 通过 orderlist 的第一个元素的 title 获得
    def shebei_name():
        with open(f'{server_lujin}\data\orderlist.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        title = data[0]['title']
        return title
    #修改设备名
    def shebei_name_xiugai():
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
                messagebox.showinfo("涵涵的控制终端", "需要手动重新启动")
                os._exit(0)

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

    def zdyml_menu():
        if not os.path.exists(f"{server_lujin}/Custom_command_editor.exe"):
            if not os.path.exists(f"{server_lujin}/app/Custom_command_editor.exe"):
                messagebox.showinfo("终端命令编辑器", "应用程序不存在，请勿删除自带文件")
                return "not"
            else:
                Custom_command_editor_start = subprocess.Popen(f'{server_lujin}/app/Custom_command_editor.exe', shell=True)
        else:
            Custom_command_editor_start = subprocess.Popen(f'{server_lujin}/Custom_command_editor.exe', shell=True)

if __name__ == '__main__':
    print("------------------------------\n")
    print("涵的涵涵的控制终端核心")
    print("------------------------------")

    host = '0.0.0.0'
    port = 5201
    #判断是否缺失文件
    check_files_and_dirs()

    #格式化文件，并实时检测ip地址是否变化，变化则根据新地址格式化文件
    check_ipv4_bianhua_duoxiancheng = threading.Thread(target=check_ipv4_bianhua, args=(port,))
    check_ipv4_bianhua_duoxiancheng.daemon = True
    check_ipv4_bianhua_duoxiancheng.start()
    

    app_name = "涵的控制终端"
    #是否第一次启动 第一次启动自行开启开机启动
    if os.path.exists(f"{server_lujin}/data/one"):
        pass
    else:
        with open(f"{server_lujin}/data/one", "w") as file:
            pass
        Basics.add_to_startup(app_name, f"{server_lujin}\{app_file}")
    print(f"{server_lujin}\{app_file}")
    startup_wenbenzhi = Basics.check_startup(app_name)
    if startup_wenbenzhi == "surr":
        startup_wenbenzhi_wenben = "开机启动[√] 修改需重新启动"
    elif startup_wenbenzhi == "null":
        startup_wenbenzhi_wenben = "开机启动[×] 修改需重新启动"
    image = Image.open(f"{server_lujin}/data/zhou.png")  # 替换为自己的图标文件路径  
    shebeiname = Basics.shebei_name()
    menu = (
        pystray.MenuItem(f"当前设备：{shebeiname}", lambda item: Basics.shebei_name_xiugai()),  
        pystray.MenuItem(f"自定义命令菜单", lambda item: Basics.zdyml_menu()),  
        pystray.MenuItem(startup_wenbenzhi_wenben, lambda item: Basics.startup_shifouqidong(app_name, f"{server_lujin}\{app_file}")),   
        pystray.MenuItem("打开目录", lambda item: Basics.open_current_directory()),   
        pystray.MenuItem("退出", lambda item: Basics.windows_exit()),  
    ) 
    serve_windows_mix_icon = pystray.Icon("name", image, f"终端服务\n地址：{get_ipv4_bianhua()}\n已激活服务，端口：{get_ipv4_bianhua()}/{port+1}", menu)  
    serve_windows_mix_icon_duoxianc = threading.Thread(target=Basics.windowsn_xiaocx)
    serve_windows_mix_icon_duoxianc.daemon = True
    serve_windows_mix_icon_duoxianc.start()

    socket_thread = threading.Thread(target=Basics.run_socket, args=(host, port))
    socket_thread.daemon = True
    socket_thread.start()
    
    #messagebox.showinfo("涵涵的控制终端核心", f"\n涵涵的控制终端核心 已成功启动 当前地址：{host}:{port}/{port+1}")  
    try:
        print(f"\n涵涵的控制终端核心 已成功启动 当前地址：{get_ipv4_bianhua()}:{port}/{port+1}")
        serve(app, host=host, port=port + 1)
    except:
        print(f"Flask 服务 无法启动 地址：{get_ipv4_bianhua()}:{port + 1} 未开放或被占用")
        messagebox.showinfo("涵涵的控制终端核心", f"Flask 服务 无法启动 地址：{get_ipv4_bianhua()}:{port + 1} 未开放或被占用")  
        os._exit(0)

    
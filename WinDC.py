#调用 Windows PowerShell
import json
import os
import socket
import subprocess
import sys
import time
from tkinter import messagebox

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
        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'r', encoding='utf-8') as file:
            data = json.load(file)
        for item in data:
            if item['title'] == '音量控制':
                Audio_value = PPowerShell.ps1_get('AudioVolume')
                if Audio_value is not None:
                    Audio_value_True = float(Audio_value) * 100
                    item['value'] = int(Audio_value_True)
                    with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                        json.dump(data, file, indent=2, ensure_ascii=False)
            if item['title'] == '亮度控制':
                Audio_value = PPowerShell.ps1_get('AudioBrightnes')
                try:
                    if Audio_value is not None:
                        Audio_value_True = Audio_value
                        item['value'] = int(Audio_value_True)
                        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                            json.dump(data, file, indent=2, ensure_ascii=False)      
                except:
                    if Audio_value is not None:
                        Audio_value_True = Audio_value[0]
                        item['value'] = int(Audio_value_True)
                        with open(f'{server_lujin}{os.sep}{config_orderlist}', 'w', encoding='utf-8') as file:
                            json.dump(data, file, indent=2, ensure_ascii=False)   
    def file_json_geshihua(ipv4,port):
        #格式化dataj json数据，设置为当机地址
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
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip_address = s.getsockname()[0]
            s.close()
        except socket.error:
            pass
        return ip_address

    def check_ipv4_Dynamic_state(port,Taskbar_start):
        previous_address = None
        while True:
            current_address = PPowerShell.get_ipv4_now()
            if current_address and current_address != previous_address:
                print("IPv4 地址发生变化：", current_address)
                previous_address = current_address
                #更改json地址
                PPowerShell.file_json_geshihua(current_address,port)
                #更改Windows小任务栏的地址
                Taskbar_start.icon_dongtai(current_address,port)
                #首先检查是否有 “音量控制、亮度控制” json配置信息，如果有则调用 Windows PowerShell 来查询数值并更新到配置文件中
            PPowerShell.file_json_Audio()
            time.sleep(20)

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

if __name__ == "__main__":
    print(PPowerShell.file_json_Audio())

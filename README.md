# 涵涵的超级控制终端   
一个 **局域网的懒人快捷操控执行远程命令助手**    
设计的理由也很简单，"懒😊"
由于移动端确实非常方便，简简单单的交互就可以了，所以因为 "懒" 诞生了此项目  
当前项目是 服务端   
**移动端：**  [涵涵的超级控制面板——客户端(安卓移动端)](https://github.com/lanzeweie/HanHan)    

## 简介
此项目是服务端终端用于创建终端服务，接受客户端(安卓移动端)的命令，对接客户端(安卓移动端)面板  
**设计方法：** 使用 服务端创建API服务，客户端(安卓移动端)来访问API进行交互，以此快捷执行命令   
**功能概述：** 可以自定义执行cmd命令，自定义执行其他API链接(支持Get、Post)    

## 使用截图
![界面1](./png/1.png)
![界面2](./png/2.png)
![界面3](./png/3.png)
## Windows exe 使用
下载发布的稳定版本     
解压-启动 `ZDserver.exe`    

## Python py 使用
**安装库**    
`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**启动**      请先用终端进入当前目录   
默认使用 端口 _5201_ 与 _5202_   
端口 _5201_ 用于被移动端发现  _5202_ 用于开放API服务  
`python ZDserver.py`  

在右下角小任务栏找到此程序右键操作即可  

**注意**    
在小任务栏程序右键选项快捷编辑命令，只能打开 Custom_command_editor.py已经打包成Custom_command_editor.exe   
可以选则手动启动   
`python ./app/Custom_command_editor.py`     

## 注意事项      
此控制终端需要对应的客户端(安卓移动端)支持，不支持普通的浏览器访问    
[涵涵的超级控制面板——客户端(安卓移动端)](https://github.com/lanzeweie/HanHan)   
程序第一次启动会把自己设置为开机自启，在小任务栏关闭即可（只有第一次启动会设置为开机自启）   
 
## 项目目录结构
./涵涵的超级控制终端    
├── data/                 --数据    
│   ├── orderlist.json    --功能配置     
│   └── zhou.png          --图标   
├── log/                  --日志    
│   └── last.log          --当前日志，会自动打包上一次的日志     
├── app/                  --一些可用上的辅助程序         
│   └── Custom_command_editor.py          --快捷API链接编辑器      
│   └── AudioBrightnes.ps1 --powershell的ps1脚本 用于查询屏幕亮度
│   └── AudioVolume.ps1   --powershell的ps1脚本 用于查询系统声音
│   └── nircmd.exe        --nircmd.exe windows设置快捷命令
├── requirements.txt      --所需库      
├── REMDAD.md     
├── WinDC.py              --底层基层命令    
├── ZDserver.py           --服务端主程序          
├── WinTaskbar.py         --在Windows的小任务栏-由主程序调用    
├── .gitignore   


## 缺陷  
安全性很低，只使用 windows 系统

## 打包
使用 `pyinstaller` 打包成exe即可，注意需要保持程序位置不变  

# 涵涵的超级控制终端   外部程序


├── app/                  --一些可用上的辅助程序         
│   ├── volume_control.cpp          --支持Win7-Win11亮度调节 
│   └── Custom_command_editor.py     --快捷命令菜单编辑器  

## 为什么用音量调节
在系统开发过程中，为避免COM组件调用过程中可能引发的全局崩溃问题，原本考虑使用CoInitialize来初始化COM库以确保线程安全。然而，在实际应用中发现，即便正确调用了CoInitialize，由于COM对象本身的不稳定性以及异常处理机制的局限性，依然存在因亮度控制等操作导致整个应用程序崩溃的风险。因此，最终决定放弃依赖CoInitialize的方式，转而采用更为稳定的多进程隔离方案，从根本上将COM相关操作与主程序分离，从而提升系统的健壮性和可靠性。

python写肯定是不可以的，一个小小的功能，体积必须精简，所以考虑C++来写，功能也只有调节音量、获得音量

使用cl/g++打包  大小 g++ 150kb  cl 100kb，功能仅音量控制 传出json
>g++ -o volume_control.exe volume_control.cpp -lole32 -luser32 -luuid -lwinmm -mconsole -DUNICODE -D_UNICODE
>cl vo.cpp /O1 /GR- /GS- /EHs-c- /DNDEBUG /DWIN32_LEAN_AND_MEAN /link /OUT:volume_control_tiny.exe /SUBSYSTEM:CONSOLE /OPT:REF /OPT:ICF /RELEASE ole32.lib user32.lib shell32.lib advapi32.lib
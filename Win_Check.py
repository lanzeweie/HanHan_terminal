import os
import sys


def check_required_files(server_lujin):
    # 如果是python源码环境则跳过检查
    if not getattr(sys, 'frozen', False):
        return

    app_dir = os.path.join(server_lujin, "app")
    required_files = [
        os.path.join(app_dir, "volume_control.exe"),
        os.path.join(app_dir, "Custom_command_editor.exe")
    ]
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        msg = "缺少以下关键文件:\n" + "\n".join(missing)
        print(msg)
        try:
            import tkinter
            from tkinter import messagebox
            tkinter.Tk().withdraw()
            messagebox.showerror("依赖缺失", msg)
        except Exception:
            pass
        sys.exit(1)

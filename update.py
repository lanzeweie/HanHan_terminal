import json
import tkinter as tk
import webbrowser
from itertools import zip_longest
from tkinter import scrolledtext

import requests
from PIL import Image, ImageTk


class UpdateWindow:
    def __init__(self, version, source, release_notes, is_latest=False):
        self.root = tk.Tk()
        self.root.title("软件更新")
        
        # 窗口居中显示
        window_width = 500
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置窗口图标
        try:
            icon = tk.PhotoImage(file="data/zhou.png")
            self.root.iconphoto(False, icon)
        except tk.TclError:
            print("图标文件加载失败，确保路径正确且文件存在。")
        
        # 版本信息框架
        version_frame = tk.Frame(self.root)
        version_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if is_latest:
            version_label = tk.Label(version_frame, text=f"当前已是最新版本 (v{version})", font=("Arial", 12, "bold"))
        else:
            version_label = tk.Label(version_frame, text=f"发现新版本 (v{version})!", font=("Arial", 12, "bold"))
        version_label.pack(side=tk.LEFT)
        
        source_label = tk.Label(version_frame, text=f"来源：{source}", font=("Arial", 10))
        source_label.pack(side=tk.RIGHT)
        
        # 分隔线
        separator = tk.Frame(self.root, height=1, bg="gray")
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # 更新内容标题
        notes_title = tk.Label(self.root, text="版本内容：", font=("Arial", 11))
        notes_title.pack(anchor=tk.W, padx=10)
        
        # 更新内容文本框（可滚动）
        self.notes_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=12)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.notes_text.insert(tk.END, release_notes)
        self.notes_text.config(state=tk.DISABLED)  # 设置为只读
        
        # 只有在发现新版本时才显示下载链接
        if not is_latest:
            # 下载链接框架
            download_frame = tk.Frame(self.root)
            download_frame.pack(fill=tk.X, padx=10, pady=5)
            
            download_label = tk.Label(download_frame, text="选择下载链接：", font=("Arial", 11))
            download_label.pack(anchor=tk.W)
            
            # 下载按钮框架
            button_style = {"font": ("Arial", 11), "bg": "#007AFF", "fg": "white", "relief": "flat", "bd": 0, "padx": 10, "pady": 5, "cursor": "hand2"}
            
            links_frame = tk.Frame(self.root)
            links_frame.pack(fill=tk.X, padx=10, pady=5)
            
            github_button = tk.Button(links_frame, text="GitHub", command=lambda: webbrowser.open("https://github.com/lanzeweie/HanHan_terminal/releases"), **button_style)
            github_button.pack(side=tk.LEFT, padx=(0, 5))
            
            gitee_button = tk.Button(links_frame, text="Gitee", command=lambda: webbrowser.open("https://gitee.com/buxiangqumingzi/han-han_terminal/releases"), **button_style)
            gitee_button.pack(side=tk.LEFT, padx=5)
            
            lanzou_button = tk.Button(links_frame, text="蓝奏云[1xw0]", command=lambda: webbrowser.open("https://wwpp.lanzouv.com/b0foy1bkb"), **button_style)
            lanzou_button.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮框架
        close_frame = tk.Frame(self.root)
        close_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.close_button = tk.Button(
            close_frame, text="关闭", width=10, command=self.root.destroy,
            font=("Arial", 11), bg="#E0E0E0", relief="flat"
        )
        self.close_button.pack(side=tk.RIGHT, padx=5)

    def show(self):
        self.root.mainloop()


class VersionChecker:
    GITHUB_RELEASES_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
    GITEE_RELEASES_URL = "https://gitee.com/api/v5/repos/{owner}/{repo}/releases/latest?access_token={access_token}"
    GITHUB_OWNER = "lanzeweie"
    GITHUB_REPO = "HanHan_terminal"
    GITEE_OWNER = "buxiangqumingzi"
    GITEE_REPO = "han-han_terminal"
    CURRENT_VERSION = "2.2.2"
    TIMEOUT = 0.5

    def __init__(self):
        self.github_owner = self.GITHUB_OWNER
        self.github_repo = self.GITHUB_REPO
        self.gitee_owner = self.GITEE_OWNER
        self.gitee_repo = self.GITEE_REPO
        self.current_version = self.CURRENT_VERSION
        self.access_token = "10ca1c7562fd92a87c3205d7af8ba01d"  # Your access token

    def fetch_latest_release(self, url):
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            return response.json() if response.ok else None
        except requests.RequestException:
            return None

    def compare_versions(self, current_version, release_version):
        try:
            current_tuple = tuple(map(int, current_version.split(".")))
            release_tuple = tuple(map(int, release_version.split(".")))
            for a, b in zip_longest(current_tuple, release_tuple, fillvalue=0):
                if a != b:
                    return a > b
            return True
        except ValueError:
            return False
            
    def show_current_version_info(self):
        """显示当前版本信息，即使是最新版本"""
        # 尝试从GitHub或Gitee获取当前版本的信息
        github_url = self.GITHUB_RELEASES_URL.format(
            owner=self.github_owner, repo=self.github_repo
        )
        latest_release = self.fetch_latest_release(github_url)
        source = "GitHub"

        if not latest_release:
            gitee_url = self.GITEE_RELEASES_URL.format(
                owner=self.gitee_owner,
                repo=self.gitee_repo,
                access_token=self.access_token,
            )
            latest_release = self.fetch_latest_release(gitee_url)
            source = "Gitee"

        if latest_release:
            release_version = latest_release["tag_name"].lstrip("v")
            release_notes = latest_release.get("body", "暂无版本内容")
            # 显示当前版本信息窗口
            is_latest = self.compare_versions(self.current_version, release_version)
            if is_latest:
                # 显示当前版本信息（已是最新版本）
                update_window = UpdateWindow(self.current_version, source, release_notes, is_latest=True)
                update_window.show()
            return True
        else:
            # 如果无法连接到GitHub或Gitee，显示简单的版本信息
            update_window = UpdateWindow(
                self.current_version, 
                "本地", 
                "无法连接到网络获取详细版本信息。\n当前版本：v" + self.current_version, 
                is_latest=True
            )
            update_window.show()
            return True

    def check_for_updates(self):
        github_url = self.GITHUB_RELEASES_URL.format(
            owner=self.github_owner, repo=self.github_repo
        )
        latest_release = self.fetch_latest_release(github_url)
        source = "GitHub"

        if not latest_release:
            gitee_url = self.GITEE_RELEASES_URL.format(
                owner=self.gitee_owner,
                repo=self.gitee_repo,
                access_token=self.access_token,
            )
            latest_release = self.fetch_latest_release(gitee_url)
            source = "Gitee"

        if latest_release:
            release_version = latest_release["tag_name"].lstrip("v")
            if not self.compare_versions(self.current_version, release_version):
                print(f"发现新版本(v{release_version})！来源：{source}")
                # 使用窗口显示更新内容和下载链接
                release_notes = latest_release.get("body", "暂无更新内容")
                update_window = UpdateWindow(release_version, source, release_notes)
                update_window.show()
                return False
            else:
                print("当前已是最新版本。")
                # 显示当前版本信息
                self.show_current_version_info()
                return True
        else:
            print("网络错误，无法访问GitHub或Gitee Release API。")
            # 显示无法连接的信息
            self.show_current_version_info()
            return True


if __name__ == "__main__":
    checker = VersionChecker()
    checker.check_for_updates()

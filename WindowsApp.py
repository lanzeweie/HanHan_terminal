"""
Windows应用检测和处理模块
用于检测WindowsApp应用并提供相应的功能适配
"""
import os
import sys


class WindowsAppDetector:
    """Windows应用检测器"""

    def __init__(self, app_path=None):
        """
        初始化Windows应用检测器

        Args:
            app_path (str, optional): 应用程序路径。如果未提供，将自动检测
        """
        self.app_path = app_path or self._get_app_path()
        self._is_windows_store_app = None

    def _get_app_path(self):
        """获取应用程序路径"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(sys.argv[0]))

    def is_windows_store_app(self):
        """
        检测是否为WindowsApp应用

        Returns:
            bool: True表示是WindowsApp应用，False表示是普通应用
        """
        if self._is_windows_store_app is None:
            self._is_windows_store_app = "WindowsApps" in self.app_path
            self._print_detection_result()
        return self._is_windows_store_app

    def _print_detection_result(self):
        """打印检测结果"""
        if self._is_windows_store_app:
            print("检测到WindowsApp应用路径，禁用日志写入功能")
        else:
            print("检测到正常应用路径，启用日志写入功能")

    def get_safe_directory_path(self, default_path=None):
        """
        获取安全的目录路径
        对于WindowsApp应用，返回Documents目录
        对于普通应用，返回原始路径

        Args:
            default_path (str, optional): 默认路径，如果未提供则使用app_path

        Returns:
            str: 安全的目录路径
        """
        if not self.is_windows_store_app():
            return default_path or self.app_path

        # WindowsApp应用返回Documents目录
        try:
            import os.path
            documents_dir = os.path.join(os.path.expanduser("~"), "Documents")
            return documents_dir
        except Exception:
            # 如果获取Documents目录失败，返回用户主目录
            return os.path.expanduser("~")

    def can_write_logs(self):
        """
        检查是否可以写入日志文件

        Returns:
            bool: True表示可以写入日志，False表示禁用日志写入
        """
        return not self.is_windows_store_app()

    def get_log_file_path(self, log_dir="log", log_file="last.log"):
        """
        获取日志文件路径
        对于WindowsApp应用返回None（禁用日志）

        Args:
            log_dir (str): 日志目录名
            log_file (str): 日志文件名

        Returns:
            str or None: 日志文件的完整路径，WindowsApp应用返回None
        """
        if not self.can_write_logs():
            return None

        log_path = os.path.join(self.app_path, log_dir, log_file)
        return log_path

    def setup_logging(self, log_dir="log", log_file="last.log"):
        """
        设置日志系统

        Args:
            log_dir (str): 日志目录名
            log_file (str): 日志文件名

        Returns:
            str or None: 日志文件路径，WindowsApp应用返回None
        """
        if not self.can_write_logs():
            print("WindowsApp应用模式：跳过日志文件创建")
            return None

        # 创建日志目录
        full_log_dir = os.path.join(self.app_path, log_dir)
        os.makedirs(full_log_dir, exist_ok=True)

        # 返回日志文件路径
        log_file_path = os.path.join(full_log_dir, log_file)
        return log_file_path

    def adapt_open_directory_function(self, original_directory):
        """
        适配打开目录功能
        对于WindowsApp应用，将目录路径修改为Documents+"HanHan_ZDserver"目录

        Args:
            original_directory (str): 原始要打开的目录路径

        Returns:
            str: 适配后的目录路径
        """
        if self.is_windows_store_app():
            documents_dir = self.get_safe_directory_path() + os.sep + "HanHan_ZDserver"
            print(f"Windows应用：将打开目录从 {original_directory} 重定向到 {documents_dir}")
            return documents_dir
        return original_directory


# 全局检测器实例
_global_detector = None


def get_detector(app_path=None):
    """
    获取Windows应用检测器实例

    Args:
        app_path (str, optional): 应用程序路径

    Returns:
        WindowsAppDetector: 检测器实例
    """
    global _global_detector
    # 如果提供了特定路径，创建新的检测器实例
    if app_path is not None:
        return WindowsAppDetector(app_path)
    # 否则使用全局实例
    if _global_detector is None:
        _global_detector = WindowsAppDetector()
    return _global_detector


def is_windows_store_app(app_path=None):
    """
    便捷函数：检测是否为WindowsApp应用

    Args:
        app_path (str, optional): 应用程序路径

    Returns:
        bool: True表示是WindowsApp应用
    """
    return get_detector(app_path).is_windows_store_app()


def get_safe_directory_path(default_path=None, app_path=None):
    """
    便捷函数：获取安全的目录路径

    Args:
        default_path (str, optional): 默认路径
        app_path (str, optional): 应用程序路径

    Returns:
        str: 安全的目录路径
    """
    return get_detector(app_path).get_safe_directory_path(default_path)


def setup_logging_for_app(log_dir="log", log_file="last.log", app_path=None):
    """
    便捷函数：为应用设置日志系统

    Args:
        log_dir (str): 日志目录名
        log_file (str): 日志文件名
        app_path (str, optional): 应用程序路径

    Returns:
        str or None: 日志文件路径，WindowsApp应用返回None
    """
    return get_detector(app_path).setup_logging(log_dir, log_file)


class WindowsStartupTaskManager:
    """
    Windows应用启动任务管理器
    对于普通应用使用注册表管理启动任务
    对于WindowsApp应用禁用启动管理功能
    """

    def __init__(self, task_id="涵涵的控制面板"):
        """
        初始化启动任务管理器

        Args:
            task_id (str): 启动任务的ID，默认为"涵涵的控制面板"
        """
        self.task_id = task_id
        self._is_windows_store_app = None

    def _is_windows_app(self):
        """检测是否为WindowsApp应用"""
        if self._is_windows_store_app is None:
            detector = get_detector()
            self._is_windows_store_app = detector.is_windows_store_app()
        return self._is_windows_store_app

    def _get_registry_startup_entry(self):
        """获取注册表中的启动项"""
        import winreg
        try:
            # 打开启动注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_READ)

            # 尝试读取我们的启动项
            try:
                value, _ = winreg.QueryValueEx(key, self.task_id)
                winreg.CloseKey(key)
                return {"path": value, "exists": True}
            except FileNotFoundError:
                winreg.CloseKey(key)
                return {"exists": False}
        except Exception as e:
            print(f"读取注册表失败: {str(e)}")
            return {"exists": False}

    def _set_registry_startup(self, enable=True):
        """设置注册表中的启动项"""
        import winreg
        try:
            # 打开启动注册表项
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE)

            if enable:
                # 获取当前程序路径
                import sys
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = sys.argv[0]

                # 设置启动项
                winreg.SetValueEx(key, self.task_id, 0, winreg.REG_SZ, exe_path)
                print(f"已添加启动项: {self.task_id}")
            else:
                # 删除启动项
                try:
                    winreg.DeleteValue(key, self.task_id)
                    print(f"已删除启动项: {self.task_id}")
                except FileNotFoundError:
                    print(f"启动项不存在: {self.task_id}")

            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"设置注册表失败: {str(e)}")
            return False

    def is_startup_enabled(self):
        """
        检查启动任务是否已启用

        Returns:
            str: "surr"表示已启用，"null"表示未启用或发生错误
        """
        # WindowsApp应用不支持启动管理功能
        if self._is_windows_app():
            print(f"WindowsApp应用不支持启动管理功能: {self.task_id}")
            return "null"

        # 普通应用使用注册表方式
        try:
            startup_entry = self._get_registry_startup_entry()
            if startup_entry.get("exists"):
                print(f"注册表启动任务 {self.task_id} 已启用")
                return "surr"
            else:
                print(f"启动任务 {self.task_id} 未启用")
                return "null"
        except Exception as e:
            print(f"检查启动任务状态时发生错误: {str(e)}")
            return "null"

    def get_startup_menu_name(self):
        """
        获取启动菜单显示名称

        Returns:
            str: 格式化的启动菜单名称
        """
        status = self.is_startup_enabled()
        if status == "surr":
            return "开机启动 【√】"
        else:
            return "开机启动 【X】"

    def enable_startup(self):
        """
        启用启动任务

        Returns:
            bool: True表示成功，False表示失败
        """
        # WindowsApp应用不支持启动管理功能
        if self._is_windows_app():
            print(f"WindowsApp应用不支持启动管理功能: {self.task_id}")
            return False

        # 普通应用使用注册表方式
        return self._set_registry_startup(enable=True)

    def disable_startup(self):
        """
        禁用启动任务

        Returns:
            bool: True表示成功，False表示失败
        """
        # WindowsApp应用不支持启动管理功能
        if self._is_windows_app():
            print(f"WindowsApp应用不支持启动管理功能: {self.task_id}")
            return False

        # 普通应用使用注册表方式
        return self._set_registry_startup(enable=False)

    def toggle_startup(self):
        """
        切换启动任务状态

        Returns:
            bool: True表示操作成功，False表示操作失败
        """
        # WindowsApp应用不支持启动管理功能
        if self._is_windows_app():
            print(f"WindowsApp应用不支持启动管理功能: {self.task_id}")
            return False

        current_status = self.is_startup_enabled()
        if current_status == "surr":
            return self.disable_startup()
        else:
            return self.enable_startup()


# 全局启动任务管理器实例
_global_startup_manager = None


def get_startup_manager(task_id="ZDserver"):
    """
    获取启动任务管理器实例

    Args:
        task_id (str): 启动任务ID，默认为"ZDserver"

    Returns:
        WindowsStartupTaskManager: 启动任务管理器实例
    """
    global _global_startup_manager
    if _global_startup_manager is None:
        _global_startup_manager = WindowsStartupTaskManager(task_id)
    return _global_startup_manager


def is_startup_enabled(task_id="ZDserver"):
    """
    便捷函数：检查启动任务是否已启用

    Args:
        task_id (str): 启动任务ID

    Returns:
        str: "surr"表示已启用，"null"表示未启用
    """
    return get_startup_manager(task_id).is_startup_enabled()


def get_startup_menu_name(task_id="ZDserver"):
    """
    便捷函数：获取启动任务菜单名称

    Args:
        task_id (str): 启动任务ID

    Returns:
        str: 格式化的菜单名称
    """
    return get_startup_manager(task_id).get_startup_menu_name()


def toggle_startup(task_id="ZDserver"):
    """
    便捷函数：切换启动任务状态

    Args:
        task_id (str): 启动任务ID

    Returns:
        bool: True表示操作成功
    """
    return get_startup_manager(task_id).toggle_startup()


# 为了向后兼容，保留旧的函数名
def is_winrt_startup_enabled(task_id="ZDserver"):
    """向后兼容：检查启动任务是否已启用"""
    return is_startup_enabled(task_id)


def get_winrt_startup_menu_name(task_id="ZDserver"):
    """向后兼容：获取启动任务菜单名称"""
    return get_startup_menu_name(task_id)


def toggle_winrt_startup(task_id="ZDserver"):
    """向后兼容：切换启动任务状态"""
    return toggle_startup(task_id)


if __name__ == "__main__":
    # 假定在WindowsApp环境中运行
    # WindowsAppDetector通过路径中是否包含"WindowsApps"来判断
    print("--- 模拟在WindowsApp环境中运行 ---")
    simulated_app_path = "C:\\Program Files\\WindowsApps\\YourApp_1.0.0.0_x64__randomstring\\app.exe"

    # 初始化检测器以模拟环境
    detector = get_detector(app_path=simulated_app_path)

    # 检查并显示安全目录
    safe_path = detector.get_safe_directory_path()
    print(f"安全目录路径: {safe_path}")

    # 检查日志功能状态
    log_path = detector.setup_logging()
    if log_path:
        print(f"日志文件路径: {log_path}")

    print("\n--- 显示启动任务状态 ---")
    # 使用在您项目中指定的任务ID "涵涵的控制面板"
    # 对于WindowsApp应用，启动管理功能被禁用
    startup_manager = WindowsStartupTaskManager(task_id="涵涵的控制面板")

    # 获取格式化后的菜单名称并打印
    menu_name = startup_manager.get_startup_menu_name()
    print(f"启动任务状态菜单显示为: {menu_name}")
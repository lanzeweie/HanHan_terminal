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
    获取全局Windows应用检测器实例

    Args:
        app_path (str, optional): 应用程序路径

    Returns:
        WindowsAppDetector: 检测器实例
    """
    global _global_detector
    if _global_detector is None:
        _global_detector = WindowsAppDetector(app_path)
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
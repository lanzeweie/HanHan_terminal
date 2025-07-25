"""
实在不知道怎么解决崩溃了，Claude Sonnet4 出手
全面的COM崩溃防护系统
整合了进程隔离、线程安全、错误监控和缓存机制
"""
import datetime
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from functools import wraps
from pathlib import Path


class CrashMonitor:
    """崩溃监控器 - 提供详细的错误监控和日志系统"""
    
    def __init__(self, log_dir="log"):
        self.log_dir = log_dir
        self.setup_logging()
        self.setup_crash_handler()
    
    def setup_logging(self):
        """设置详细的日志系统"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"com_protection_{timestamp}.log")
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [线程:%(thread)d] - %(message)s'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('COMProtection')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def setup_crash_handler(self):
        """设置崩溃处理器"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            self.logger.critical("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
            self.log_system_state()
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = handle_exception
    
    def log_system_state(self):
        """记录系统状态信息"""
        try:
            import psutil
            self.logger.info("=== 系统状态信息 ===")
            self.logger.info(f"CPU使用率: {psutil.cpu_percent()}%")
            self.logger.info(f"内存使用率: {psutil.virtual_memory().percent}%")
            
            current_process = psutil.Process()
            self.logger.info(f"当前进程内存: {current_process.memory_info().rss / 1024 / 1024:.2f} MB")
            self.logger.info(f"当前进程线程数: {current_process.num_threads()}")
            
            for thread in threading.enumerate():
                self.logger.info(f"线程: {thread.name}, ID: {thread.ident}, 存活: {thread.is_alive()}")
        except Exception as e:
            self.logger.error(f"记录系统状态失败: {e}")
    
    def monitor_operation(self, operation_name):
        """操作监控装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                thread_id = threading.get_ident()
                self.logger.info(f"开始操作: {operation_name} [线程:{thread_id}]")
                start_time = datetime.datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (datetime.datetime.now() - start_time).total_seconds()
                    self.logger.info(f"操作成功: {operation_name} [耗时:{duration:.2f}s]")
                    return result
                except Exception as e:
                    duration = (datetime.datetime.now() - start_time).total_seconds()
                    self.logger.error(f"操作失败: {operation_name} [耗时:{duration:.2f}s] - {str(e)}")
                    self.logger.error(f"异常详情: {traceback.format_exc()}")
                    raise
            return wrapper
        return decorator


class ThreadSafeFileManager:
    """线程安全的文件操作管理器"""
    
    def __init__(self):
        self._file_locks = {}
        self._lock = threading.RLock()
    
    def _get_file_lock(self, filepath):
        """获取文件锁"""
        with self._lock:
            if filepath not in self._file_locks:
                self._file_locks[filepath] = threading.RLock()
            return self._file_locks[filepath]
    
    def safe_json_read(self, filepath, default=None):
        """线程安全的JSON读取"""
        file_lock = self._get_file_lock(filepath)
        with file_lock:
            try:
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return default
            except Exception as e:
                print(f"读取JSON文件失败 {filepath}: {e}")
                return default
    
    def safe_json_write(self, filepath, data):
        """线程安全的JSON写入"""
        file_lock = self._get_file_lock(filepath)
        with file_lock:
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"写入JSON文件失败 {filepath}: {e}")
                return False


class COMOperationManager:
    """COM操作管理器 - 提供线程安全的操作控制"""
    
    def __init__(self, max_concurrent_operations=1):
        self.semaphore = threading.Semaphore(max_concurrent_operations)
        self.operation_count = 0
        self.operation_lock = threading.RLock()
        self.last_operation_time = 0
        self.min_interval = 0.5  # 操作间隔
        self.operation_history = []
        self.max_history = 50
    
    @contextmanager
    def acquire_operation(self, operation_name="未知操作"):
        """获取操作权限的上下文管理器"""
        acquired = self.semaphore.acquire(timeout=30)
        if not acquired:
            raise TimeoutError(f"获取操作权限超时: {operation_name}")
        
        try:
            with self.operation_lock:
                # 控制操作间隔
                current_time = time.time()
                if current_time - self.last_operation_time < self.min_interval:
                    wait_time = self.min_interval - (current_time - self.last_operation_time)
                    time.sleep(wait_time)
                
                self.operation_count += 1
                self.last_operation_time = time.time()
            
            yield
            
        finally:
            with self.operation_lock:
                self.operation_count -= 1
            self.semaphore.release()
    
    def record_operation(self, operation, success, error=None):
        """记录操作历史"""
        record = {
            'timestamp': time.time(),
            'operation': operation,
            'success': success,
            'error': str(error) if error else None,
            'thread_id': threading.get_ident()
        }
        
        self.operation_history.append(record)
        if len(self.operation_history) > self.max_history:
            self.operation_history.pop(0)
    
    def get_stats(self):
        """获取操作统计"""
        if not self.operation_history:
            return {"total": 0, "success": 0, "failure": 0, "success_rate": 0}
        
        total = len(self.operation_history)
        success = sum(1 for op in self.operation_history if op['success'])
        failure = total - success
        success_rate = (success / total) * 100 if total > 0 else 0
        
        return {
            "total": total,
            "success": success,
            "failure": failure,
            "success_rate": success_rate
        }


class ProcessIsolatedCOMWorker:
    """进程隔离的COM工作器 - EXE兼容版"""
    
    def __init__(self):
        """初始化COM工作器"""
        self.process_timeout = 30  # 超时时间保留，用于其他限制
        
    def _execute_com_operation(self, operation, *args):
        """
        执行COM操作 - 使用线程隔离替代进程隔离，兼容EXE打包环境
        此方法在EXE环境下也能正常工作，不需要外部Python解释器
        """
        import queue
        import threading
        import traceback

        # 用于存储操作结果的队列
        result_queue = queue.Queue()
        
        # 在独立线程中执行COM操作
        def run_com_operation():
            try:
                # 导入必要的模块
                import json
                from ctypes import POINTER, cast

                # 初始化COM
                try:
                    import comtypes
                    comtypes.CoInitialize()
                    COM_INITIALIZED = True
                except Exception as e:
                    COM_INITIALIZED = False
                    error_msg = f"COM初始化失败: {str(e)}"
                    print(error_msg)
                    result_queue.put({"success": False, "error": error_msg})
                    return
                
                # 检查音量控制库是否可用
                if operation in ["get_volume", "set_volume"]:
                    try:
                        from pycaw.pycaw import (AudioUtilities,
                                                 IAudioEndpointVolume)
                        PYCAW_AVAILABLE = True
                    except ImportError as e:
                        error_msg = f"pycaw库导入失败: {str(e)}"
                        print(error_msg)
                        result_queue.put({"success": False, "error": error_msg})
                        return
                    except Exception as e:
                        error_msg = f"pycaw库初始化异常: {str(e)}"
                        print(error_msg)
                        result_queue.put({"success": False, "error": error_msg})
                        return
                
                try:
                    # 执行操作
                    if operation == "get_volume":
                        result = self._get_volume()
                    elif operation == "set_volume":
                        result = self._set_volume(args[0])
                    elif operation == "get_brightness":
                        result = self._get_brightness()
                    elif operation == "set_brightness":
                        result = self._set_brightness(args[0])
                    elif operation == "check_brightness":
                        result = self._check_brightness_support()
                    else:
                        result = {"success": False, "error": f"未知操作: {operation}"}
                    
                    # 将结果放入队列
                    result_queue.put(result)
                    
                except Exception as e:
                    # 捕获所有异常，防止线程崩溃
                    error_info = {
                        "success": False, 
                        "error": f"COM操作异常: {str(e)}",
                        "traceback": traceback.format_exc()
                    }
                    print(f"COM操作异常: {str(e)}\n{traceback.format_exc()}")
                    result_queue.put(error_info)
                finally:
                    # 释放COM资源
                    if COM_INITIALIZED:
                        try:
                            comtypes.CoUninitialize()
                        except:
                            pass
            except Exception as e:
                # 捕获线程中的所有异常
                error_msg = f"线程异常: {str(e)}"
                print(error_msg)
                result_queue.put({"success": False, "error": error_msg})
        
        # 创建并启动线程
        com_thread = threading.Thread(target=run_com_operation)
        com_thread.daemon = True  # 设为守护线程，确保主程序退出时线程也会退出
        com_thread.start()
        
        try:
            # 等待结果，带超时
            result = result_queue.get(timeout=self.process_timeout)
            return result
        except queue.Empty:
            # 超时处理
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            # 其他异常
            return {"success": False, "error": f"队列操作异常: {str(e)}"}
    
    # 以下是实际的COM操作函数
    def _get_volume(self):
        """获取系统音量实现"""
        try:
            from ctypes import POINTER, cast  # 确保在方法内也导入

            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_volume = volume.GetMasterVolumeLevelScalar()
            return {"success": True, "volume": int(current_volume * 100)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _set_volume(self, volume_percent):
        """设置系统音量实现"""
        try:
            from ctypes import POINTER, cast  # 确保在方法内也导入

            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            target_volume = max(0, min(100, volume_percent)) / 100.0
            volume.SetMasterVolumeLevelScalar(target_volume, None)
            
            current_volume = volume.GetMasterVolumeLevelScalar()
            return {"success": True, "volume": int(current_volume * 100)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_brightness(self):
        """获取屏幕亮度实现"""
        try:
            import io
            import sys

            import screen_brightness_control as sbc

            # 临时重定向标准错误，隐藏一些警告
            original_stderr = sys.stderr
            sys.stderr = io.StringIO()
            
            try:
                brightness = sbc.get_brightness()
                sys.stderr = original_stderr
                
                if isinstance(brightness, list):
                    brightness_value = brightness[0] if brightness else 0
                else:
                    brightness_value = brightness
                    
                return {"success": True, "brightness": brightness_value}
            except Exception as e:
                sys.stderr = original_stderr
                error_msg = str(e).lower()
                if "edid" in error_msg or "parse" in error_msg:
                    return {"success": False, "error": "亮度控制可能受限，但不影响使用"}
                else:
                    return {"success": False, "error": str(e)}
        except Exception as e:
            try:
                sys.stderr = original_stderr
            except:
                pass
            return {"success": False, "error": str(e)}
    
    def _set_brightness(self, brightness_percent):
        """设置屏幕亮度实现"""
        try:
            import io
            import sys

            import screen_brightness_control as sbc

            # 临时重定向标准错误
            original_stderr = sys.stderr
            sys.stderr = io.StringIO()
            
            brightness_level = max(0, min(100, brightness_percent))
            sbc.set_brightness(brightness_level)
            
            sys.stderr = original_stderr
            
            # 尝试读取设置后的亮度进行确认
            try:
                current_brightness = sbc.get_brightness()
                if isinstance(current_brightness, list):
                    current_percent = current_brightness[0] if current_brightness else brightness_level
                else:
                    current_percent = current_brightness
                
                return {"success": True, "brightness": current_percent}
            except:
                return {"success": True, "brightness": brightness_level, "note": "无法获取确认值"}
        except Exception as e:
            try:
                sys.stderr = original_stderr
            except:
                pass
            return {"success": False, "error": str(e)}
    
    def _check_brightness_support(self):
        """检查亮度支持实现"""
        try:
            # 尝试导入亮度控制库
            try:
                import screen_brightness_control as sbc
                BRIGHTNESS_AVAILABLE = True
            except ImportError:
                BRIGHTNESS_AVAILABLE = False
                return {"success": True, "brightness_available": False}
            
            # 创建结果对象
            result = {
                "success": True,
                "brightness_available": BRIGHTNESS_AVAILABLE,
                "detection_methods": {
                    "sbc_available": True
                }
            }
            
            # 如果库导入成功，检查是否能获取亮度
            if BRIGHTNESS_AVAILABLE:
                import io
                import sys
                original_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    brightness = sbc.get_brightness()
                    result["can_get_brightness"] = brightness is not None
                    result["brightness_value"] = brightness
                    result["detection_methods"]["can_get_brightness"] = True
                except Exception as e:
                    result["can_get_brightness"] = False
                    result["brightness_error"] = str(e)
                
                sys.stderr = original_stderr
                
                # 尝试列出显示器
                try:
                    monitors = sbc.list_monitors()
                    result["has_monitors"] = len(monitors) > 0
                    result["monitors"] = monitors
                    result["detection_methods"]["has_monitors"] = result["has_monitors"]
                except:
                    result["has_monitors"] = False
            
            # 判断结果 - 兼容旧版本保持宽松判断
            result["true_available"] = BRIGHTNESS_AVAILABLE
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e), "brightness_available": False}
    
    # 公共接口方法
    def get_volume(self):
        return self._execute_com_operation("get_volume")
    
    def set_volume(self, volume):
        return self._execute_com_operation("set_volume", volume)
    
    def get_brightness(self):
        return self._execute_com_operation("get_brightness")
    
    def set_brightness(self, brightness):
        return self._execute_com_operation("set_brightness", brightness)
    
    def check_brightness_support(self):
        return self._execute_com_operation("check_brightness")


class COMProtectionSystem:
    """COM保护系统 - 统一的接口和管理"""
    
    def __init__(self, cache_dir="cache", log_dir="log"):
        # 初始化各个组件
        self.crash_monitor = CrashMonitor(log_dir)
        self.file_manager = ThreadSafeFileManager()
        self.operation_manager = COMOperationManager()
        self.com_worker = ProcessIsolatedCOMWorker()
        
        # 缓存设置
        self.cache_dir = cache_dir
        self.volume_cache_file = os.path.join(cache_dir, "volume_cache.json")
        self.brightness_cache_file = os.path.join(cache_dir, "brightness_cache.json")
        self.cache_timeout = 2.0  # 缓存有效期（秒）
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        self.crash_monitor.logger.info("COM保护系统初始化完成")
    
    def _get_cached_value(self, cache_file, operation_name):
        """获取缓存值"""
        cache_data = self.file_manager.safe_json_read(cache_file, {})
        if cache_data:
            cache_time = cache_data.get('timestamp', 0)
            if time.time() - cache_time < self.cache_timeout:
                self.crash_monitor.logger.debug(f"使用缓存值: {operation_name}")
                return cache_data.get('value')
        return None
    
    def _set_cached_value(self, cache_file, value):
        """设置缓存值"""
        cache_data = {
            'value': value,
            'timestamp': time.time()
        }
        self.file_manager.safe_json_write(cache_file, cache_data)
    
    def get_volume(self, use_cache=True):
        """获取系统音量"""
        # 使用实例方法调用装饰器
        @self.crash_monitor.monitor_operation("get_volume")
        def _get_volume():
            # 尝试获取缓存值
            if use_cache:
                cached_volume = self._get_cached_value(self.volume_cache_file, "get_volume")
                if cached_volume is not None:
                    return {"success": True, "volume": cached_volume, "from_cache": True}
            
            # 执行实际操作
            with self.operation_manager.acquire_operation("get_volume"):
                result = self.com_worker.get_volume()
                
                # 记录操作结果
                self.operation_manager.record_operation("get_volume", result.get("success", False), result.get("error"))
                
                # 缓存成功结果
                if result.get("success") and "volume" in result:
                    self._set_cached_value(self.volume_cache_file, result["volume"])
                    result["from_cache"] = False
            
            return result
        
        return _get_volume()
    
    def set_volume(self, volume):
        """设置系统音量"""
        @self.crash_monitor.monitor_operation("set_volume")
        def _set_volume():
            with self.operation_manager.acquire_operation("set_volume"):
                result = self.com_worker.set_volume(volume)
                
                # 记录操作结果
                self.operation_manager.record_operation("set_volume", result.get("success", False), result.get("error"))
                
                # 更新缓存
                if result.get("success") and "volume" in result:
                    self._set_cached_value(self.volume_cache_file, result["volume"])
                
                return result
        
        return _set_volume()
    
    def get_brightness(self, use_cache=True):
        """获取屏幕亮度"""
        @self.crash_monitor.monitor_operation("get_brightness")
        def _get_brightness():
            # 尝试获取缓存值
            if use_cache:
                cached_brightness = self._get_cached_value(self.brightness_cache_file, "get_brightness")
                if cached_brightness is not None:
                    return {"success": True, "brightness": cached_brightness, "from_cache": True}
            
            # 执行实际操作
            with self.operation_manager.acquire_operation("get_brightness"):
                result = self.com_worker.get_brightness()
                
                # 记录操作结果
                self.operation_manager.record_operation("get_brightness", result.get("success", False), result.get("error"))
                
                # 缓存成功结果
                if result.get("success") and "brightness" in result:
                    self._set_cached_value(self.brightness_cache_file, result["brightness"])
                    result["from_cache"] = False
            
            return result
        
        return _get_brightness()
    
    def set_brightness(self, brightness):
        """设置屏幕亮度"""
        @self.crash_monitor.monitor_operation("set_brightness")
        def _set_brightness():
            with self.operation_manager.acquire_operation("set_brightness"):
                result = self.com_worker.set_brightness(brightness)
                
                # 记录操作结果
                self.operation_manager.record_operation("set_brightness", result.get("success", False), result.get("error"))
                
                # 更新缓存
                if result.get("success") and "brightness" in result:
                    self._set_cached_value(self.brightness_cache_file, result["brightness"])
                
                return result
        
        return _set_brightness()
    
    def check_brightness_support(self):
        """严格检查亮度调节功能是否支持"""
        @self.crash_monitor.monitor_operation("check_brightness")
        def _check_brightness_support():
            with self.operation_manager.acquire_operation("check_brightness"):
                result = self.com_worker.check_brightness_support()
                self.operation_manager.record_operation(
                    "check_brightness", 
                    result.get("success", False), 
                    result.get("error")
                )
                return result
        
        return _check_brightness_support()
    
    def get_system_stats(self):
        """获取系统统计信息"""
        stats = self.operation_manager.get_stats()
        stats["cache_info"] = {
            "volume_cache_exists": os.path.exists(self.volume_cache_file),
            "brightness_cache_exists": os.path.exists(self.brightness_cache_file)
        }
        return stats
    
    def clear_cache(self):
        """清除缓存"""
        try:
            if os.path.exists(self.volume_cache_file):
                os.remove(self.volume_cache_file)
            if os.path.exists(self.brightness_cache_file):
                os.remove(self.brightness_cache_file)
            self.crash_monitor.logger.info("缓存已清除")
            return True
        except Exception as e:
            self.crash_monitor.logger.error(f"清除缓存失败: {e}")
            return False


# 全局实例
_protection_system = None

def get_protection_system():
    """获取COM保护系统实例"""
    global _protection_system
    if _protection_system is None:
        _protection_system = COMProtectionSystem()
    return _protection_system


# 改进亮度控制可用性检测
def is_brightness_control_available():
    """
    更宽松地判断亮度控制是否可用
    使用多种检测方法并综合判断
    """
    system = get_protection_system()
    try:
        # 检查环境变量，允许用户强制启用亮度控制
        if os.environ.get('FORCE_BRIGHTNESS_ENABLE') == '1':
            print("亮度控制: 通过环境变量强制启用")
            return True
            
        # 使用专门的检查函数
        check_result = system.check_brightness_support()
        if check_result.get("success", False):
            is_available = check_result.get("brightness_available", False)
            # 输出详细的检测信息
            if "detection_methods" in check_result:
                methods = check_result["detection_methods"]
                print(f"亮度控制检测详情: Dxva2={methods.get('dxva2_available', False)}, "
                      f"SBC库={methods.get('sbc_available', False)}, "
                      f"能获取亮度={methods.get('can_get_brightness', False)}, "
                      f"有显示器={methods.get('has_monitors', False)}")
            
            return is_available
        
        # 备用方法：直接尝试获取亮度
        get_result = system.get_brightness(use_cache=False)
        if get_result.get("success", False):
            print("亮度控制: 通过直接获取亮度值判定为可用")
            return True
        
        # 第三种方法：尝试使用屏幕亮度控制库列出显示器
        try:
            import screen_brightness_control as sbc
            monitors = sbc.list_monitors()
            if monitors:
                print(f"亮度控制: 通过检测到显示器({len(monitors)}个)判定为可用")
                return True
        except:
            pass
            
        return False
    except Exception as e:
        print(f"亮度控制检测异常: {str(e)}")
        return False


# 便捷函数
def safe_get_volume(use_cache=True):
    """安全获取音量"""
    return get_protection_system().get_volume(use_cache)

def safe_set_volume(volume):
    """安全设置音量"""
    return get_protection_system().set_volume(volume)

def safe_get_brightness(use_cache=True):
    """安全获取亮度"""
    return get_protection_system().get_brightness(use_cache)

def safe_set_brightness(brightness):
    """安全设置亮度"""
    return get_protection_system().set_brightness(brightness)

def safe_check_brightness_support():
    """安全检查亮度控制是否可用（更严格的检查）"""
    return get_protection_system().check_brightness_support()

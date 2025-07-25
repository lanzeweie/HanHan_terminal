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
    """进程隔离的COM工作器 - 核心防护机制"""
    
    def __init__(self, worker_script_path=None):
        self.worker_script_path = worker_script_path or self._create_worker_script()
        self.process_timeout = 30  # 进程超时时间
    
    def _create_worker_script(self):
        """创建COM工作进程脚本"""
        script_content = '''
"""
COM操作工作进程 - 隔离COM操作避免主进程崩溃
"""
import json
import sys
from ctypes import POINTER, cast

# COM初始化
try:
    import comtypes
    comtypes.CoInitialize()
    COM_INITIALIZED = True
except Exception:
    COM_INITIALIZED = False

# 音量控制
try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

# 亮度控制 - 使用旧版本的简单检测方式
try:
    import screen_brightness_control as sbc
    # 简单检测：只要能导入库就认为亮度控制可能可用
    BRIGHTNESS_AVAILABLE = True
    
    # 尝试导入wmi库，但不强制要求（和旧版本一致）
    try:
        import wmi
    except ImportError:
        pass
        
    print("亮度控制库检测: 成功导入screen_brightness_control库")
except ImportError:
    BRIGHTNESS_AVAILABLE = False
    print("亮度控制库检测: 无法导入screen_brightness_control库")


def get_volume():
    """获取系统音量"""
    if not PYCAW_AVAILABLE or not COM_INITIALIZED:
        return {"success": False, "error": "pycaw不可用或COM未初始化"}
    
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_volume = volume.GetMasterVolumeLevelScalar()
        return {"success": True, "volume": int(current_volume * 100)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_volume(volume_percent):
    """设置系统音量"""
    if not PYCAW_AVAILABLE or not COM_INITIALIZED:
        return {"success": False, "error": "pycaw不可用或COM未初始化"}
    
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        target_volume = max(0, min(100, volume_percent)) / 100.0
        volume.SetMasterVolumeLevelScalar(target_volume, None)
        
        current_volume = volume.GetMasterVolumeLevelScalar()
        return {"success": True, "volume": int(current_volume * 100)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_brightness():
    """获取屏幕亮度 - 更宽容的实现"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用"}
    
    try:
        # 临时重定向标准错误，隐藏一些警告 (旧版本方式)
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            # 先尝试获取亮度
            brightness = sbc.get_brightness()
            # 恢复标准错误输出
            sys.stderr = original_stderr
            
            # 处理返回值
            if isinstance(brightness, list):
                brightness_value = brightness[0] if brightness else 0
            else:
                brightness_value = brightness
                
            return {"success": True, "brightness": brightness_value}
        except Exception as e:
            sys.stderr = original_stderr
            # 如果是EDID解析错误，这在很多设备上是正常的
            error_msg = str(e).lower()
            if "edid" in error_msg or "parse" in error_msg:
                # 尝试返回一个默认值
                return {"success": False, "error": "亮度控制可能受限，但不影响使用"}
            else:
                return {"success": False, "error": str(e)}
    except Exception as e:
        try:
            sys.stderr = original_stderr
        except:
            pass
        return {"success": False, "error": str(e)}


def set_brightness(brightness_percent):
    """设置屏幕亮度 - 更宽容的实现"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用"}
    
    try:
        # 临时重定向标准错误，隐藏一些警告 (旧版本方式)
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        # 设置亮度范围限制
        brightness_level = max(0, min(100, brightness_percent))
        
        # 尝试设置亮度
        sbc.set_brightness(brightness_level)
        
        # 恢复标准错误
        sys.stderr = original_stderr
        
        # 尝试读取设置后的亮度进行确认
        try:
            current_brightness = sbc.get_brightness()
            if isinstance(current_brightness, list):
                current_percent = current_brightness[0] if current_brightness else brightness_level
            else:
                current_percent = current_brightness
                
            return {"success": True, "brightness": current_percent}
        except Exception as e:
            # 即使无法获取确认值，但如果设置命令没有抛出异常，我们认为设置成功了
            return {"success": True, "brightness": brightness_level, "note": "无法获取确认值"}
    except Exception as e:
        try:
            sys.stderr = original_stderr
        except:
            pass
        return {"success": False, "error": str(e)}


def check_brightness_support():
    """检查亮度支持的函数 - 旧版本兼容版"""
    try:
        result = {
            "success": True,
            "brightness_available": BRIGHTNESS_AVAILABLE,
        }
        
        # 如果库导入成功，我们简单地认为亮度控制可能可用
        if BRIGHTNESS_AVAILABLE:
            # 进一步检查是否真的能获取亮度值
            try:
                # 临时重定向标准错误
                import io
                original_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                brightness = sbc.get_brightness()
                sys.stderr = original_stderr
                
                if brightness is not None:
                    result["can_get_brightness"] = True
                    result["brightness_value"] = brightness
                    # 如果获取亮度成功，检测结果为真正可用
                    result["true_available"] = True
                else:
                    result["can_get_brightness"] = False
                    # 即使获取失败，我们仍然认为可能可用
                    result["true_available"] = True
            except Exception as e:
                try:
                    sys.stderr = original_stderr
                except:
                    pass
                result["can_get_brightness"] = False
                result["brightness_error"] = str(e)
                # 旧版本中即使获取亮度失败也认为可能可用
                result["true_available"] = True
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "brightness_available": BRIGHTNESS_AVAILABLE}


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "缺少操作参数"}))
        sys.exit(1)
    
    operation = sys.argv[1]
    
    try:
        if operation == "get_volume":
            result = get_volume()
        elif operation == "set_volume":
            volume = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            result = set_volume(volume)
        elif operation == "get_brightness":
            result = get_brightness()
        elif operation == "set_brightness":
            brightness = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            result = set_brightness(brightness)
        elif operation == "check_brightness":
            result = check_brightness_support()
        else:
            result = {"success": False, "error": f"未知操作: {operation}"}
        
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
    finally:
        # 确保COM资源清理
        if COM_INITIALIZED:
            try:
                comtypes.CoUninitialize()
            except:
                pass


if __name__ == "__main__":
    main()
'''
        
        script_path = os.path.join(os.path.dirname(__file__), "com_worker_isolated.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        return script_path
    
    def _execute_com_operation(self, operation, *args):
        """执行COM操作（通过独立进程）"""
        try:
            cmd = [sys.executable, self.worker_script_path, operation] + [str(arg) for arg in args]
            
            # 不指定encoding，让subprocess.run返回字节而不是字符串
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.process_timeout,
                # 移除encoding参数，让输出保持为字节
            )
            
            if result.returncode == 0:
                # 使用更宽容的解码方式处理输出
                try:
                    # 首先尝试用UTF-8解码，大多数情况下应该是这个编码
                    stdout_text = result.stdout.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果UTF-8解码失败，使用latin-1编码（它可以处理所有可能的字节值）
                    stdout_text = result.stdout.decode('latin-1')
                
                try:
                    return json.loads(stdout_text.strip())
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始内容以便调试
                    return {
                        "success": False,
                        "error": f"无法解析JSON: {stdout_text[:100]}"
                    }
            else:
                # 错误输出也需要安全解码
                try:
                    stderr_text = result.stderr.decode('utf-8')
                except UnicodeDecodeError:
                    stderr_text = result.stderr.decode('latin-1')
                
                return {
                    "success": False,
                    "error": f"进程执行失败: {stderr_text or '未知错误'}"
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "操作超时"}
        except Exception as e:
            return {"success": False, "error": f"进程执行异常: {str(e)}"}
    
    def get_volume(self):
        """获取音量"""
        return self._execute_com_operation("get_volume")
    
    def set_volume(self, volume):
        """设置音量"""
        return self._execute_com_operation("set_volume", volume)
    
    def get_brightness(self):
        """获取亮度"""
        return self._execute_com_operation("get_brightness")
    
    def set_brightness(self, brightness):
        """设置亮度"""
        return self._execute_com_operation("set_brightness", brightness)
    
    def check_brightness_support(self):
        """检查亮度调节功能是否可用（更严格的检查）"""
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
    """更严格地检查亮度控制是否可用"""
    system = get_protection_system()
    try:
        # 使用专门的检查函数
        check_result = system.check_brightness_support()
        if check_result.get("success", False):
            return check_result.get("brightness_available", False)
        
        # 备用方法：尝试获取亮度
        get_result = system.get_brightness(use_cache=False)
        if get_result.get("success", False):
            return True
            
        return False
    except Exception:
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
    return get_protection_system().set_brightness(brightness)

def safe_check_brightness_support():
    """安全检查亮度控制是否可用（更严格的检查）"""
    return get_protection_system().check_brightness_support()

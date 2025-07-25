
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


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

# 亮度控制 - 使用更宽松的检测方式
try:
    import screen_brightness_control as sbc
    
    # 更简单的检测方式 - 只要能导入库并执行基本操作就认为可用
    try:
        # 首先尝试获取亮度列表
        monitors = sbc.list_monitors()
        
        # 然后尝试获取亮度值
        brightness_value = sbc.get_brightness(display=0 if monitors else None)
        
        # 如果能够正常获取亮度值，就认为亮度控制可用
        if brightness_value is not None:
            if isinstance(brightness_value, list):
                BRIGHTNESS_AVAILABLE = len(brightness_value) > 0
            else:
                BRIGHTNESS_AVAILABLE = True
        else:
            BRIGHTNESS_AVAILABLE = False
            
        print(f"亮度检测: 获取到值={brightness_value}, 支持亮度控制={BRIGHTNESS_AVAILABLE}")
        
    except Exception as e:
        BRIGHTNESS_AVAILABLE = False
        print(f"基本亮度检测失败: {str(e)}")
    
except ImportError:
    BRIGHTNESS_AVAILABLE = False
    print("无法导入screen_brightness_control库")


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
    """获取屏幕亮度"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用或当前设备不支持亮度调节"}
    
    try:
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            brightness = sbc.get_brightness(display=0)  # 尝试特定显示器
        except:
            brightness = sbc.get_brightness()  # 如果失败，尝试默认方式
            
        sys.stderr = original_stderr
        
        if isinstance(brightness, list):
            brightness_value = brightness[0] if brightness else 0
        else:
            brightness_value = brightness
            
        return {"success": True, "brightness": brightness_value, "brightness_available": True}
    except Exception as e:
        return {"success": False, "error": str(e), "brightness_available": False}
    finally:
        try:
            sys.stderr = original_stderr
        except:
            pass


def set_brightness(brightness_percent):
    """设置屏幕亮度"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用或当前设备不支持亮度调节"}
    
    try:
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        brightness_level = max(0, min(100, brightness_percent))
        
        # 尝试特定显示器，如果失败则尝试默认方式
        try:
            sbc.set_brightness(brightness_level, display=0)
        except:
            sbc.set_brightness(brightness_level)
            
        sys.stderr = original_stderr
        
        # 再次获取当前值作为确认
        try:
            current_brightness = sbc.get_brightness(display=0)
        except:
            current_brightness = sbc.get_brightness()
            
        if isinstance(current_brightness, list):
            current_value = current_brightness[0] if current_brightness else brightness_level
        else:
            current_value = current_brightness
        
        return {"success": True, "brightness": current_value, "brightness_available": True}
    except Exception as e:
        return {"success": False, "error": str(e), "brightness_available": False}
    finally:
        try:
            sys.stderr = original_stderr
        except:
            pass


def check_brightness_support():
    """专门检查亮度支持的函数 - 更宽松的版本"""
    try:
        result = {
            "success": True,
            "brightness_available": BRIGHTNESS_AVAILABLE,
        }
        
        # 尝试简单获取亮度值，这是最基本的检测
        try:
            brightness = sbc.get_brightness()
            result["simple_check"] = True
            result["brightness_value"] = brightness
            
            # 即使BRIGHTNESS_AVAILABLE是False，如果能成功获取亮度，也视为支持
            if brightness is not None and not BRIGHTNESS_AVAILABLE:
                result["brightness_available"] = True
                print("亮度检查: 虽然初始检测失败，但能获取亮度值，判定为支持")
        except Exception as e:
            result["simple_check"] = False
            result["simple_check_error"] = str(e)
        
        # 列出所有显示器
        try:
            import screen_brightness_control as sbc
            displays = sbc.list_monitors()
            result["displays"] = displays
            result["has_displays"] = len(displays) > 0
            
            # 如果有显示器列表，可能支持亮度控制
            if result["has_displays"] and not result["brightness_available"]:
                result["brightness_available"] = True
                print(f"亮度检查: 发现{len(displays)}个显示器，判定可能支持亮度控制")
        except Exception as e:
            result["displays"] = []
            result["has_displays"] = False
            result["display_list_error"] = str(e)
            
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "brightness_available": False}


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

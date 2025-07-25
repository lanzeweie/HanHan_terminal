
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

# 亮度控制
try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False


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
        return {"success": False, "error": "screen_brightness_control不可用"}
    
    try:
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        brightness = sbc.get_brightness()
        sys.stderr = original_stderr
        
        if isinstance(brightness, list):
            brightness_value = brightness[0] if brightness else 0
        else:
            brightness_value = brightness
            
        return {"success": True, "brightness": brightness_value}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            sys.stderr = original_stderr
        except:
            pass


def set_brightness(brightness_percent):
    """设置屏幕亮度"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用"}
    
    try:
        import io
        original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        brightness_level = max(0, min(100, brightness_percent))
        sbc.set_brightness(brightness_level)
        sys.stderr = original_stderr
        
        current_brightness = sbc.get_brightness()
        if isinstance(current_brightness, list):
            current_value = current_brightness[0] if current_brightness else brightness_level
        else:
            current_value = current_brightness
        
        return {"success": True, "brightness": current_value}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            sys.stderr = original_stderr
        except:
            pass


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

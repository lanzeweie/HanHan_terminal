import threading
import time

try:
    import screen_brightness_control as sbc
    BRIGHTNESS_AVAILABLE = True
except ImportError:
    BRIGHTNESS_AVAILABLE = False

_brightness_lock = threading.RLock()

def get_brightness():
    """获取屏幕亮度"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用"}
    with _brightness_lock:
        try:
            brightness = sbc.get_brightness()
            if isinstance(brightness, list):
                value = brightness[0] if brightness else 0
            else:
                value = brightness
            return {"success": True, "brightness": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

def set_brightness(percent):
    """设置屏幕亮度"""
    if not BRIGHTNESS_AVAILABLE:
        return {"success": False, "error": "screen_brightness_control不可用"}
    with _brightness_lock:
        try:
            value = max(0, min(100, int(percent)))
            sbc.set_brightness(value)
            # 再次读取确认
            try:
                brightness = sbc.get_brightness()
                if isinstance(brightness, list):
                    current = brightness[0] if brightness else value
                else:
                    current = brightness
                return {"success": True, "brightness": current}
            except Exception:
                return {"success": True, "brightness": value, "note": "无法确认"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def check_brightness_support():
    """检测亮度调节支持情况，返回详细检测信息"""
    result = {"success": True, "brightness_available": BRIGHTNESS_AVAILABLE}
    detection_methods = {
        "dxva2_available": False,
        "sbc_available": BRIGHTNESS_AVAILABLE,
        "can_get_brightness": False,
        "has_monitors": False
    }
    if not BRIGHTNESS_AVAILABLE:
        result["detection_methods"] = detection_methods
        return result
    try:
        # 检查是否有显示器
        monitors = sbc.list_monitors()
        detection_methods["has_monitors"] = bool(monitors)
        result["monitors"] = monitors

        # 检查能否获取亮度
        try:
            brightness = sbc.get_brightness()
            detection_methods["can_get_brightness"] = brightness is not None
            result["brightness_value"] = brightness
        except Exception as e:
            detection_methods["can_get_brightness"] = False
            result["brightness_error"] = str(e)

        # 检查dxva2方法（仅Windows）
        try:
            if hasattr(sbc, "get_methods"):
                methods = sbc.get_methods()
                if "windows" in methods:
                    dxva2 = methods["windows"].get("dxva2", None)
                    detection_methods["dxva2_available"] = bool(dxva2)
        except Exception:
            pass

        # 只要有一个为True就认为亮度可用
        is_available = (
            detection_methods["dxva2_available"] or
            detection_methods["sbc_available"] or
            detection_methods["can_get_brightness"] or
            detection_methods["has_monitors"]
        )
        result["brightness_available"] = is_available
        result["detection_methods"] = detection_methods
    except Exception as e:
        result["error"] = str(e)
        result["detection_methods"] = detection_methods
    return result

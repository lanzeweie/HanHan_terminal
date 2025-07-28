import json
import os
import queue
import subprocess
import sys
import threading
import time

# 配置
VOLUME_EXE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "volume_control.exe")
MAX_WORKERS = 2  # 并发进程数限制
TASK_QUEUE_SIZE = 20  # 最大排队任务数

# 任务队列和线程池
_task_queue = queue.Queue(maxsize=TASK_QUEUE_SIZE)
_result_dict = {}
_result_lock = threading.Lock()

def _worker():
    while True:
        task_id, args = _task_queue.get()
        try:
            cmd = [VOLUME_EXE] + args
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(timeout=10)
            try:
                result = json.loads(stdout.decode("utf-8"))
            except Exception:
                result = {"success": False, "error": stdout.decode(errors="ignore") + stderr.decode(errors="ignore")}
        except Exception as e:
            result = {"success": False, "error": str(e)}
        with _result_lock:
            _result_dict[task_id] = result
        _task_queue.task_done()

# 启动线程池
for _ in range(MAX_WORKERS):
    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def _submit_task(args):
    task_id = f"{time.time()}_{threading.get_ident()}"
    try:
        _task_queue.put((task_id, args), timeout=2)
    except queue.Full:
        return {"success": False, "error": "请求过于频繁，请稍后再试"}
    # 等待结果
    for _ in range(50):  # 最多等待5秒
        time.sleep(0.1)
        with _result_lock:
            if task_id in _result_dict:
                return _result_dict.pop(task_id)
    return {"success": False, "error": "音量操作超时"}

def get_volume():
    """获取当前音量"""
    return _submit_task(["get"])

def set_volume(percent):
    """设置音量到指定百分比"""
    percent = max(0, min(100, int(percent)))
    return _submit_task(["set", str(percent)])

def adjust_volume(delta):
    """音量增减delta（正负整数）"""
    try:
        delta = int(delta)
    except Exception:
        return {"success": False, "error": "参数错误"}
    return _submit_task(["adjust", str(delta)])

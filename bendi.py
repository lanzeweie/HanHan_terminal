import os

class windows_command():
    def shutdonw():
        os.system("shutdown /s /f")

    def suoping():
        os.system("rundll32.exe user32.dll,LockWorkStation")

    def lanping():
        os.system("taskkill /f /im wininit.exe")
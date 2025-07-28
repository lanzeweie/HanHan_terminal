// volume_control.cpp
//
// 用法示例：
//   获取当前音量：
//     volume_control.exe get
//   设置音量为50：
//     volume_control.exe set 50
//   音量增加5：
//     volume_control.exe adjust 5
//   音量减少10：
//     volume_control.exe adjust -10
//
// g++ 编译命令:
// g++ -o volume_control.exe volume_control.cpp -lole32 -luser32 -luuid -lwinmm -mconsole -DUNICODE -D_UNICODE

#include <windows.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <string>
#include <iostream>
#include <cwchar>
#include <comdef.h> // for _com_error

// --- 新增部分：模拟按键以显示系统OSD ---
void ShowVolumeOSD() {
    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) return;

    IAudioEndpointVolume* pEndpointVolume = NULL;
    IMMDeviceEnumerator* pEnumerator = NULL;
    IMMDevice* pDevice = NULL;

    try {
        hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), NULL, CLSCTX_ALL, __uuidof(IMMDeviceEnumerator), (void**)&pEnumerator);
        if (FAILED(hr)) throw std::runtime_error("Failed to create enumerator");

        hr = pEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
        if (FAILED(hr)) throw std::runtime_error("Failed to get endpoint");

        hr = pDevice->Activate(__uuidof(IAudioEndpointVolume), CLSCTX_ALL, NULL, (void**)&pEndpointVolume);
        if (FAILED(hr)) throw std::runtime_error("Failed to activate volume");

        float currentVolume = 0.0f;
        hr = pEndpointVolume->GetMasterVolumeLevelScalar(&currentVolume);
        if (FAILED(hr)) throw std::runtime_error("Failed to get volume");

        // 判断音量是否已到极限，选择合适方向
        bool canUp = currentVolume < 1.0f;
        bool canDown = currentVolume > 0.0f;

        // 用SendInput发送音量键
        INPUT input[2] = {};
        input[0].type = INPUT_KEYBOARD;
        input[1].type = INPUT_KEYBOARD;

        if (canUp) {
            input[0].ki.wVk = VK_VOLUME_UP;
            input[1].ki.wVk = VK_VOLUME_UP;
            input[1].ki.dwFlags = KEYEVENTF_KEYUP;
        } else if (canDown) {
            input[0].ki.wVk = VK_VOLUME_DOWN;
            input[1].ki.wVk = VK_VOLUME_DOWN;
            input[1].ki.dwFlags = KEYEVENTF_KEYUP;
        } else {
            // 静音或最大音量，无法触发OSD
            goto cleanup;
        }

        SendInput(2, input, sizeof(INPUT));
        Sleep(50); // 等待OSD弹出

        // 恢复原音量
        pEndpointVolume->SetMasterVolumeLevelScalar(currentVolume, NULL);

    } catch (...) {
        // 忽略错误
    }

cleanup:
    if (pEndpointVolume) pEndpointVolume->Release();
    if (pDevice) pDevice->Release();
    if (pEnumerator) pEnumerator->Release();
    CoUninitialize();
}


// JSON 输出函数
void printJson(bool success, int volume, const std::wstring& operation, const std::wstring& errorMsg) {
    if (success) {
        wprintf(L"{\n    \"success\": true,\n    \"volume\": %d,\n    \"operation\": \"%ls\"\n}\n", volume, operation.c_str());
    } else {
        wprintf(L"{\n    \"success\": false,\n    \"error\": \"%ls\",\n    \"operation\": \"%ls\"\n}\n", errorMsg.c_str(), operation.c_str());
    }
}

// 错误处理辅助函数
std::wstring HResultToString(HRESULT hr) {
    _com_error err(hr);
    return std::wstring(err.ErrorMessage());
}

// 主函数
int wmain(int argc, wchar_t* argv[]) {
    std::wstring operation = L"unknown";

    if (argc < 2) {
        printJson(false, -1, operation, L"Invalid arguments. Usage: volume_control.exe <get|set|adjust> [value]");
        return 1;
    }

    operation = argv[1];
    for (wchar_t& c : operation) {
        c = towlower(c);
    }

    HRESULT hr = CoInitialize(NULL);
    if (FAILED(hr)) {
        printJson(false, -1, operation, L"COM initialization failed. " + HResultToString(hr));
        return 1;
    }

    IAudioEndpointVolume* pEndpointVolume = NULL;
    IMMDeviceEnumerator* pEnumerator = NULL;
    IMMDevice* pDevice = NULL;

    try {
        hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), NULL, CLSCTX_ALL, __uuidof(IMMDeviceEnumerator), (void**)&pEnumerator);
        if (FAILED(hr)) throw std::runtime_error("Failed to create device enumerator. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));

        hr = pEnumerator->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
        if (FAILED(hr)) throw std::runtime_error("Failed to get default audio endpoint. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));

        hr = pDevice->Activate(__uuidof(IAudioEndpointVolume), CLSCTX_ALL, NULL, (void**)&pEndpointVolume);
        if (FAILED(hr)) throw std::runtime_error("Failed to activate endpoint volume interface. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));

        if (operation == L"get") {
            float currentVolume = 0.0f;
            hr = pEndpointVolume->GetMasterVolumeLevelScalar(&currentVolume);
            if (FAILED(hr)) throw std::runtime_error("Failed to get volume. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));
            
            printJson(true, static_cast<int>(currentVolume * 100 + 0.5), operation, L"");

        } else if (operation == L"set") {
            if (argc < 3) throw std::invalid_argument("Missing volume value for 'set' operation.");
            
            int targetVolumePercent = _wtoi(argv[2]);
            if (targetVolumePercent < 0 || targetVolumePercent > 100) {
                 throw std::out_of_range("Volume must be between 0 and 100.");
            }

            float targetVolumeScalar = targetVolumePercent / 100.0f;
            hr = pEndpointVolume->SetMasterVolumeLevelScalar(targetVolumeScalar, NULL);
            if (FAILED(hr)) throw std::runtime_error("Failed to set volume. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));
            
            float finalVolume = 0.0f;
            pEndpointVolume->GetMasterVolumeLevelScalar(&finalVolume);
            printJson(true, static_cast<int>(finalVolume * 100 + 0.5), operation, L"");
            
            // --- 调用新增的函数来显示OSD ---
            ShowVolumeOSD();

        } else if (operation == L"adjust") {
            if (argc < 3) throw std::invalid_argument("Missing adjustment value for 'adjust' operation.");

            int adjustment = _wtoi(argv[2]);

            float currentVolumeScalar = 0.0f;
            hr = pEndpointVolume->GetMasterVolumeLevelScalar(&currentVolumeScalar);
            if (FAILED(hr)) throw std::runtime_error("Failed to get current volume for adjustment. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));

            int currentVolumePercent = static_cast<int>(currentVolumeScalar * 100 + 0.5);
            int newVolumePercent = currentVolumePercent + adjustment;

            if (newVolumePercent > 100) newVolumePercent = 100;
            if (newVolumePercent < 0) newVolumePercent = 0;

            float newVolumeScalar = newVolumePercent / 100.0f;
            hr = pEndpointVolume->SetMasterVolumeLevelScalar(newVolumeScalar, NULL);
            if (FAILED(hr)) throw std::runtime_error("Failed to adjust volume. " + std::string(HResultToString(hr).begin(), HResultToString(hr).end()));
            
            float finalVolume = 0.0f;
            pEndpointVolume->GetMasterVolumeLevelScalar(&finalVolume);
            printJson(true, static_cast<int>(finalVolume * 100 + 0.5), operation, L"");

            // --- 调用新增的函数来显示OSD ---
            ShowVolumeOSD();

        } else {
            throw std::invalid_argument("Unknown operation: '" + std::string(operation.begin(), operation.end()) + "'. Must be 'get', 'set', or 'adjust'.");
        }

    } catch (const std::exception& e) {
        std::string errorStr = e.what();
        printJson(false, -1, operation, std::wstring(errorStr.begin(), errorStr.end()));
    }

    if (pEndpointVolume) pEndpointVolume->Release();
    if (pDevice) pDevice->Release();
    if (pEnumerator) pEnumerator->Release();
    
    CoUninitialize();

    return 0;
}
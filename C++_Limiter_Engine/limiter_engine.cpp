#include <windows.h>
#include <thread>
#include <vector>
#include <mutex>
#include <chrono>
#include <map>

// --- Function Pointer Typedefs for the NT API ---
typedef LONG (NTAPI *pNtSuspendProcess)(IN HANDLE ProcessHandle);
typedef LONG (NTAPI *pNtResumeProcess)(IN HANDLE ProcessHandle);

static pNtSuspendProcess g_NtSuspendProcess = nullptr;
static pNtResumeProcess g_NtResumeProcess = nullptr;

// --- Structs and Global State ---
struct ProcessInfo {
    DWORD pid;
    HANDLE hProcess;
    double suspend_ms;
    double resume_ms;
    bool is_suspended = false;
    std::chrono::steady_clock::time_point next_state_change_time;
};

static std::map<DWORD, ProcessInfo> g_managed_processes;
static std::mutex g_mutex;
static bool g_should_stop = false;
static std::thread g_manager_thread;

// --- Helper Functions ---
BOOL EnableDebugPrivilege() {
    HANDLE hToken;
    LUID luid;
    TOKEN_PRIVILEGES tkp;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken)) return FALSE;
    if (!LookupPrivilegeValue(NULL, SE_DEBUG_NAME, &luid)) { CloseHandle(hToken); return FALSE; }
    tkp.PrivilegeCount = 1;
    tkp.Privileges[0].Luid = luid;
    tkp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    BOOL result = AdjustTokenPrivileges(hToken, FALSE, &tkp, sizeof(tkp), NULL, NULL);
    CloseHandle(hToken);
    return result;
}

void cleanup_and_resume_process(ProcessInfo& info) {
    if (info.hProcess) {
        if (g_NtResumeProcess && info.is_suspended) { // Only resume if we know it was suspended
            g_NtResumeProcess(info.hProcess);
        }
        CloseHandle(info.hProcess);
        info.hProcess = NULL;
    }
}

// --- The Core Limiter Thread ---
void manager_loop() {
    using namespace std::chrono;
    timeBeginPeriod(1);

    while (!g_should_stop) {
        auto now = steady_clock::now();
        steady_clock::time_point next_wakeup = now + milliseconds(500);
        std::vector<DWORD> pids_to_remove;

        std::unique_lock<std::mutex> lock(g_mutex);

        if (g_managed_processes.empty()) {
            lock.unlock(); Sleep(100); continue;
        }

        for (auto& pair : g_managed_processes) {
            ProcessInfo& info = pair.second;
            
            DWORD exit_code;
            if (!GetExitCodeProcess(info.hProcess, &exit_code) || exit_code != STILL_ACTIVE) {
                pids_to_remove.push_back(info.pid);
                continue;
            }

            if (now >= info.next_state_change_time) {
                if (info.is_suspended) { // Time to RESUME
                    if (g_NtResumeProcess(info.hProcess) == 0) { // 0 is STATUS_SUCCESS
                        info.is_suspended = false;
                    }
                    info.next_state_change_time = now + milliseconds(static_cast<long long>(info.resume_ms));
                } else { // Time to SUSPEND
                    if (g_NtSuspendProcess(info.hProcess) == 0) { // 0 is STATUS_SUCCESS
                        info.is_suspended = true;
                    } else {
                        // FAILED to suspend. This method won't work for this process.
                        // Mark it for removal so we don't waste CPU trying again.
                        pids_to_remove.push_back(info.pid);
                        continue;
                    }
                    info.next_state_change_time = now + milliseconds(static_cast<long long>(info.suspend_ms));
                }
            }

            if (info.next_state_change_time < next_wakeup) {
                next_wakeup = info.next_state_change_time;
            }
        }
        
        for (DWORD pid_to_remove : pids_to_remove) {
            auto it = g_managed_processes.find(pid_to_remove);
            if (it != g_managed_processes.end()) {
                cleanup_and_resume_process(it->second);
                g_managed_processes.erase(it);
            }
        }
        lock.unlock();

        auto sleep_duration_ms = duration_cast<milliseconds>(next_wakeup - steady_clock::now()).count();
        if (sleep_duration_ms > 0) Sleep(static_cast<DWORD>(sleep_duration_ms));
    }
    timeEndPeriod(1);
}

// --- Functions Exported for Python ---
extern "C" {
    __declspec(dllexport) void StartLimiter() {
        if (g_manager_thread.joinable()) return;
        HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
        if (hNtdll) {
            g_NtSuspendProcess = (pNtSuspendProcess)GetProcAddress(hNtdll, "NtSuspendProcess");
            g_NtResumeProcess = (pNtResumeProcess)GetProcAddress(hNtdll, "NtResumeProcess");
        }
        if (!g_NtSuspendProcess || !g_NtResumeProcess) return;
        EnableDebugPrivilege();
        g_should_stop = false;
        g_manager_thread = std::thread(manager_loop);
    }

    __declspec(dllexport) void StopLimiter() {
        if (!g_manager_thread.joinable()) return;
        g_should_stop = true;
        g_manager_thread.join();
        std::lock_guard<std::mutex> lock(g_mutex);
        for (auto& pair : g_managed_processes) {
            cleanup_and_resume_process(pair.second);
        }
        g_managed_processes.clear();
    }

    __declspec(dllexport) void AddProcess(DWORD pid, int limit_percentage) {
        std::lock_guard<std::mutex> lock(g_mutex);
        if (g_managed_processes.count(pid)) return;

        // *** FIX: Request PROCESS_ALL_ACCESS for the best chance of success ***
        HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
        if (!hProcess) return;

        double cycle_time_ms = 200.0;
        ProcessInfo info;
        info.pid = pid;
        info.hProcess = hProcess;
        info.suspend_ms = cycle_time_ms * (limit_percentage / 100.0);
        info.resume_ms = cycle_time_ms - info.suspend_ms;
        if (info.resume_ms < 1) info.resume_ms = 1;
        if (info.suspend_ms < 1) info.suspend_ms = 1;
        info.is_suspended = false;
        info.next_state_change_time = std::chrono::steady_clock::now();

        g_managed_processes[pid] = info;
    }

    __declspec(dllexport) void RemoveProcess(DWORD pid) {
        std::lock_guard<std::mutex> lock(g_mutex);
        auto it = g_managed_processes.find(pid);
        if (it != g_managed_processes.end()) {
            cleanup_and_resume_process(it->second);
            g_managed_processes.erase(it);
        }
    }

    __declspec(dllexport) int GetManagedPids(DWORD* pids_array, int max_size) {
        std::lock_guard<std::mutex> lock(g_mutex);
        int count = 0;
        for (const auto& pair : g_managed_processes) {
            if (count < max_size) pids_array[count++] = pair.first;
            else break;
        }
        return count;
    }
}
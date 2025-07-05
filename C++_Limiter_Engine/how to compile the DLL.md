# How to Compile the DLL

## Prerequisites
1. **Install Visual Studio Community** (it's free).  
    During installation, select the **"Desktop development with C++"** workload.  
    From the list of components, ensure the following are installed:
    - ✅ **MSVC v143 - VS 2022 C++ x64/x86 build tools** (This is the actual compiler and the most important part).
    - ✅ **Windows 11 SDK** (Provides Windows-specific libraries like `<windows.h>`).

## Steps to Compile
1. After installation, open the **Start Menu**.
2. Search for and open **x64 Native Tools Command Prompt**.
3. Navigate to the directory containing your `limiter_engine.cpp` file.
4. Run the following compile command:
    ```bash
    cl.exe /LD /EHsc /O2 limiter_engine.cpp winmm.lib Advapi32.lib
    ```

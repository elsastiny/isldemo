#include <flutter/dart_project.h>
#include <flutter/flutter_view_controller.h>
#include <windows.h>

#include "flutter_window.h"
#include "utils.h"

int APIENTRY wWinMain(_In_ HINSTANCE instance, _In_opt_ HINSTANCE prev,
                      _In_ wchar_t *command_line, _In_ int show_command) {
  // Attach to console when present (e.g., 'flutter run') or create a
  // new console when running with a debugger.
  if (!::AttachConsole(ATTACH_PARENT_PROCESS) && ::IsDebuggerPresent()) {
    CreateAndAttachConsole();
  }

  // Initialize COM, so that it is available for use in the library and/or
  // plugins.
  ::CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);

  flutter::DartProject project(L"data");

  std::vector<std::string> command_line_arguments =
      GetCommandLineArguments();

  project.set_dart_entrypoint_arguments(std::move(command_line_arguments));

  FlutterWindow window(project);
  Win32Window::Point origin(10, 10);
  
  // Adjusted initial window bounds to match the narrow, sleek dashboard layout specs (380x620)
  Win32Window::Size size(380, 620);
  
  // 1. First, check if creating the window fails. If it does, stop execution immediately.
  if (!window.Create(L"signspeak", origin, size)) {
    return EXIT_FAILURE;
  }
  
  // 2. NOW APPLY THE FLOATING OVERLAY PARAMETERS (Since window creation succeeded!)
  HWND hwnd = window.GetHandle();
  
  // WS_EX_TOPMOST: Pins the window on top of any external app like Zoom or Microsoft Teams
  // WS_EX_LAYERED: Allows complete transparency layers to render across the custom background layout canvas
  SetWindowLong(hwnd, GWL_EXSTYLE, GetWindowLong(hwnd, GWL_EXSTYLE) | WS_EX_TOPMOST | WS_EX_LAYERED);
  
  // Set window opacity attributes (255 = fully visible layout elements, while background stays clean and transparent)
  SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA);
  
  // Force update window UI to lock properties into the Windows OS window manager layer
  ShowWindow(hwnd, SW_SHOW);
  UpdateWindow(hwnd);

  window.SetQuitOnClose(true);

  ::MSG msg;
  while (::GetMessage(&msg, nullptr, 0, 0)) {
    ::TranslateMessage(&msg);
    ::DispatchMessage(&msg);
  }

  ::CoUninitialize();
  return EXIT_SUCCESS;
}
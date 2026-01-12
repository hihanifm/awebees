; NSIS Installer Script for LensAI (Self-contained with Python)
; This installer includes embedded Python runtime

!include "MUI2.nsh"

; Installer Information
Name "LensAI"
!ifdef OUTDIR
OutFile "${OUTDIR}\lens-setup-with-python.exe"
!else
OutFile "lens-setup-with-python.exe"
!endif
InstallDir "$PROGRAMFILES\LensAI"
RequestExecutionLevel admin

; Build directory (passed from GitHub Actions)
!ifndef BUILD_DIR
!define BUILD_DIR "build\windows"
!endif

; Version information (can be overridden by command line)
!ifndef VERSION
!define VERSION "2.6.0"
!endif
!define APP_NAME "LensAI"
!define PUBLISHER "LensAI Development Team"
!define APP_URL "https://github.com/hihanifm/awebees"

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer (Self-contained)"
VIAddVersionKey "LegalCopyright" "Copyright (C) 2024"

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Finish page settings - Add "Run Lens" option
!define MUI_FINISHPAGE_RUN "$INSTDIR\lens-start.bat"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Lens now"
!define MUI_FINISHPAGE_TEXT "LensAI has been successfully installed on your computer.$\r$\n$\r$\nYou can start LensAI by:$\r$\n  • Clicking the checkbox above to launch it now$\r$\n  • Using the desktop shortcut$\r$\n  • Opening it from the Start Menu (LensAI folder)$\r$\n$\r$\nOnce started, LensAI will run in the system tray. Right-click the tray icon to start/stop the backend or view logs."

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Function to check and optionally install ripgrep
Function CheckRipgrep
    ; #region agent log - Debug: Log PATH environment
    ; Write debug info to log file
    FileOpen $R1 "$TEMP\lens-installer-debug.log" w
    FileWrite $R1 "=== Ripgrep Detection Debug (with-python) ===$\r$\n"
    ; Get system PATH
    ReadEnvStr $R2 "PATH"
    FileWrite $R1 "System PATH: $R2$\r$\n"
    FileClose $R1
    ; Capture where.exe output to file
    ExecWait 'cmd /c where rg > "$TEMP\rg-where-output.txt" 2>&1' $R3
    ; #endregion agent log
    
    ; Method 1: Try direct command execution (current method - no cmd /c)
    ClearErrors
    ExecWait 'rg --version' $0
    ; #region agent log - Debug: Log Method 1 result
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Method 1 (rg --version, no cmd): exit code=$0, errors=$EXEC_ERR$\r$\n"
    ; Read where.exe output if available
    IfFileExists "$TEMP\rg-where-output.txt" 0 skipWhereRead
        ClearErrors
        FileOpen $R4 "$TEMP\rg-where-output.txt" r
        IfErrors skipWhereRead
        FileRead $R4 $R5
        FileWrite $R1 "where.exe output: $R5$\r$\n"
        FileClose $R4
    skipWhereRead:
    FileClose $R1
    ; #endregion agent log
    IfErrors 0 RipgrepFound
    
    ; #region agent log - Debug: Method 1 failed, try alternative methods
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Method 1 failed, trying alternative detection...$\r$\n"
    FileClose $R1
    ; #endregion agent log
    
    ; Method 2: Try with cmd /c (like the other installer)
    ExecWait 'cmd /c rg --version' $0
    ; #region agent log - Debug: Log Method 2 result
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Method 2 (cmd /c rg --version): exit code=$0$\r$\n"
    FileClose $R1
    ; #endregion agent log
    IntCmp $0 0 RipgrepFound
    
    ; Method 3: Try with where.exe result (if it found rg, use that path)
    IfFileExists "$TEMP\rg-where-output.txt" 0 tryMethod4
        ClearErrors
        FileOpen $R4 "$TEMP\rg-where-output.txt" r
        IfErrors tryMethod4
        FileRead $R4 $R5
        FileClose $R4
        ; Try executing rg from the path found by where.exe
        ExecWait 'cmd /c "$R5" --version' $0
        ; #region agent log - Debug: Log Method 3 result
        FileOpen $R1 "$TEMP\lens-installer-debug.log" a
        FileWrite $R1 "Method 3 (where.exe path): exit code=$0, path=$R5$\r$\n"
        FileClose $R1
        ; #endregion agent log
        IntCmp $0 0 RipgrepFound
    tryMethod4:
    
    ; Method 4: Check common installation locations
    IfFileExists "$PROGRAMFILES\ripgrep\rg.exe" RipgrepFound
    IfFileExists "$PROGRAMFILES(x86)\ripgrep\rg.exe" RipgrepFound
    ReadEnvStr $R6 "LOCALAPPDATA"
    StrCmp $R6 "" skipUserCheck
        IfFileExists "$R6\Microsoft\WindowsApps\rg.exe" RipgrepFound
    skipUserCheck:
    ; #region agent log - Debug: Log Method 4 results
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Method 4 (file system check): not found in common locations$\r$\n"
    FileClose $R1
    ; #endregion agent log
    
    ; Ripgrep not found, ask user if they want to install it
    MessageBox MB_YESNO|MB_ICONQUESTION "Ripgrep (rg) is not installed.$\n$\nRipgrep enables 10-100x faster pattern matching (optional but recommended).$\nWould you like to install it automatically using winget?" IDNO RipgrepSkipped
    
    ; Check if winget is available
    ClearErrors
    ExecWait 'winget --version' $0
    IfErrors WingetNotFound
    
    ; Install ripgrep via winget
    DetailPrint "Installing ripgrep via winget..."
    ExecWait 'winget install BurntSushi.ripgrep.MSVC --silent --accept-source-agreements --accept-package-agreements' $0
    IfErrors WingetInstallFailed
    
    ; Verify installation
    ClearErrors
    ExecWait 'rg --version' $0
    IfErrors RipgrepInstallFailed
    DetailPrint "Ripgrep installed successfully"
    Goto RipgrepFound
    
    WingetNotFound:
    MessageBox MB_OK|MB_ICONEXCLAMATION "winget is not available on this system.$\n$\nRipgrep installation skipped. You can install it manually later:$\nwinget install BurntSushi.ripgrep.MSVC"
    Goto RipgrepSkipped
    
    WingetInstallFailed:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to install ripgrep via winget.$\n$\nYou can install it manually later:$\nwinget install BurntSushi.ripgrep.MSVC"
    Goto RipgrepSkipped
    
    RipgrepInstallFailed:
    MessageBox MB_OK|MB_ICONEXCLAMATION "Ripgrep installation completed but verification failed.$\n$\nYou may need to restart your system or add ripgrep to PATH manually."
    Goto RipgrepSkipped
    
    RipgrepSkipped:
    DetailPrint "Ripgrep installation skipped (optional component)"
    Goto RipgrepDone
    
    RipgrepFound:
    DetailPrint "Ripgrep is already installed"
    
    ; #region agent log - Debug: Log successful detection
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Result: Ripgrep FOUND$\r$\n"
    FileClose $R1
    ; #endregion agent log
    
    RipgrepDone:
    
    ; #region agent log - Debug: Log final result if not found
    FileOpen $R1 "$TEMP\lens-installer-debug.log" a
    FileWrite $R1 "Result: Ripgrep NOT FOUND (or skipped)$\r$\n"
    FileWrite $R1 "Debug log location: $TEMP\lens-installer-debug.log$\r$\n"
    FileClose $R1
    ; #endregion agent log
    
FunctionEnd

; Function to uninstall previous version if it exists
Function uninstallPrevious
    ; Check if LensAI is already installed by looking for the registry key
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "UninstallString"
    StrCmp $0 "" checkOld
    goto found
    
    checkOld:
    ; Also check for old "Lens" registry key for backward compatibility
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Lens" "UninstallString"
    StrCmp $0 "" done
    
    found:
    ; Found existing installation, uninstall it
    DetailPrint "Uninstalling previous version of LensAI..."
    ExecWait '"$0" /S _?=$INSTDIR'
    
    ; Wait a bit for uninstaller to complete
    Sleep 1000
    
    ; Remove the installation directory if it still exists
    IfFileExists "$INSTDIR" 0 done
    RMDir /r "$INSTDIR"
    
    done:
FunctionEnd

; Installer Sections
Section "Lens Application" SecApp
    SectionIn RO
    
    ; Uninstall previous version if it exists
    Call uninstallPrevious
    
    ; Check and optionally install ripgrep (optional component)
    Call CheckRipgrep
    
    SetOutPath "$INSTDIR"
    
    ; Extract package contents
    File /r "${BUILD_DIR}\lens-app-with-python\*"
    
    ; Install Python dependencies for embedded Python
    DetailPrint "Installing Python dependencies..."
    ExecWait '"$INSTDIR\python\python.exe" -m ensurepip --upgrade'
    ExecWait '"$INSTDIR\python\python.exe" -m pip install --upgrade pip'
    ExecWait '"$INSTDIR\python\python.exe" -m pip install -r "$INSTDIR\backend\requirements.txt"'
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\LensAI"
    CreateShortcut "$SMPROGRAMS\LensAI\LensAI.lnk" "$INSTDIR\lens-start.bat" "" "$INSTDIR\lens-start.bat" 0
    CreateShortcut "$SMPROGRAMS\LensAI\Stop LensAI.lnk" "$INSTDIR\lens-stop.bat" "" "$INSTDIR\lens-stop.bat" 0
    CreateShortcut "$SMPROGRAMS\LensAI\Uninstall LensAI.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
    
    ; Create desktop shortcut (optional)
    CreateShortcut "$DESKTOP\LensAI.lnk" "$INSTDIR\lens-start.bat" "" "$INSTDIR\lens-start.bat" 0
    
    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "NoRepair" 1
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\LensAI"
    Delete "$DESKTOP\LensAI.lnk"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI"
SectionEnd


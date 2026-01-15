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
    ; Found existing installation
    DetailPrint "Existing LensAI installation detected"
    
    ; Check if app is running (check for both python.exe and pythonw.exe processes)
    ; python.exe = backend server, pythonw.exe = tray icon
    DetailPrint "Checking for running LensAI processes..."
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH | findstr /C:"python.exe"' $R0
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH | findstr /C:"pythonw.exe"' $R3
    ; If findstr finds either process, exit code is 0 (found)
    ; If findstr doesn't find it, exit code is non-zero (not found)
    IntCmp $R0 0 processRunning
    IntCmp $R3 0 processRunning
    ; No process found - continue
    Goto continueUninstall
    
    processRunning:
    ; Python process found - ask user to close
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "LensAI appears to be running.$\n$\nThe application must be closed before upgrading.$\n$\nWould you like to close it now and continue with the upgrade?" IDNO abortUpgrade
    ; Try to stop python processes (necessary for upgrade)
    ; Stop both python.exe (backend server) and pythonw.exe (tray icon)
    DetailPrint "Stopping running LensAI processes..."
    ExecWait 'cmd /c taskkill /F /IM python.exe /T' $R1
    ExecWait 'cmd /c taskkill /F /IM pythonw.exe /T' $R4
    ; Give processes time to terminate (increased from 2000ms to 5000ms)
    Sleep 5000
    ; Verify processes are actually gone
    DetailPrint "Verifying processes have terminated..."
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH | findstr /C:"python.exe"' $R2
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH | findstr /C:"pythonw.exe"' $R5
    IntCmp $R2 0 processesStillRunning
    IntCmp $R5 0 processesStillRunning
    ; Processes are gone, continue
    Goto continueUninstall
    processesStillRunning:
    ; Processes still running, wait a bit more and try again
    DetailPrint "Some processes still running, waiting additional 3 seconds..."
    Sleep 3000
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH | findstr /C:"python.exe"' $R2
    ExecWait 'cmd /c tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH | findstr /C:"pythonw.exe"' $R5
    IntCmp $R2 0 warnProcessesStillRunning
    IntCmp $R5 0 warnProcessesStillRunning
    ; Processes are now gone
    Goto continueUninstall
    warnProcessesStillRunning:
    ; Still running after retry - warn user but continue
    DetailPrint "Warning: Some Python processes may still be running. Continuing anyway..."
    
    continueUninstall:
    ; Backup .env file if it exists
    IfFileExists "$INSTDIR\backend\.env" 0 skipBackup
        DetailPrint "Backing up .env file..."
        CreateDirectory "$TEMP\LensAI-Upgrade\backend"
        CopyFiles /SILENT "$INSTDIR\backend\.env" "$TEMP\LensAI-Upgrade\backend\.env"
    skipBackup:
    
    ; Uninstall previous version
    DetailPrint "Uninstalling previous version of LensAI..."
    IfFileExists "$0" 0 skipUninstall
        ExecWait '"$0" /S _?=$INSTDIR' $R6
        ; Check if uninstaller succeeded (exit code 0)
        IntCmp $R6 0 uninstallSuccess
        ; Uninstaller failed
        MessageBox MB_OK|MB_ICONEXCLAMATION "Failed to uninstall previous version (exit code: $R6).$\n$\nPlease uninstall manually from Control Panel and try again."
        ; If .env was backed up, inform user
        IfFileExists "$TEMP\LensAI-Upgrade\backend\.env" 0 abortUpgrade
            MessageBox MB_OK|MB_ICONINFORMATION ".env file was backed up to:$\n$TEMP\LensAI-Upgrade\backend\.env"
        Abort
    uninstallSuccess:
    skipUninstall:
    
    ; Wait a bit for uninstaller to complete
    Sleep 1000
    
    ; Remove the installation directory if it still exists
    ; (The uninstaller should have removed it, but clean up just in case)
    ; Note: .env backup is already in $TEMP, so it's safe to remove $INSTDIR
    IfFileExists "$INSTDIR" 0 done
    
    ; Try to remove venv directory separately first (venv files are often locked)
    IfFileExists "$INSTDIR\venv" 0 skipVenvCleanup
        DetailPrint "Removing old virtual environment directory..."
        RMDir /r "$INSTDIR\venv"
        ; If venv removal failed, try with REBOOTOK flag
        IfFileExists "$INSTDIR\venv" 0 skipVenvCleanup
            DetailPrint "Virtual environment directory locked, will be removed on reboot..."
            RMDir /REBOOTOK "$INSTDIR\venv"
    skipVenvCleanup:
    
    ; Now try to remove the entire installation directory
    DetailPrint "Removing old installation directory..."
    RMDir /r "$INSTDIR"
    ; If removal failed, try with REBOOTOK flag for stubborn files
    IfFileExists "$INSTDIR" 0 done
        DetailPrint "Some files are locked, will be removed on reboot..."
        RMDir /REBOOTOK "$INSTDIR"
    
    ; Note: .env file will be restored after files are extracted in the main section
    Goto done
    
    abortUpgrade:
    Abort
    
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
    
    ; Restore .env file if it was backed up (after files are extracted)
    IfFileExists "$TEMP\LensAI-Upgrade\backend\.env" 0 skipRestoreAfterExtract
        DetailPrint "Restoring .env file..."
        CopyFiles /SILENT "$TEMP\LensAI-Upgrade\backend\.env" "$INSTDIR\backend\.env"
        ; Clean up backup
        RMDir /r "$TEMP\LensAI-Upgrade"
    skipRestoreAfterExtract:
    
    ; Install Python dependencies for embedded Python
    DetailPrint "Installing Python dependencies..."
    ExecWait '"$INSTDIR\python\python.exe" -m ensurepip --upgrade'
    ExecWait '"$INSTDIR\python\python.exe" -m pip install --upgrade pip'
    ExecWait '"$INSTDIR\python\python.exe" -m pip install -r "$INSTDIR\backend\requirements.txt"'
    
    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\LensAI" "NoRepair" 1
    
    ; Create uninstaller (must be done before creating shortcuts)
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\LensAI"
    CreateShortcut "$SMPROGRAMS\LensAI\LensAI.lnk" "$INSTDIR\lens-start.bat" "" "$INSTDIR\lens-start.bat" 0
    CreateShortcut "$SMPROGRAMS\LensAI\Stop LensAI.lnk" "$INSTDIR\lens-stop.bat" "" "$INSTDIR\lens-stop.bat" 0
    CreateShortcut "$SMPROGRAMS\LensAI\Uninstall LensAI.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
    
    ; Create desktop shortcut (optional)
    CreateShortcut "$DESKTOP\LensAI.lnk" "$INSTDIR\lens-start.bat" "" "$INSTDIR\lens-start.bat" 0
    
    ; Automatically start the application after installation
    ExecShell "open" "$INSTDIR\lens-start.bat"
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


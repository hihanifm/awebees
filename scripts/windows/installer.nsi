; NSIS Installer Script for LensAI
; This installer automatically installs Python and ripgrep via winget if needed

!include "MUI2.nsh"

; Installer Information
Name "LensAI"
!ifdef OUTDIR
OutFile "${OUTDIR}\lens-setup.exe"
!else
OutFile "lens-setup.exe"
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
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
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

; Function to check and optionally install Python
Function CheckPython
    ClearErrors
    ExecWait 'python --version' $0
    IfErrors 0 PythonFound
    
    ; Python not found, ask user if they want to install it
    MessageBox MB_YESNO|MB_ICONQUESTION "Python 3.x is not installed or not in PATH.$\n$\nLensAI requires Python 3.x.$\nWould you like to install Python automatically using winget?" IDNO PythonSkipped
    
    ; Check if winget is available
    ClearErrors
    ExecWait 'winget --version' $0
    IfErrors WingetNotFound
    
    ; Install Python via winget
    DetailPrint "Installing Python via winget..."
    ExecWait 'winget install Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements' $0
    IfErrors WingetInstallFailed
    
    ; Wait a bit for Python to be added to PATH
    Sleep 2000
    
    ; Verify installation
    ClearErrors
    ExecWait 'python --version' $0
    IfErrors PythonInstallFailed
    DetailPrint "Python installed successfully"
    Goto PythonFound
    
    WingetNotFound:
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "winget is not available on this system.$\n$\nPython installation via winget is not possible.$\nWould you like to open the Python download page?" IDNO PythonSkipped
    ExecShell "open" "https://www.python.org/downloads/"
    Abort
    
    WingetInstallFailed:
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "Failed to install Python via winget.$\n$\nWould you like to open the Python download page?" IDNO PythonSkipped
    ExecShell "open" "https://www.python.org/downloads/"
    Abort
    
    PythonInstallFailed:
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "Python installation completed but verification failed.$\n$\nYou may need to restart your system or add Python to PATH manually.$\nWould you like to open the Python download page?" IDNO PythonSkipped
    ExecShell "open" "https://www.python.org/downloads/"
    Abort
    
    PythonSkipped:
    MessageBox MB_OK|MB_ICONSTOP "Python installation is required to continue.$\n$\nPlease install Python 3.x and run the installer again.$\nDownload: https://www.python.org/downloads/"
    Abort
    
    PythonFound:
    DetailPrint "Python is already installed"
FunctionEnd

; Function to check and optionally install ripgrep
Function CheckRipgrep
    ClearErrors
    ExecWait 'rg --version' $0
    IfErrors 0 RipgrepFound
    
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
    
    RipgrepDone:
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
    
    ; Check for Python before installation
    Call CheckPython
    
    ; Check and optionally install ripgrep (optional component)
    Call CheckRipgrep
    
    SetOutPath "$INSTDIR"
    
    ; Extract package contents
    File /r "${BUILD_DIR}\lens-app\*"
    
    ; Create virtual environment and install dependencies
    DetailPrint "Creating virtual environment..."
    ExecWait 'python -m venv "$INSTDIR\venv"'
    
    DetailPrint "Installing dependencies..."
    ExecWait '"$INSTDIR\venv\Scripts\python.exe" -m pip install --upgrade pip'
    ExecWait '"$INSTDIR\venv\Scripts\python.exe" -m pip install -r "$INSTDIR\backend\requirements.txt"'
    
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


@echo off
chcp 65001 >nul 2>&1
echo.
echo ====================================================
echo   Captcha Service Build Script
echo ====================================================
echo.

echo [Step 1] Checking Python...
py --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo.
echo [Step 2] Checking model files...
if not exist "model\best_v3.onnx" (
    echo ERROR: YOLO model not found: model\best_v3.onnx
    pause
    exit /b 1
)
if not exist "model\pre_model_v7.onnx" (
    echo ERROR: Siamese model not found: model\pre_model_v7.onnx
    pause
    exit /b 1
)
echo Model files OK

echo.
echo [Step 3] Installing PyInstaller...
py -m pip install pyinstaller -q

echo.
echo [Step 4] Building executable (this may take a few minutes)...
py -m PyInstaller build.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo [Step 5] Cleaning up...
if exist "build" rmdir /s /q "build" 2>nul

echo.
echo ====================================================
echo   Build Complete!
echo ====================================================
echo.
echo Output: dist\captcha-service.exe
echo.
echo Usage:
echo   - Copy captcha-service.exe to any Windows PC
echo   - Double-click to start the service
echo   - Service URL: http://127.0.0.1:8000
echo   - API Docs: http://127.0.0.1:8000/docs
echo.
echo ====================================================
pause
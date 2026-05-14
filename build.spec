# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置文件
# 模型文件会被打包进 exe，实现单文件部署

import os

block_cipher = None

# 模型文件路径
# SPECPATH 是 PyInstaller 提供的内置变量，指向 spec 文件所在目录
MODEL_DIR = os.path.join(SPECPATH, 'model')

a = Analysis(
    ['service.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 打包模型文件到 exe 内部
        (os.path.join(MODEL_DIR, '*.onnx'), 'model'),
        (os.path.join(MODEL_DIR, 'version.json'), 'model'),  # 包含版本信息
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.responses',
        'fastapi.routing',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'onnxruntime',
        'scipy',
        'scipy.optimize',
        'aiohttp',
        'app',
        'app.main',
        'app.api.router',
        'app.api.endpoints.dianxuan',
        'app.models.input',
        'app.services.operation',
        'app.utils.errors',
        'src',
        'src.captcha',
        'src.utils',
        'src.utils.matchingMode',
        'src.utils.ver_onnx',
        'src.utils.yolo_onnx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='captcha-service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，方便查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon='icon.ico'
)
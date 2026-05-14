# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File       : service.py
# Time       ：2021/9/26 14:36
# Author     ：yujia
# version    ：python 3.6
# Description：验证码识别服务启动入口
"""
import os
import json
import uvicorn
from app import main

# 模型版本配置文件路径
MODEL_VERSION_FILE = os.path.join(os.path.dirname(__file__), 'model', 'version.json')

# 当前支持的模型版本
CURRENT_MODEL_VERSION = {
    "yolo_model": "best_v3.onnx",
    "siamese_model": "pre_model_v7.onnx",
    "version": "1.0.0",
    "update_date": "2026-05-11"
}

def check_model_version():
    """检查模型版本信息"""
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    
    # 检查模型文件是否存在
    yolo_path = os.path.join(model_dir, CURRENT_MODEL_VERSION["yolo_model"])
    siamese_path = os.path.join(model_dir, CURRENT_MODEL_VERSION["siamese_model"])
    
    if not os.path.exists(yolo_path):
        print(f"[警告] YOLO 模型文件不存在: {yolo_path}")
        return False
    if not os.path.exists(siamese_path):
        print(f"[警告] Siamese 模型文件不存在: {siamese_path}")
        return False
    
    # 获取模型文件大小
    yolo_size = os.path.getsize(yolo_path) / 1024  # KB
    siamese_size = os.path.getsize(siamese_path) / 1024  # KB
    
    print(f"[模型] 版本: {CURRENT_MODEL_VERSION['version']}")
    print(f"[模型] YOLO: {CURRENT_MODEL_VERSION['yolo_model']} ({yolo_size:.1f} KB)")
    print(f"[模型] Siamese: {CURRENT_MODEL_VERSION['siamese_model']} ({siamese_size:.1f} KB)")
    print(f"[模型] 更新日期: {CURRENT_MODEL_VERSION['update_date']}")
    
    # 检查 version.json 文件
    if os.path.exists(MODEL_VERSION_FILE):
        try:
            with open(MODEL_VERSION_FILE, 'r', encoding='utf-8') as f:
                saved_version = json.load(f)
                if saved_version.get("version") != CURRENT_MODEL_VERSION["version"]:
                    print(f"[提示] 模型版本可能有更新，当前: {saved_version.get('version')} → 最新: {CURRENT_MODEL_VERSION['version']}")
        except Exception as e:
            print(f"[警告] 无法读取版本文件: {e}")
    else:
        # 创建版本文件
        try:
            with open(MODEL_VERSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(CURRENT_MODEL_VERSION, f, indent=2, ensure_ascii=False)
            print(f"[模型] 已创建版本记录文件")
        except Exception as e:
            print(f"[警告] 无法创建版本文件: {e}")
    
    return True

print("="*50)
print("  文字点选验证码识别服务")
print("="*50)
print(f"[服务] 地址: http://localhost:8000")
print(f"[API] 文档: http://localhost:8000/docs")
print(f"[ReDoc] 文档: http://localhost:8000/redoc")
check_model_version()
print("="*50)

if __name__ == '__main__':
    uvicorn.run(main.app, host="127.0.0.1", port=8000)
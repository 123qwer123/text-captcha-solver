# 智谱清言 GLM 过验证码

自动识别并点击腾讯云 / 极验文字点选验证码（YOLO + Siamese + Hungarian 匹配）。

## ⚠️ 使用前提

**本脚本必须配合本地 Python 识别服务才能工作**，脚本本身只负责前端交互，文字定位和顺序判定由本地 API 完成。

请先部署后端服务，详见 GitHub 仓库：  
https://github.com/Dingtaiqi/text-captcha-solver

```bash
git clone https://github.com/Dingtaiqi/text-captcha-solver.git
cd text-captcha-solver
pip install -r requirements.txt
python service.py
```

服务启动后访问 `http://127.0.0.1:8000/docs` 确认运行正常。

## 功能

- 检测页面中的腾讯云 / 极验文字点选验证码
- 自动提取背景图和提示文字，调用本地 API 获取点击坐标
- 按正确顺序依次点击，自动提交
- 支持循环识别（同一页面多次验证码）
- GPU 加速（DirectML）

## 支持的平台

- 腾讯云验证码 (Tencent CAPTCHA)
- 极验 (GeeTest) 文字点选
- 其他使用类似 DOM 结构的文字点选验证码

## 技术细节

- YOLO ONNX 定位文字区域
- Siamese 孪生网络 + Hungarian 算法确定点击顺序
- 宋体渲染匹配文字特征

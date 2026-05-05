# 腾讯云文字点选验证码自动识别

> 💡 **项目动机**  
> 限量发售？官方从来不说每天到底放了多少，抢购窗口短到离谱——基本不到2分钟就被一抢而空，晚1分钟点进去就只能看见第二天的10:00的通知。   
> 而整个抢购流程里，最让人血压飙升的根本不是网速，是抢到一半突然弹出的文字点选验证码。手忙脚乱点错一个字，前面的全白费，当场一肚子脾气。  
> 索性不手动点了，写套东西让它自己过——于是就有了这个本地自动识别服务 + 油猴脚本的组合，帮你在抢码的那两分钟里直接绕过验证码，专心等付款就行了。

本地 Python 服务 + 油猴脚本，自动识别并点击腾讯云/极验文字点选验证码。

## 架构

```text
油猴脚本 (浏览器)
  → 检测验证码弹窗 → 提取背景图URL + 提示文字
  → POST localhost:8000/api/v1/identify
    → Python 服务下载图片
    → YOLO 定位文字位置 → Siamese + Hungarian 确定点击顺序
    → 返回坐标
  → 映射到页面坐标 → 依次点击 → 提交
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
# 或
pip install -r requirements.txt
```

### 2. 下载模型文件

将 `best_v3.onnx`（YOLO 检测）和 `pre_model_v7.onnx`（Siamese 匹配）放入 `model/` 目录。

### 3. 启动服务

```bash
python service.py
```

服务运行在 `http://127.0.0.1:8000`，API 文档见 `/docs`。

### 4. 安装油猴脚本

在 Tampermonkey 中导入 `text_select_captcha.user.js`，脚本会自动检测页面中的验证码并调用本地 API。

## API

### POST /api/v1/identify

```json
{
  "dataType": 1,
  "imageSource": "https://example.com/captcha.jpg",
  "imageID": "optional",
  "prompt": "请依次点击：般 弛 埠"
}
```

**响应：**

```json
{
  "code": 200,
  "data": {
    "imageID": "",
    "res": {
      "imgW": 344,
      "imgH": 384,
      "point": [
        {"x_rel": 159.0, "y_rel": 209.0},
        {"x_rel": 260.5, "y_rel": 229.5},
        {"x_rel": 122.5, "y_rel": 105.0}
      ]
    }
  }
}
```

## 项目结构

```text
├── app/                             # FastAPI 服务
│   ├── api/endpoints/dianxuan.py    # API 端点
│   ├── api/router.py
│   ├── main.py                      # 应用入口
│   ├── models/input.py              # 请求模型
│   ├── services/operation.py        # 推理服务
│   └── utils/errors.py
├── model/                           # ONNX 模型文件（需自行下载）
├── src/                             # 核心识别逻辑
│   ├── captcha.py                   # 主识别类
│   └── utils/
│       ├── matchingMode.py          # 贪心/Hungarian 匹配
│       ├── ver_onnx.py              # Siamese 孪生网络
│       └── yolo_onnx.py             # YOLO 目标检测
├── requirements.txt
├── service.py                       # 启动入口
└── text_select_captcha.user.js      # 油猴脚本
```

## 技术方案

| 环节 | 方案 |
| --- | --- |
| 文字定位 | YOLO ONNX 模型，支持 DirectML GPU 推理 |
| 顺序判定 | 宋体渲染 + Siamese 孪生网络 + Hungarian 全局最优匹配 |
| 降级策略 | 高置信度 class 0 → 降阈值 class 0 → class 2 补充 |
| 验证码兼容 | 腾讯云、极验 |

## 注意事项

- 需要 Windows 字体 `simsun.ttc`（宋体），Linux/macOS 需自行配置字体路径
- GPU 加速需要 DirectX 12 兼容显卡（DirectML），CPU 也可运行但较慢
- 模型文件未包含在仓库中，需自行训练或获取

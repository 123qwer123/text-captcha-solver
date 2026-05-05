# !/usr/bin/env python
# -*-coding:utf-8 -*-

import os
import re
from typing import List, Dict, Any, Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import linear_sum_assignment

from src.utils import ver_onnx
from src.utils import yolo_onnx
from src.utils import matchingMode


class TextSelectCaptcha(object):
    _font = None

    def __init__(self, per_path: str = 'pre_model_v7.onnx', yolo_path: str = 'best_v3.onnx') -> None:
        save_path = os.path.join(os.path.dirname(__file__), '../model')
        path = lambda a, b: os.path.join(a, b)
        per_path = path(save_path, per_path)
        yolo_path = path(save_path, yolo_path)
        self.yolo = yolo_onnx.YOLO(yolo_path)
        self.pre = ver_onnx.PreONNX(per_path)

    def detection(self, image_path: str) -> List[List[float]]:
        img = matchingMode.open_image(image_path)
        data = self.yolo.inference(img)
        return data

    def run(self, image_path: str) -> List[List[float]]:
        return self._run_img(matchingMode.open_image(image_path))

    def _run_img(self, img):
        data = self.yolo.inference(img)
        target_boxes = [item[:4] for item in data if len(item) >= 6 and item[5] == 0]
        char_boxes = [item[:4] for item in data if len(item) >= 6 and item[5] == 2]
        # 检测太少时降阈值重试
        if len(target_boxes) < 2:
            data = self.yolo.inference(img, conf_threshold=0.1)
            target_boxes = [item[:4] for item in data if len(item) >= 6 and item[5] == 0]
            char_boxes = [item[:4] for item in data if len(item) >= 6 and item[5] == 2]
        char_boxes.sort(key=lambda box: box[0])
        if not target_boxes:
            return []
        if not char_boxes:
            target_boxes.sort(key=lambda box: (box[1], box[0]))
            return target_boxes
        img_targets = [img[int(box[1]):int(box[3]), int(box[0]):int(box[2])] for box in target_boxes]
        chars = [img[int(box[1]):int(box[3]), int(box[0]):int(box[2])] for box in char_boxes]
        slys = self.pre.reason_all_batch(chars, img_targets)
        sorted_result = matchingMode.find_overall_index_fast(slys)
        return [target_boxes[j] for i, j in sorted_result]

    def run_with_prompt(self, image_path, prompt: str) -> List[List[float]]:
        return self._run_with_prompt_img(matchingMode.open_image(image_path), prompt)

    def _run_with_prompt_img(self, img, prompt: str) -> List[List[float]]:
        chars_to_click = self._parse_prompt(prompt)
        if not chars_to_click:
            return []

        N = len(chars_to_click)
        print(f"[run_with_prompt] 解析提示文字({N}个): {chars_to_click}")

        # YOLO 检测 class 0：先用默认阈值，不够再降阈值
        data = self.yolo.inference(img)
        targets = [(item[:4], item[4]) for item in data if len(item) >= 6 and item[5] == 0]
        full_data = data
        if len(targets) < N:
            print(f"[run_with_prompt] 默认阈值仅检出 {len(targets)}/{N} 个目标，降阈值重试")
            full_data = self.yolo.inference(img, conf_threshold=0.1)
            targets = [(item[:4], item[4]) for item in full_data if len(item) >= 6 and item[5] == 0]

        # 仍不够：用 class 2 作为补充
        if len(targets) < N:
            extra = [(item[:4], item[4]) for item in full_data
                     if len(item) >= 6 and item[5] == 2 and item[4] > 0.1]
            extra = [e for e in extra if not any(
                self._iou_overlap(e[0], t[0]) > 0.3 for t in targets)]
            extra.sort(key=lambda t: t[1], reverse=True)
            targets.extend(extra)
            print(f"[run_with_prompt] 加入 class 2 补充后: {len(targets)}/{N} 个目标")

        targets.sort(key=lambda t: t[1], reverse=True)
        targets = targets[:N]

        print(f"[run_with_prompt] 最终使用 {len(targets)}/{N} 个目标, 置信度: {[round(t[1], 3) for t in targets]}")

        if len(targets) < N:
            return [t[0] for t in targets]

        boxes = [t[0] for t in targets]

        # Siamese + Hungarian
        img_targets = [img[int(b[1]):int(b[3]), int(b[0]):int(b[2])] for b in boxes]
        char_imgs = self._render_chars(chars_to_click, target_sizes=[(c.shape[1], c.shape[0]) for c in img_targets])
        slys = self.pre.reason_all_batch(char_imgs, img_targets)

        cost = -np.array(slys)
        _, col_ind = linear_sum_assignment(cost)
        ordered = [boxes[j] for j in col_ind]
        return ordered

    @staticmethod
    def _iou_overlap(a, b):
        x1 = max(a[0], b[0]); y1 = max(a[1], b[1])
        x2 = min(a[2], b[2]); y2 = min(a[3], b[3])
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inter = (x2 - x1) * (y2 - y1)
        area_a = (a[2] - a[0]) * (a[3] - a[1])
        area_b = (b[2] - b[0]) * (b[3] - b[1])
        return inter / (area_a + area_b - inter)

    def run_dict(self, image_path, prompt: Optional[str] = None) -> Dict[str, Any]:
        img = matchingMode.open_image(image_path)
        h, w, _ = img.shape
        if prompt:
            result = self._run_with_prompt_img(img, prompt)
        else:
            result = self._run_img(img)
        return {
            "imgW": w, "imgH": h,
            "point": [{"x_rel": (x1 + x2) / 2, "y_rel": (y1 + y2) / 2} for x1, y1, x2, y2 in result],
            "corp": [{"x1": x1, "y1": y1, "x2": x2, "y2": y2} for x1, y1, x2, y2 in result],
        }

    @staticmethod
    def _parse_prompt(prompt: str) -> List[str]:
        # 用 rfind 找最后一个 ： 或 : 作为分隔点
        idx = max(prompt.rfind('：'), prompt.rfind(':'))
        if idx >= 0:
            cleaned = prompt[idx + 1:].strip()
        else:
            # 无冒号，尝试去掉常见前缀
            cleaned = re.sub(r'^.*?(?:点击|依次|按顺序|顺序)', '', prompt).strip()
        chars = [c for c in re.split(r'[\s,，、]+', cleaned) if c and len(c) == 1]
        return chars if chars else [c for c in prompt if '一' <= c <= '鿿']

    @classmethod
    def _render_chars(cls, chars: List[str], target_sizes=None) -> List[np.ndarray]:
        if cls._font is None:
            font_paths = [
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simsun.ttf",
            ]
            font = None
            for fp in font_paths:
                if os.path.exists(fp):
                    try:
                        font = ImageFont.truetype(fp, 80)
                        break
                    except Exception:
                        continue
            if font is None:
                font = ImageFont.load_default()
            cls._font = font
        text_rgb = (227, 179, 76)
        result = []
        for i, char in enumerate(chars):
            sz = 112
            img = Image.new('RGB', (sz, sz), (225, 225, 225))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), char, font=cls._font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            cx = (sz - tw) // 2 - bbox[0]
            cy = (sz - th) // 2 - bbox[1]
            draw.text((cx, cy), char, font=cls._font, fill=text_rgb)
            arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            arr = cv2.GaussianBlur(arr, (5, 5), 1.0)
            if target_sizes and i < len(target_sizes):
                tw, th = target_sizes[i]
                arr = cv2.resize(arr, (tw, th))
            result.append(arr)
        return result


if __name__ == '__main__':
    cap = TextSelectCaptcha()
    # 用法示例：
    # result = cap.run("path/to/image.jpg")
    # print(result)
    # print(cap.run_dict("path/to/image.jpg", prompt="请依次点击：般 弛 埠"))

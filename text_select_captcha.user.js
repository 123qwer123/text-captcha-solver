// ==UserScript==
// @name         智谱清言GLM过验证码
// @namespace    https://github.com/Dingtaiqi/text-captcha-solver
// @version      1.4
// @description  自动识别并点击腾讯云/极验文字点选验证码，YOLO+Siamese+Hungarian匹配。
// @description  使用前必须本地运行识别API服务，详见GitHub仓库：
// @description  https://github.com/Dingtaiqi/text-captcha-solver
// @author       Dingtaiqi
// @match        *://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @connect      localhost
// @connect      127.0.0.1
// @license      MIT
// @homepageURL  https://github.com/Dingtaiqi/text-captcha-solver
// @supportURL   https://github.com/Dingtaiqi/text-captcha-solver/issues
// @updateURL    https://raw.githubusercontent.com/Dingtaiqi/text-captcha-solver/main/text_select_captcha.user.js
// @downloadURL  https://raw.githubusercontent.com/Dingtaiqi/text-captcha-solver/main/text_select_captcha.user.js
// ==/UserScript==

(function () {
    'use strict';

    const CONFIG = {
        apiUrl: 'http://127.0.0.1:8000/api/v1/identify',
        debug: true,
        clickInterval: 150,
        submitWait: 300,
        jitter: 3,
        containerSelectors: [
            '#tCaptchaDyMainWrap',
            '.tencent-captcha-dy__warp',
            '.tencent-captcha-dy__click-type-wrap',
            '.geetest_panel',
            '.geetest_widget',
            '.captcha-modal',
            '.verify-modal',
            'div[id*="captcha"]',
            'div[class*="captcha"]',
        ],
        submitSelectors: [
            '.tencent-captcha-dy__verify-confirm-btn',
            '.geetest_commit_tip',
            '.geetest_commit',
            '.geetest_btn',
            '.captcha-submit',
            '.verify-submit',
            'div[class*="commit"]',
            'div[class*="submit"]',
        ],
        promptSelectors: [
            '.tencent-captcha-dy__header-text',
            '.geetest_tip',
            '.captcha-prompt',
            '.verify-prompt',
            '.geetest_header',
        ],
    };

    function log(...args) { if (CONFIG.debug) console.log('[TextSelectCaptcha]', ...args); }
    function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

    function identifyCaptcha(imageUrl, prompt) {
        const data = { dataType: 1, imageSource: imageUrl, imageID: Date.now().toString() };
        if (prompt) data.prompt = prompt;
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'POST', url: CONFIG.apiUrl,
                data: JSON.stringify(data),
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000,
                onload: resp => {
                    try {
                        const r = JSON.parse(resp.responseText);
                        r.code === 200 ? resolve(r.data.res) : reject(new Error('API: ' + r.msg));
                    } catch (e) { reject(new Error('解析API响应失败: ' + e.message)); }
                },
                onerror: () => reject(new Error('请求API失败，确认服务已启动 (python service.py)')),
                ontimeout: () => reject(new Error('API请求超时')),
            });
        });
    }

    function extractCaptchaImage(container) {
        // 1) 腾讯云：背景图在 .verify-bg-img 的 background-image
        const bgImg = container.querySelector('.tencent-captcha-dy__verify-bg-img');
        if (bgImg) {
            const s = bgImg.getAttribute('style');
            if (s) {
                const m = s.match(/url\(["']?(.+?)["']?\)/);
                if (m && m[1].length > 100) return normalizeUrl(m[1]);
            }
        }
        // 2) 容器自身的 background-image
        const selfStyle = container.getAttribute('style');
        if (selfStyle) {
            const m = selfStyle.match(/url\(["']?(.+?)["']?\)/);
            if (m) return normalizeUrl(m[1]);
        }
        // 3) 遍历子元素找 background-image（跳过 data: 小图）
        for (const el of container.querySelectorAll('*')) {
            const bg = window.getComputedStyle(el).backgroundImage;
            if (bg && bg !== 'none') {
                const m = bg.match(/url\(["']?(.+?)["']?\)/);
                if (m && !m[1].startsWith('data:image')) return normalizeUrl(m[1]);
            }
        }
        // 4) img 元素（跳过 tiny data: 图标）
        for (const img of container.querySelectorAll('img')) {
            if (img.src && img.src.startsWith('data:') && img.src.length < 5000) continue;
            if (img.src) return img.src;
        }
        // 5) canvas
        const c = container.querySelector('canvas');
        if (c) { try { return c.toDataURL('image/jpeg'); } catch (e) {} }
        return null;
    }

    function normalizeUrl(url) {
        if (url.startsWith('//')) return location.protocol + url;
        if (url.startsWith('/')) return location.origin + url;
        return url;
    }

    function findPromptText() {
        for (const sel of CONFIG.promptSelectors) {
            const el = document.querySelector(sel);
            if (!el) continue;
            const aria = el.getAttribute('aria-label');
            if (aria && aria.includes('点击')) return aria;
            const text = el.textContent.trim();
            if (text && text.includes('点击')) return text;
        }
        return null;
    }

    function getClickArea(container) {
        for (const sel of ['.tencent-captcha-dy__verify-bg-img', '.tencent-captcha-dy__verify-bg',
                          '.tencent-captcha-dy__image-area', '.geetest_item_wrap']) {
            const el = container.querySelector(sel);
            if (el && el.offsetHeight > 0) return el;
        }
        return container;
    }

    function findVisible(selectors) {
        for (const sel of selectors) {
            const el = document.querySelector(sel);
            if (el && el.offsetParent !== null) return el;
        }
        return null;
    }

    function simulateClick(targetEl, clientX, clientY) {
        clientX += (Math.random() - 0.5) * 2 * CONFIG.jitter;
        clientY += (Math.random() - 0.5) * 2 * CONFIG.jitter;
        const o = { bubbles: true, cancelable: true, clientX, clientY, button: 0 };
        targetEl.dispatchEvent(new MouseEvent('mouseover', o));
        targetEl.dispatchEvent(new MouseEvent('mousemove', o));
        return wait(30 + Math.random() * 50).then(() => {
            targetEl.dispatchEvent(new MouseEvent('mousedown', o));
            return wait(40 + Math.random() * 40);
        }).then(() => {
            targetEl.dispatchEvent(new MouseEvent('mouseup', o));
            targetEl.dispatchEvent(new MouseEvent('click', o));
            log(`点击: (${clientX.toFixed(1)}, ${clientY.toFixed(1)})`);
        });
    }

    // ===================== 关闭空结果弹窗 =====================
    function closeEmptyDialog() {
        const dialog = document.querySelector('.pay-dialog .empty-data-wrap');
        if (!dialog) return false;
        const closeBtn = document.querySelector('.pay-dialog .el-dialog__headerbtn');
        if (closeBtn) {
            closeBtn.click();
            log('已关闭 "当前购买人数较多" 弹窗');
            return true;
        }
        return false;
    }

    let dialogObserver;
    function startDialogWatcher() {
        if (dialogObserver) dialogObserver.disconnect();
        dialogObserver = new MutationObserver(() => {
            if (closeEmptyDialog()) return;
            // 也监控文本内容变化（弹窗可能有异步加载）
            const p = document.querySelector('.pay-dialog .empty-data-wrap p');
            if (p && p.textContent.includes('当前购买人数较多')) {
                const closeBtn = document.querySelector('.pay-dialog .el-dialog__headerbtn');
                if (closeBtn) closeBtn.click();
            }
        });
        dialogObserver.observe(document.body, { childList: true, subtree: true, characterData: true });
        log('弹窗监控已启动');
    }

    // ===================== 主逻辑 =====================
    let isProcessing = false;
    let solvedImages = new Set();  // 用图片URL去重，新图自动解

    async function handleCaptcha() {
        if (isProcessing) return;
        const container = findVisible(CONFIG.containerSelectors);
        if (!container) return;

        // 先提取图片URL作为唯一标识
        const imageUrl = extractCaptchaImage(container);
        if (!imageUrl) return;
        if (solvedImages.has(imageUrl)) return;

        isProcessing = true;
        try {
            log('验证码图片URL:', imageUrl.slice(0, 80) + '...');
            const prompt = findPromptText();
            if (prompt) log('提示文字:', prompt);

            GM_notification({ text: '识别验证码中...', timeout: 2000 });
            const result = await identifyCaptcha(imageUrl, prompt);
            log('识别结果:', result);

            // 等待渲染完成
            let clickArea, imgBox;
            for (let i = 0; i < 8; i++) {
                clickArea = getClickArea(container);
                imgBox = clickArea.getBoundingClientRect();
                if (imgBox.width > 0 && imgBox.height > 0) break;
                await wait(200);
            }
            if (!imgBox || imgBox.width === 0 || imgBox.height === 0)
                throw new Error('获取点击区域尺寸失败');

            log(`区域: (${imgBox.left.toFixed(1)},${imgBox.top.toFixed(1)}) ${imgBox.width}x${imgBox.height}`);

            const sx = imgBox.width / result.imgW;
            const sy = imgBox.height / result.imgH;

            for (let i = 0; i < result.point.length; i++) {
                const pt = result.point[i];
                const x = imgBox.left + pt.x_rel * sx;
                const y = imgBox.top + pt.y_rel * sy;
                log(`[${i+1}/${result.point.length}] -> (${x.toFixed(1)},${y.toFixed(1)})`);
                await simulateClick(clickArea, x, y);
                await wait(CONFIG.clickInterval);
            }

            // 点提交按钮
            const btn = findVisible(CONFIG.submitSelectors);
            if (btn) {
                await wait(200);
                if (btn.classList.contains('tencent-captcha-dy__verify-confirm-btn--disabled')) {
                    for (let i = 0; i < 8; i++) { await wait(200); if (!btn.classList.contains('tencent-captcha-dy__verify-confirm-btn--disabled')) break; }
                }
                btn.click();
                log('已点提交');
            }

            solvedImages.add(imageUrl);
            GM_notification({ text: '验证码通过！', timeout: 2000 });
            log('✓ 完成');

            // 提交后检查是否为空的错误弹窗，是则自动关掉
            await wait(500);
            closeEmptyDialog();

        } catch (err) {
            log('✗ 失败:', err.message);
            GM_notification({ text: '识别失败: ' + err.message, timeout: 4000 });
        } finally {
            await wait(CONFIG.submitWait);
            isProcessing = false;
        }
    }

    // ===================== 监听 =====================
    let observer;
    function startObserver() {
        if (observer) observer.disconnect();
        observer = new MutationObserver(() => {
            const c = findVisible(CONFIG.containerSelectors);
            if (!c) return;
            const url = extractCaptchaImage(c);
            if (url && !solvedImages.has(url)) {
                log('检测到验证码');
                setTimeout(handleCaptcha, 200);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
        log('observer已启动');
    }

    let pollTimer;
    function startPolling() {
        clearInterval(pollTimer);
        pollTimer = setInterval(() => {
            if (isProcessing) return;
            const c = findVisible(CONFIG.containerSelectors);
            if (!c) return;
            const url = extractCaptchaImage(c);
            if (url && !solvedImages.has(url)) handleCaptcha();
        }, 2000);
        log('轮询已启动(2s)');
    }

    function init() {
        log('脚本已加载 v1.4');
        if (document.body) { startObserver(); startPolling(); startDialogWatcher(); }
        else document.addEventListener('DOMContentLoaded', () => { startObserver(); startPolling(); startDialogWatcher(); });
        window.__tc = {
            config: CONFIG, handleNow: handleCaptcha, solved: solvedImages,
            reset: () => { solvedImages.clear(); log('已重置'); },
        };
    }
    init();
})();
# 发布到 GitHub Pages

GitHub Pages 只能运行静态网页，因此上传 `index.html` 即可。`paddle_ocr_server.py` 是 Python 后端，不能由 GitHub Pages 直接运行。

## 网页端发布

1. 登录 GitHub，点击右上角 **+ → New repository**。
2. 仓库名可填写：`smart-expense-demo`。
3. 创建仓库后，点击 **Add file → Upload files**。
4. 上传本目录中的 `index.html`。如果希望保留说明，也可以同时上传 `README.md`。
5. 点击 **Commit changes**。
6. 打开仓库的 **Settings → Pages**。
7. 在 **Build and deployment** 中选择：
   - Source：`Deploy from a branch`
   - Branch：`main`
   - Folder：`/(root)`
8. 点击 **Save**，等待约 1–3 分钟。

发布链接通常是：

```text
https://你的GitHub用户名.github.io/smart-expense-demo/
```

## 关于 PaddleOCR

GitHub Pages 上的页面仍然可以使用浏览器 OCR。若要使用 PaddleOCR 专用服务，需要把 `paddle_ocr_server.py` 单独部署到云服务器、Render 或 Railway，并把 `index.html` 中的 `OCR_API` 改成后端公网地址，例如：

```js
const OCR_API = 'https://你的后端域名/api/invoice-ocr';
```

不要把企业真实发票或密钥提交到公开 GitHub 仓库。

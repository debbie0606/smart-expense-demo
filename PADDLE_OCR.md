# 接入 PaddleOCR

当前页面会优先请求同源接口 `POST /api/invoice-ocr`。接口不可用时，页面会自动回退到浏览器端 OCR。

## 本地启动

在 `outputs` 目录执行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python paddle_ocr_server.py
```

然后打开 <http://127.0.0.1:8000>，上传发票即可使用 PaddleOCR。

首次启动会下载 PaddleOCR 模型，耗时取决于网络速度。生产环境请把 CORS 的 `allow_origins` 改成实际域名，并将服务部署在有足够内存的服务器上。

## 识别策略

- PDF：前端提取第一页并高清渲染为图片，再发送给 PaddleOCR。
- 图片：直接发送原图给 PaddleOCR。
- 服务不可用：自动切换到浏览器端 Tesseract OCR。
- 发票税务验真：仍需另接合规的税务查验或第三方发票服务。

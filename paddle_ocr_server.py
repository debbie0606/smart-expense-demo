"""本地发票 OCR 服务：PaddleOCR 优先，供 outputs/index.html 调用。"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from paddleocr import PaddleOCR
except ImportError as exc:  # pragma: no cover - 提示用户安装依赖
    raise RuntimeError("请先安装 requirements.txt 中的 PaddleOCR 依赖") from exc

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="票智发票 OCR 服务")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 中文文档方向和去畸变能明显改善手机拍摄、倾斜和扫描发票的识别效果。
try:
    ocr = PaddleOCR(
        lang="ch",
        use_doc_orientation_classify=True,
        use_doc_unwarping=True,
        use_textline_orientation=True,
    )
except TypeError:  # PaddleOCR 2.x 兼容模式
    ocr = PaddleOCR(lang="ch")


def _result_text(result) -> str:
    """兼容 PaddleOCR 2.x/3.x 的结果对象。"""
    texts: list[str] = []
    if isinstance(result, list):
        # PaddleOCR 2.x: [[[[box], (text, score)], ...]]
        for page in result:
            if not isinstance(page, list):
                continue
            for line in page:
                if isinstance(line, (list, tuple)) and len(line) >= 2 and isinstance(line[1], (list, tuple)):
                    texts.append(str(line[1][0]))
        if texts:
            return " ".join(texts)
    for item in result:
        payload = getattr(item, "json", None)
        if callable(payload):
            payload = payload()
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)
        if isinstance(payload, dict):
            data = payload.get("res", payload)
            values = data.get("rec_texts", []) if isinstance(data, dict) else []
            texts.extend(str(value) for value in values if value)
        values = getattr(item, "rec_texts", None)
        if values:
            texts.extend(str(value) for value in values if value)
    return " ".join(texts)


def parse_invoice_text(text: str) -> dict[str, str]:
    compact = re.sub(r"\s+", " ", text or "")
    date = ""
    date_match = re.search(r"20\d{2}\s*[年\-/.]\s*\d{1,2}\s*[月\-/.]\s*\d{1,2}\s*日?", compact)
    if date_match:
        date = re.sub(r"\s", "", date_match.group(0)).replace("年", "-").replace("月", "-").replace("日", "")

    labeled = re.search(r"(?:发票号码|票据号码|号码)[^0-9]{0,18}(\d{8,20})", compact)
    candidates = re.findall(r"(?<!\d)\d{8,20}(?!\d)", compact)
    number = labeled.group(1) if labeled else next((n for n in candidates if len(n) >= 19), "")
    if not number:
        number = next((n for n in candidates if len(n) == 8 and not n.startswith("91")), "")

    money = re.search(r"(?:价税合计|小写|合计金额|金额)[^0-9]{0,45}(?:¥|￥|元)?\s*([0-9]{1,3}(?:[,，][0-9]{3})*(?:\.\d{1,2})?)", compact)
    if money:
        total = "¥ " + money.group(1)
    else:
        values = re.findall(r"(?:¥|￥)\s*([0-9,]+\.\d{1,2})", compact)
        total = "¥ " + values[-1] if values else ""

    seller_match = re.search(r"(?:销售方|销方|销售名称|销售方信息)[^：:\s]{0,3}[：:\s]*([\u4e00-\u9fa5A-Za-z0-9（）()·\-]{3,40}(?:有限公司|有限责任公司|公司|酒店|铁路|商旅))", compact)
    companies = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9（）()·\-]{4,40}(?:有限公司|有限责任公司|公司|酒店|铁路|商旅)", compact)
    seller = seller_match.group(1) if seller_match else (companies[-1] if companies else "")
    return {"no": number, "date": date, "seller": seller, "total": total}


@app.post("/api/invoice-ocr")
async def invoice_ocr(file: UploadFile = File(...)):
    suffix = Path(file.filename or "invoice.png").suffix.lower() or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)
    try:
        result = ocr.predict(str(temp_path)) if hasattr(ocr, "predict") else ocr.ocr(str(temp_path), cls=True)
        text = _result_text(result)
        return {"provider": "PaddleOCR", "text": text, "fields": parse_invoice_text(text)}
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/")
def index():
    return FileResponse(ROOT / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

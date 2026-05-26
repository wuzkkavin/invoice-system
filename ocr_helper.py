import os
import json
import base64
import requests
from pathlib import Path
import config_manager

OCR_PROMPT_TAIWAN = """
以下是一張台灣的發票或收據照片，請依照以下規則進行分析：

1. 憑證判斷：
請先判斷該圖片是否屬於以下五種類型之一：
電子發票、二聯式發票、三聯式發票、免用統一發票收據、其他。

2. 欄位抽取：
- 發票號碼（invoice_no）：AA-12345678 格式（兩碼英文+八碼數字）
- 日期（date）：轉換成 YYYY-MM-DD 格式（民國年需 +1911）
- 賣方名稱（seller）：公司或商店名稱
- 統一編號（seller_tax_id）：8 碼數字
- 品名（product）：商品名稱（若有多項用逗號分隔）
- 金額（amount）：總金額，純數字（不含貨幣符號與逗號）
- 稅額（tax）：稅額，純數字

若欄位不存在，請填空字串 "" 或 0。
回覆內容需為合法 JSON，禁止其他描述性文字。
"""



def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ocr_invoice_openai(image_path):
    """使用 OpenAI Vision API 辨識發票"""
    api_key = config_manager.get_api_key("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    base64_img = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": OCR_PROMPT_TAIWAN},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{ext};base64,{base64_img}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1000
    )

    text = response.choices[0].message.content
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "無法解析 OCR 結果", "raw": text}


def ocr_invoice_gemini(image_path):
    """使用 Google Gemini API 辨識發票（預設方案）"""
    api_key = config_manager.get_api_key("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY")

    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    base64_img = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": OCR_PROMPT_TAIWAN},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{ext};base64,{base64_img}"
                        }
                    }
                ]
            }
        ],
        temperature=0.1,
        max_tokens=1000
    )

    text = response.choices[0].message.content
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "無法解析 OCR 結果", "raw": text}


def ocr_invoice_minimax(image_path):
    """使用 MiniMax-Text-01 原生 API 辨識發票"""
    api_key = config_manager.get_api_key("MINIMAX_API_KEY")
    if not api_key:
        raise SystemExit("Missing MINIMAX_API_KEY")

    base64_img = encode_image(image_path)
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    data_url = f"data:image/{ext};base64,{base64_img}"

    payload = {
        "model": "MiniMax-Text-01",
        "messages": [
            {
                "role": "user",
                "name": "user",
                "content": [
                    {"type": "text", "text": OCR_PROMPT_TAIWAN},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1000
    }

    resp = requests.post(
        "https://api.minimax.io/v1/text/chatcompletion_v2",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=60
    )

    if resp.status_code != 200:
        return {"error": f"MiniMax API 錯誤 ({resp.status_code}): {resp.text}"}

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return {"error": "無法解析 MiniMax 回應", "raw": data}

    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "無法解析 OCR 結果", "raw": text}


def pdf_to_images(pdf_path, dpi=200):
    """將 PDF 第一頁轉為 JPEG 暫存檔，回傳圖片路徑列表"""
    import fitz
    doc = fitz.open(pdf_path)
    img_paths = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=dpi)
        img_path = pdf_path.replace(".pdf", f"_page{page_num}.jpg")
        pix.save(img_path)
        img_paths.append(img_path)
    doc.close()
    return img_paths


def ocr_invoice(image_path, provider="gemini"):
    """統一的發票 OCR 入口（預設 Gemini，備用 OpenAI / MiniMax）"""
    if not os.path.exists(image_path):
        return {"error": f"圖片不存在: {image_path}"}
    if image_path.lower().endswith(".pdf"):
        images = pdf_to_images(image_path)
        if not images:
            return {"error": "PDF 轉換圖片失敗"}
        result = None
        for img in images:
            result = ocr_invoice(img, provider=provider)
            os.remove(img)
        return result if result else {"error": "OCR 辨識失敗"}
    if provider == "gemini":
        return ocr_invoice_gemini(image_path)
    if provider == "minimax":
        return ocr_invoice_minimax(image_path)
    return ocr_invoice_openai(image_path)


def map_ocr_to_fields(ocr_result):
    """將 OCR 結果對應到表單欄位"""
    mapping = {
        "invoice_no": ["發票號碼", "invoice_no", "憑證號碼"],
        "date": ["日期", "date", "憑證日期"],
        "seller": ["賣方名稱", "seller", "賣方營業人名稱", "seller_name"],
        "seller_tax_id": ["統一編號", "seller_tax_id", "賣方統編"],
        "product": ["品名", "product"],
        "amount": ["金額", "amount", "total"],
        "tax": ["稅額", "tax"],
    }

    result = {}
    for field, keys in mapping.items():
        for key in keys:
            value = ocr_result.get(key)
            if value and str(value).strip():
                result[field] = str(value).strip()
                break
        if field not in result:
            result[field] = ""

    # 清洗金額
    for num_field in ["amount", "tax"]:
        val = result.get(num_field, "0")
        val = val.replace(",", "").replace("$", "").replace("NT", "").replace(" ", "")
        try:
            result[num_field] = str(float(val))
        except ValueError:
            result[num_field] = "0"

    return result
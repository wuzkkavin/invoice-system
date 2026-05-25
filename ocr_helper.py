import os
import json
import base64
from pathlib import Path

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


def load_env_file(path):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def ocr_invoice_openai(image_path):
    """使用 OpenAI Vision API 辨識發票"""
    load_env_file(os.path.expanduser("~/.openai.env"))
    api_key = os.getenv("OPENAI_API_KEY")
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
    """使用 Google Gemini API 辨識發票（備用方案）"""
    load_env_file(os.path.expanduser("~/.openai.env"))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing API key")

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


def ocr_invoice(image_path, provider="openai"):
    """統一的發票 OCR 入口"""
    if not os.path.exists(image_path):
        return {"error": f"圖片不存在: {image_path}"}
    if image_path.lower().endswith(".pdf"):
        return {"error": "PDF 檔案不支援 OCR，請先轉為圖片"}
    if provider == "gemini":
        return ocr_invoice_gemini(image_path)
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
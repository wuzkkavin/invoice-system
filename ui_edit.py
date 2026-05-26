import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import shutil
import threading
from PIL import Image, ImageTk


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


IMAGES_DIR = os.path.join(_get_base_dir(), "images")


class EditInvoiceWindow:
    def __init__(self, parent, db_manager, invoice_id, callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.invoice_id = invoice_id
        self.callback = callback
        self.invoice_data = db_manager.get_invoice_by_id(invoice_id)

        self.win = tk.Toplevel(parent)
        self.win.title(f"檢視/編輯發票 #{invoice_id}")
        self.win.geometry("700x600")
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main_frame = tk.Frame(self.win, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.entries = {}
        fields = [
            ("發票號碼", "invoice_no"),
            ("日期", "date"),
            ("賣方名稱", "seller"),
            ("統一編號", "seller_tax_id"),
            ("品名（逗號分隔）", "product"),
            ("金額", "amount"),
            ("稅額", "tax"),
        ]

        for i, (label, key) in enumerate(fields):
            tk.Label(left_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            self.entries[key] = tk.Entry(left_frame, width=30)
            self.entries[key].grid(row=i, column=1, sticky=tk.W, pady=3)

        btn_frame = tk.Frame(left_frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="選擇新圖片", command=self.select_new_image).pack(side=tk.LEFT, padx=5)
        self.image_name_label = tk.Label(left_frame, text="", fg="gray")
        self.image_name_label.grid(row=len(fields)+1, column=0, columnspan=2, sticky=tk.W)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="發票圖片").pack()

        preview_frame = tk.Frame(right_frame, bd=1, relief=tk.SUNKEN)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview_label = tk.Label(preview_frame, text="無圖片")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.ocr_btn = tk.Button(right_frame, text="🤖 OCR 自動填入", command=self.run_ocr, bg="#e8f5e9")
        self.ocr_btn.pack(fill=tk.X, pady=2)
        self.ocr_status = tk.Label(right_frame, text="", fg="gray", font=("", 8))
        self.ocr_status.pack()

        bottom_frame = tk.Frame(self.win)
        bottom_frame.pack(fill=tk.X, pady=5)
        tk.Button(bottom_frame, text="儲存", command=self.save).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="刪除", command=self.delete).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="關閉", command=self.win.destroy).pack(side=tk.RIGHT, padx=5)

    def _load_data(self):
        if not self.invoice_data:
            messagebox.showerror("錯誤", "找不到發票資料")
            self.win.destroy()
            return

        for key, entry in self.entries.items():
            value = self.invoice_data.get(key, "")
            if value is not None:
                entry.insert(0, str(value))

        if self.invoice_data.get("image_path"):
            self.image_name_label.config(text=self.invoice_data["image_path"])
            self._show_image(self.invoice_data["image_path"])

    def _show_image(self, filename):
        if not filename:
            return
        path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(path):
            self.preview_label.config(text="圖片檔案不存在")
            return
        try:
            if path.lower().endswith(".pdf"):
                self.preview_label.config(text="PDF 檔案（無法預覽）")
            else:
                img = Image.open(path)
                img.thumbnail((300, 400))
                self.preview_photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.preview_photo, text="")
        except Exception as e:
            self.preview_label.config(text=f"無法預覽: {e}")

    def select_new_image(self):
        file_path = filedialog.askopenfilename(
            title="選擇新圖片",
            filetypes=[
                ("圖片檔案", "*.jpg *.jpeg *.png *.pdf"),
                ("所有檔案", "*.*")
            ]
        )
        if file_path:
            self.new_image_path = file_path
            self.image_name_label.config(text=f"新圖片: {os.path.basename(file_path)}")
            self._show_image(file_path)

    def run_ocr(self):
        path = None
        if hasattr(self, "new_image_path") and self.new_image_path:
            path = self.new_image_path
        elif self.invoice_data and self.invoice_data.get("image_path"):
            path = os.path.join(IMAGES_DIR, self.invoice_data["image_path"])

        if not path or not os.path.exists(path):
            messagebox.showinfo("提示", "沒有可用的圖片進行 OCR")
            return
        if path.lower().endswith(".pdf"):
            messagebox.showwarning("警告", "PDF 不支援 OCR")
            return

        self.ocr_btn.config(state=tk.DISABLED, text="辨識中...")
        self.ocr_status.config(text="正在呼叫 AI 辨識...")

        def do_ocr():
            try:
                from ocr_helper import ocr_invoice, map_ocr_to_fields
                result = ocr_invoice(path)
                if "error" in result:
                    self.win.after(0, lambda: self.ocr_status.config(text=f"辨識失敗: {result['error']}", fg="red"))
                else:
                    fields = map_ocr_to_fields(result)
                    self.win.after(0, lambda: self._fill_ocr_result(fields))
                    self.win.after(0, lambda: self.ocr_status.config(text="✅ OCR 完成", fg="green"))
            except Exception as e:
                self.win.after(0, lambda: self.ocr_status.config(text=f"錯誤: {e}", fg="red"))
            finally:
                self.win.after(0, lambda: self.ocr_btn.config(state=tk.NORMAL, text="🤖 OCR 自動填入"))

        threading.Thread(target=do_ocr, daemon=True).start()

    def _fill_ocr_result(self, fields):
        mapping = {
            "invoice_no": self.entries["invoice_no"],
            "date": self.entries["date"],
            "seller": self.entries["seller"],
            "seller_tax_id": self.entries["seller_tax_id"],
            "product": self.entries["product"],
            "amount": self.entries["amount"],
            "tax": self.entries["tax"],
        }
        for key, entry in mapping.items():
            value = fields.get(key, "")
            if value and not entry.get():
                entry.delete(0, tk.END)
                entry.insert(0, value)

    def save(self):
        invoice_no = self.entries["invoice_no"].get().strip()
        date = self.entries["date"].get().strip()
        if not invoice_no or not date:
            messagebox.showwarning("警告", "發票號碼和日期不可為空")
            return

        data = {
            "invoice_no": invoice_no,
            "date": date,
            "seller": self.entries["seller"].get().strip(),
            "seller_tax_id": self.entries["seller_tax_id"].get().strip(),
            "product": self.entries["product"].get().strip(),
            "amount": float(self.entries["amount"].get()) if self.entries["amount"].get() else 0,
            "tax": float(self.entries["tax"].get()) if self.entries["tax"].get() else 0,
        }

        image_filename = None
        if hasattr(self, "new_image_path") and self.new_image_path:
            ext = os.path.splitext(self.new_image_path)[1].lower()
            if ext == ".jpeg":
                ext = ".jpg"
            filename = f"{date}_{invoice_no}{ext}"
            dest = os.path.join(IMAGES_DIR, filename)
            try:
                if self.new_image_path.lower().endswith(".pdf"):
                    shutil.copy(self.new_image_path, dest)
                else:
                    img = Image.open(self.new_image_path)
                    img.convert("RGB").save(dest, "JPEG", quality=85)
                image_filename = filename
            except Exception as e:
                messagebox.showerror("錯誤", f"圖片儲存失敗: {e}")
                return

        try:
            self.db_manager.update_invoice(self.invoice_id, data, image_filename)
            messagebox.showinfo("成功", "發票已更新")
            if self.callback:
                self.callback()
            self.win.destroy()
        except Exception as e:
            messagebox.showerror("錯誤", f"更新失敗: {e}")

    def delete(self):
        if messagebox.askyesno("確認刪除", "確定要刪除這筆發票嗎？"):
            try:
                self.db_manager.delete_invoice(self.invoice_id)
                messagebox.showinfo("成功", "發票已刪除")
                if self.callback:
                    self.callback()
                self.win.destroy()
            except Exception as e:
                messagebox.showerror("錯誤", f"刪除失敗: {e}")
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import threading
from datetime import datetime
from PIL import Image, ImageTk

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")


class AddInvoiceWindow:
    def __init__(self, parent, db_manager, callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.image_files = []
        self.image_labels = []
        self.current_index = 0
        self.entries = {}
        self.preview_label = None

        self.win = tk.Toplevel(parent)
        self.win.title("新增發票")
        self.win.geometry("700x600")
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()

    def _build_ui(self):
        main_frame = tk.Frame(self.win, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="發票號碼").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.entries["invoice_no"] = tk.Entry(left_frame, width=30)
        self.entries["invoice_no"].grid(row=0, column=1, sticky=tk.W, pady=3)

        tk.Label(left_frame, text="日期").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.entries["date"] = tk.Entry(left_frame, width=30)
        self.entries["date"].grid(row=1, column=1, sticky=tk.W, pady=3)
        self.entries["date"].insert(0, datetime.today().strftime("%Y-%m-%d"))

        tk.Label(left_frame, text="賣方名稱").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.entries["seller"] = tk.Entry(left_frame, width=30)
        self.entries["seller"].grid(row=2, column=1, sticky=tk.W, pady=3)

        tk.Label(left_frame, text="統一編號").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.entries["seller_tax_id"] = tk.Entry(left_frame, width=30)
        self.entries["seller_tax_id"].grid(row=3, column=1, sticky=tk.W, pady=3)

        tk.Label(left_frame, text="品名（逗號分隔）").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.entries["product"] = tk.Entry(left_frame, width=30)
        self.entries["product"].grid(row=4, column=1, sticky=tk.W, pady=3)

        tk.Label(left_frame, text="金額").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.entries["amount"] = tk.Entry(left_frame, width=30)
        self.entries["amount"].grid(row=5, column=1, sticky=tk.W, pady=3)

        tk.Label(left_frame, text="稅額").grid(row=6, column=0, sticky=tk.W, pady=3)
        self.entries["tax"] = tk.Entry(left_frame, width=30)
        self.entries["tax"].grid(row=6, column=1, sticky=tk.W, pady=3)

        btn_frame = tk.Frame(left_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="選擇圖片（可多選）", command=self.select_images).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="清除圖片", command=self.clear_images).pack(side=tk.LEFT, padx=5)

        self.image_list_label = tk.Label(left_frame, text="已選取 0 張圖片", fg="gray")
        self.image_list_label.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="圖片預覽").pack()

        preview_frame = tk.Frame(right_frame, bd=1, relief=tk.SUNKEN)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.preview_label = tk.Label(preview_frame, text="尚未選擇圖片")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        nav_frame = tk.Frame(right_frame)
        nav_frame.pack(fill=tk.X)
        self.nav_label = tk.Label(nav_frame, text="")
        self.nav_label.pack(side=tk.LEFT)
        tk.Button(nav_frame, text="< 上一張", command=self.prev_image).pack(side=tk.RIGHT, padx=2)
        tk.Button(nav_frame, text="下一張 >", command=self.next_image).pack(side=tk.RIGHT, padx=2)

        ocr_frame = tk.Frame(right_frame)
        ocr_frame.pack(fill=tk.X, pady=5)
        self.ocr_btn = tk.Button(ocr_frame, text="🤖 OCR 自動辨識", command=self.run_ocr, bg="#e8f5e9")
        self.ocr_btn.pack(fill=tk.X)
        self.ocr_status = tk.Label(ocr_frame, text="", fg="gray", font=("", 8))
        self.ocr_status.pack()

        bottom_frame = tk.Frame(self.win)
        bottom_frame.pack(fill=tk.X, pady=5)
        tk.Button(bottom_frame, text="儲存並新增下一筆", command=self.save_and_continue).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="儲存並關閉", command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="取消", command=self.win.destroy).pack(side=tk.RIGHT, padx=5)

    def select_images(self):
        files = filedialog.askopenfilenames(
            title="選擇發票圖片",
            filetypes=[
                ("圖片檔案", "*.jpg *.jpeg *.png *.pdf"),
                ("所有檔案", "*.*")
            ]
        )
        if files:
            self.image_files = list(files)
            self.current_index = 0
            self.update_image_list_label()
            self.show_preview()

    def clear_images(self):
        self.image_files = []
        self.current_index = 0
        self.update_image_list_label()
        self.preview_label.config(image=None, text="尚未選擇圖片")

    def update_image_list_label(self):
        count = len(self.image_files)
        self.image_list_label.config(text=f"已選取 {count} 張圖片")

    def show_preview(self):
        if not self.image_files:
            return
        path = self.image_files[self.current_index]
        try:
            if path.lower().endswith(".pdf"):
                self.preview_label.config(text="PDF 檔案（無法預覽）")
            else:
                img = Image.open(path)
                img.thumbnail((300, 400))
                self.preview_photo = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.preview_photo, text="")
        except Exception as e:
            self.preview_label.config(image=None, text=f"無法預覽: {e}")

        self.nav_label.config(text=f"{self.current_index + 1} / {len(self.image_files)}")

    def prev_image(self):
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.show_preview()

    def next_image(self):
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.show_preview()

    def _get_form_data(self):
        data = {}
        for key, entry in self.entries.items():
            data[key] = entry.get().strip()
        data["amount"] = float(data["amount"]) if data["amount"] else 0
        data["tax"] = float(data["tax"]) if data["tax"] else 0
        return data

    def _copy_image(self, original_path, invoice_no, date):
        if not original_path:
            return None
        ext = os.path.splitext(original_path)[1].lower()
        if ext == ".jpeg":
            ext = ".jpg"
        filename = f"{date}_{invoice_no}{ext}"
        dest = os.path.join(IMAGES_DIR, filename)
        try:
            if original_path.lower().endswith(".pdf"):
                shutil.copy(original_path, dest)
            else:
                img = Image.open(original_path)
                img.convert("RGB").save(dest, "JPEG", quality=85)
        except Exception as e:
            return None
        return filename

    def save_invoice(self):
        if not self.entries["invoice_no"].get().strip():
            messagebox.showwarning("警告", "發票號碼不可為空")
            return False
        if not self.entries["date"].get().strip():
            messagebox.showwarning("警告", "日期不可為空")
            return False

        data = self._get_form_data()
        image_filename = None

        if self.image_files:
            image_filename = self._copy_image(
                self.image_files[0],
                data["invoice_no"],
                data["date"]
            )

        try:
            self.db_manager.insert_invoice(data, image_filename)
            return True
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {e}")
            return False

    def save_and_continue(self):
        if self.save_invoice():
            messagebox.showinfo("成功", "發票已儲存")
            self._clear_form()
            if self.callback:
                self.callback()

    def save_and_close(self):
        if self.save_invoice():
            self.win.destroy()
            if self.callback:
                self.callback()

    def run_ocr(self):
        if not self.image_files:
            messagebox.showinfo("提示", "請先選擇發票圖片")
            return
        path = self.image_files[self.current_index]
        if path.lower().endswith(".pdf"):
            messagebox.showwarning("警告", "PDF 不支援 OCR，請先轉為圖片")
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
                self.win.after(0, lambda: self.ocr_btn.config(state=tk.NORMAL, text="🤖 OCR 自動辨識"))

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
            if value:
                entry.delete(0, tk.END)
                entry.insert(0, value)

    def _clear_form(self):
        for key, entry in self.entries.items():
            if key == "date":
                entry.delete(0, tk.END)
                entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
            else:
                entry.delete(0, tk.END)
        self.clear_images()
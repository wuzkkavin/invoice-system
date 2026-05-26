import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import shutil
import threading
from datetime import datetime
from PIL import Image, ImageTk


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


IMAGES_DIR = os.path.join(_get_base_dir(), "images")
IMAGES_BAK_DIR = os.path.join(_get_base_dir(), "imageBAK")


class AddInvoiceWindow:
    def __init__(self, parent, db_manager, callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.image_files = []
        self.current_index = 0
        self.entries = {}
        self.original_image = None
        self.zoom_level = 1.0
        self.fit_zoom = 1.0
        self._drag_x = 0
        self._drag_y = 0
        self.ocr_bak_path = None

        self.win = tk.Toplevel(parent)
        self.win.title("新增發票")
        self.win.geometry("700x600")
        self.win.transient(parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

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

        tk.Label(right_frame, text="圖片預覽（滾輪縮放，拖曳平移）").pack()

        self.canvas_frame = tk.Frame(right_frame, bd=1, relief=tk.SUNKEN)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_move)

        nav_frame = tk.Frame(right_frame)
        nav_frame.pack(fill=tk.X)
        self.nav_label = tk.Label(nav_frame, text="")
        self.nav_label.pack(side=tk.LEFT)
        self.zoom_label = tk.Label(nav_frame, text="", fg="gray", font=("", 8))
        self.zoom_label.pack(side=tk.LEFT, padx=5)
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
        tk.Button(bottom_frame, text="取消", command=self._on_close).pack(side=tk.RIGHT, padx=5)

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

    def _on_close(self):
        self.win.unbind_all("<MouseWheel>")
        self.win.destroy()

    def clear_images(self):
        self.image_files = []
        self.current_index = 0
        self.update_image_list_label()
        self.canvas.delete("all")
        self.canvas.create_text(100, 50, text="尚未選擇圖片", fill="gray", anchor=tk.NW)

    def update_image_list_label(self):
        count = len(self.image_files)
        self.image_list_label.config(text=f"已選取 {count} 張圖片")

    def show_preview(self):
        self.ocr_bak_path = None
        if not self.image_files:
            return
        path = self.image_files[self.current_index]
        try:
            if path.lower().endswith(".pdf"):
                import fitz
                doc = fitz.open(path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=200)
                self.original_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
            else:
                self.original_image = Image.open(path).copy()
            fit = min(300 / self.original_image.width, 400 / self.original_image.height, 1.0)
            self.fit_zoom = fit
            self.zoom_level = 1.0
            self._render_preview()
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(100, 50, text=f"無法預覽: {e}", fill="red", anchor=tk.NW)

        self.nav_label.config(text=f"{self.current_index + 1} / {len(self.image_files)}")

    def _render_preview(self):
        if self.original_image is None:
            return
        scale = self.fit_zoom * self.zoom_level
        w = max(1, int(self.original_image.width * scale))
        h = max(1, int(self.original_image.height * scale))
        img = self.original_image.resize((w, h), Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        cx = self.canvas.winfo_width() // 2 or 150
        cy = self.canvas.winfo_height() // 2 or 150
        self.canvas.create_image(cx, cy, image=self.preview_photo, anchor=tk.CENTER, tags="img")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")

    def _on_mousewheel(self, event):
        if self.original_image is None:
            return
        factor = 1.1 if event.delta > 0 else 0.9
        new_zoom = self.zoom_level * factor
        if 0.1 <= new_zoom <= 5.0:
            self.zoom_level = new_zoom
            self._render_preview()

    def _on_drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        self.canvas.config(cursor="hand2")

    def _on_drag_move(self, event):
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        self._drag_x = event.x
        self._drag_y = event.y
        self.canvas.move("img", dx, dy)

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
            orig_path = self.image_files[self.current_index]
            if self.ocr_bak_path:
                image_filename = self.ocr_bak_path
            else:
                image_filename = self._copy_image(orig_path, data["invoice_no"], data["date"])

        try:
            self.db_manager.insert_invoice(data, image_filename)
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗: {e}")
            return False

        if self.ocr_bak_path and self.image_files:
            self._rename_original(self.image_files[self.current_index])
        return True

    def _rename_original(self, path):
        try:
            d = os.path.dirname(path)
            b = os.path.basename(path)
            new = os.path.join(d, f"已辨識登錄_{b}")
            if not os.path.exists(new):
                os.rename(path, new)
        except Exception:
            pass

    def save_and_continue(self):
        if not self.save_invoice():
            return
        messagebox.showinfo("成功", "發票已儲存")
        if self.current_index < len(self.image_files) - 1:
            self._clear_form(keep_images=True)
            self.current_index += 1
            self.show_preview()
        else:
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

        self.ocr_btn.config(state=tk.DISABLED, text="辨識中...")
        self.ocr_status.config(text="正在呼叫 AI 辨識...", fg="gray")

        def do_ocr():
            try:
                from ocr_helper import ocr_invoice, map_ocr_to_fields
                result = ocr_invoice(path)
                if "error" in result:
                    err = result["error"]
                    self.win.after(0, lambda: self.ocr_status.config(text="辨識失敗", fg="red"))
                    self.win.after(0, lambda: messagebox.showerror("OCR 錯誤", err))
                else:
                    fields = map_ocr_to_fields(result)
                    self.win.after(0, lambda: self._fill_ocr_result(fields))
                    self.win.after(0, lambda: self._on_ocr_success(path, fields))
                    self.win.after(0, lambda: self.ocr_status.config(text="✅ OCR 完成", fg="green"))
            except Exception as e:
                self.win.after(0, lambda: self.ocr_status.config(text="錯誤", fg="red"))
                self.win.after(0, lambda: messagebox.showerror("OCR 錯誤", str(e)))
            finally:
                self.win.after(0, lambda: self.ocr_btn.config(state=tk.NORMAL, text="🤖 OCR 自動辨識"))

        threading.Thread(target=do_ocr, daemon=True).start()

    def _on_ocr_success(self, original_path, fields):
        bak_dir = os.path.join(_get_base_dir(), "imageBAK")
        os.makedirs(bak_dir, exist_ok=True)
        inv_no = fields.get("invoice_no", "unknown")
        date = fields.get("date", datetime.today().strftime("%Y-%m-%d"))
        orig_name = os.path.basename(original_path)
        bak_name = f"{date}_{inv_no}_{orig_name}"
        bak_path = os.path.join(bak_dir, bak_name)
        try:
            shutil.copy2(original_path, bak_path)
            self.ocr_bak_path = bak_name
        except Exception:
            pass

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

    def _clear_form(self, keep_images=False):
        for key, entry in self.entries.items():
            if key == "date":
                entry.delete(0, tk.END)
                entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
            else:
                entry.delete(0, tk.END)
        if not keep_images:
            self.clear_images()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from PIL import Image, ImageTk

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")


class MainWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        self.parent.title("華葳集成自動發票系統 - by Wuzk")
        self.parent.geometry("1000x600")

        self.search_entries = {}
        self.tree = None
        self.current_image_label = None
        self.current_preview_label = None

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        toolbar = tk.Frame(self.parent, bd=1, relief=tk.RAISED)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(toolbar, text="新增發票", command=self.open_add_window).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="匯出 Excel", command=self.export_excel).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="重新整理", command=self._load_data).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="設定", command=self.open_settings).pack(side=tk.RIGHT, padx=3)

        search_frame = tk.LabelFrame(self.parent, text="搜尋條件", padx=5, pady=5)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        row = 0
        fields = [
            ("發票號碼", "invoice_no", 0),
            ("賣方名稱", "seller", 0),
            ("品名", "product", 1),
            ("統一編號", "seller_tax_id", 1),
            ("金額區間", "amount_min", 2),
            ("~", "amount_max", 2),
            ("日期區間", "date_start", 3),
            ("~", "date_end", 3),
        ]

        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_columnconfigure(3, weight=1)

        tk.Label(search_frame, text="發票號碼").grid(row=0, column=0, sticky=tk.W, padx=3)
        self.search_entries["invoice_no"] = tk.Entry(search_frame, width=15)
        self.search_entries["invoice_no"].grid(row=0, column=1, sticky=tk.W, padx=3)

        tk.Label(search_frame, text="賣方名稱").grid(row=0, column=2, sticky=tk.W, padx=3)
        self.search_entries["seller"] = tk.Entry(search_frame, width=15)
        self.search_entries["seller"].grid(row=0, column=3, sticky=tk.W, padx=3)

        tk.Label(search_frame, text="品名").grid(row=1, column=0, sticky=tk.W, padx=3)
        self.search_entries["product"] = tk.Entry(search_frame, width=15)
        self.search_entries["product"].grid(row=1, column=1, sticky=tk.W, padx=3)

        tk.Label(search_frame, text="統一編號").grid(row=1, column=2, sticky=tk.W, padx=3)
        self.search_entries["seller_tax_id"] = tk.Entry(search_frame, width=15)
        self.search_entries["seller_tax_id"].grid(row=1, column=3, sticky=tk.W, padx=3)

        tk.Label(search_frame, text="金額").grid(row=2, column=0, sticky=tk.W, padx=3)
        self.search_entries["amount_min"] = tk.Entry(search_frame, width=10)
        self.search_entries["amount_min"].grid(row=2, column=1, sticky=tk.W, padx=3)
        tk.Label(search_frame, text="~").grid(row=2, column=2, sticky=tk.W, padx=3)
        self.search_entries["amount_max"] = tk.Entry(search_frame, width=10)
        self.search_entries["amount_max"].grid(row=2, column=3, sticky=tk.W, padx=3)

        tk.Label(search_frame, text="日期").grid(row=3, column=0, sticky=tk.W, padx=3)
        self.search_entries["date_start"] = tk.Entry(search_frame, width=10)
        self.search_entries["date_start"].grid(row=3, column=1, sticky=tk.W, padx=3)
        tk.Label(search_frame, text="~").grid(row=3, column=2, sticky=tk.W, padx=3)
        self.search_entries["date_end"] = tk.Entry(search_frame, width=10)
        self.search_entries["date_end"].grid(row=3, column=3, sticky=tk.W, padx=3)

        tk.Button(search_frame, text="搜尋", command=self.do_search).grid(row=4, column=0, pady=5)
        tk.Button(search_frame, text="清除", command=self.clear_search).grid(row=4, column=1, pady=5, sticky=tk.W)

        list_frame = tk.Frame(self.parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "invoice_no", "date", "seller", "seller_tax_id", "product", "amount", "tax")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("invoice_no", text="發票號碼")
        self.tree.heading("date", text="日期")
        self.tree.heading("seller", text="賣方名稱")
        self.tree.heading("seller_tax_id", text="統一編號")
        self.tree.heading("product", text="品名")
        self.tree.heading("amount", text="金額")
        self.tree.heading("tax", text="稅額")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("invoice_no", width=100, anchor=tk.CENTER)
        self.tree.column("date", width=90, anchor=tk.CENTER)
        self.tree.column("seller", width=150, anchor=tk.W)
        self.tree.column("seller_tax_id", width=90, anchor=tk.CENTER)
        self.tree.column("product", width=200, anchor=tk.W)
        self.tree.column("amount", width=80, anchor=tk.E)
        self.tree.column("tax", width=60, anchor=tk.E)

        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-Button-1>", self.on_double_click)

        preview_frame = tk.Frame(self.parent, bd=1, relief=tk.SUNKEN, height=150)
        preview_frame.pack(fill=tk.X, padx=5, pady=5)
        self.current_preview_label = tk.Label(preview_frame, text="選取一筆資料可預覽圖片")
        self.current_preview_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

    def _load_data(self, results=None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        if results is None:
            results = self.db_manager.get_all_invoices()

        for item in results:
            self.tree.insert("", tk.END, values=(
                item["id"],
                item["invoice_no"],
                item["date"],
                item["seller"],
                item["seller_tax_id"],
                item["product"],
                f"{item['amount']:.0f}",
                f"{item['tax']:.0f}"
            ), tags=(item["id"],))

    def on_select_row(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0])["values"]
        invoice_id = values[0]
        invoice = self.db_manager.get_invoice_by_id(invoice_id)
        if invoice and invoice.get("image_path"):
            self._show_preview(invoice["image_path"])

    def _show_preview(self, filename):
        if not filename:
            self.current_preview_label.config(text="無圖片", image="")
            return
        path = os.path.join(IMAGES_DIR, filename)
        if not os.path.exists(path):
            self.current_preview_label.config(text="圖片不存在", image="")
            return
        try:
            if path.lower().endswith(".pdf"):
                import fitz
                doc = fitz.open(path)
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=100)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
            else:
                img = Image.open(path)
            img.thumbnail((120, 150))
            self.preview_photo = ImageTk.PhotoImage(img)
            self.current_preview_label.config(image=self.preview_photo, text="")
        except Exception as e:
            self.current_preview_label.config(text=f"預覽失敗: {e}", image="")

    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0])["values"]
        invoice_id = values[0]
        self.open_edit_window(invoice_id)

    def open_add_window(self):
        from ui_add import AddInvoiceWindow
        AddInvoiceWindow(self.parent, self.db_manager, callback=self._load_data)

    def open_edit_window(self, invoice_id):
        from ui_edit import EditInvoiceWindow
        EditInvoiceWindow(self.parent, self.db_manager, invoice_id, callback=self._load_data)

    def open_settings(self):
        from ui_settings import SettingsWindow
        SettingsWindow(self.parent)

    def do_search(self):
        amount_min = None
        amount_max = None
        if self.search_entries["amount_min"].get().strip():
            try:
                amount_min = float(self.search_entries["amount_min"].get())
            except ValueError:
                messagebox.showwarning("警告", "金額請輸入數字")
                return
        if self.search_entries["amount_max"].get().strip():
            try:
                amount_max = float(self.search_entries["amount_max"].get())
            except ValueError:
                messagebox.showwarning("警告", "金額請輸入數字")
                return

        results = self.db_manager.search_invoices(
            invoice_no=self.search_entries["invoice_no"].get().strip(),
            seller=self.search_entries["seller"].get().strip(),
            product=self.search_entries["product"].get().strip(),
            seller_tax_id=self.search_entries["seller_tax_id"].get().strip(),
            amount_min=amount_min,
            amount_max=amount_max,
            date_start=self.search_entries["date_start"].get().strip(),
            date_end=self.search_entries["date_end"].get().strip()
        )
        self._load_data(results)

    def clear_search(self):
        for entry in self.search_entries.values():
            entry.delete(0, tk.END)
        self._load_data()

    def export_excel(self):
        selection = self.tree.selection()
        if selection:
            ids = [self.tree.item(item)["values"][0] for item in selection]
            results = []
            for vid in ids:
                inv = self.db_manager.get_invoice_by_id(vid)
                if inv:
                    results.append(inv)
        else:
            results = self.db_manager.get_all_invoices()

        if not results:
            messagebox.showinfo("提示", "目前沒有資料可匯出")
            return

        file_path = filedialog.asksaveasfilename(
            title="匯出 Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel 檔案", "*.xlsx")],
            initialfile=f"發票資料_{datetime.now().strftime('%Y%m%d')}"
        )

        if not file_path:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "發票資料"

            headers = ["ID", "發票號碼", "日期", "賣方名稱", "統一編號", "品名", "金額", "稅額"]
            ws.append(headers)

            for item in results:
                ws.append([
                    item["id"],
                    item["invoice_no"],
                    item["date"],
                    item["seller"],
                    item["seller_tax_id"],
                    item["product"],
                    item["amount"],
                    item["tax"]
                ])

            for col in ws.columns:
                max_length = 0
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                for cell in col:
                    cell.font = cell.font.copy(name="微軟正黑體")
                ws.column_dimensions[col[0].column_letter].width = min(max_length + 5, 40)

            wb.save(file_path)
            messagebox.showinfo("成功", f"已匯出至:\n{file_path}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗: {e}")
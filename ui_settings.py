import os
import tkinter as tk
from tkinter import messagebox
import config_manager


class SettingsWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("API 金鑰設定")
        self.win.geometry("560x240")
        self.win.transient(parent)
        self.win.grab_set()

        self.entries = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        frame = tk.Frame(self.win, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        frame.grid_columnconfigure(1, weight=1)

        tk.Label(frame, text="輸入各 AI 服務的 API Key（儲存後寫入 config.json）").grid(
            row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        providers = [
            ("GEMINI_API_KEY", "Gemini（預設 OCR）"),
            ("MINIMAX_API_KEY", "MiniMax（備用 OCR）"),
            ("OPENAI_API_KEY", "OpenAI（備用 OCR）"),
        ]

        for i, (key, label) in enumerate(providers):
            tk.Label(frame, text=label).grid(row=i+1, column=0, sticky=tk.W, pady=4)
            entry = tk.Entry(frame, show="*")
            entry.grid(row=i+1, column=1, sticky=tk.EW, padx=5, pady=4)
            self.entries[key] = entry

            show_btn = tk.Button(frame, text="👁", width=3,
                                 command=lambda e=entry: self._toggle_show(e))
            show_btn.grid(row=i+1, column=2, pady=4)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=len(providers)+1, column=0, columnspan=3, pady=12)

        tk.Button(btn_frame, text="儲存", command=self._save, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.win.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def _toggle_show(self, entry):
        entry.config(show="" if entry.cget("show") == "*" else "*")

    def _load_values(self):
        cfg = config_manager.load_config()
        for key, entry in self.entries.items():
            val = cfg.get(key, "")
            if val:
                entry.insert(0, val)

    def _save(self):
        cfg = config_manager.load_config()
        for key, entry in self.entries.items():
            cfg[key] = entry.get().strip()
        config_manager.save_config(cfg)
        for key, entry in self.entries.items():
            val = entry.get().strip()
            if val:
                os.environ[key] = val
        messagebox.showinfo("成功", "API 金鑰已儲存")
        self.win.destroy()

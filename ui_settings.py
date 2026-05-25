import tkinter as tk
from tkinter import ttk, messagebox
import config_manager


class SettingsWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("API 金鑰設定")
        self.win.geometry("500x280")
        self.win.transient(parent)
        self.win.grab_set()

        self.entries = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        frame = tk.Frame(self.win, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="在此輸入各 AI 服務的 API Key，設定後會儲存在 config.json").pack(anchor=tk.W, pady=(0, 10))

        providers = [
            ("GEMINI_API_KEY", "Gemini（預設 OCR）", "AIza..."),
            ("MINIMAX_API_KEY", "MiniMax（備用 OCR）", "mx-..."),
            ("OPENAI_API_KEY", "OpenAI（備用 OCR）", "sk-..."),
        ]

        for i, (key, label, placeholder) in enumerate(providers):
            tk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = tk.Entry(frame, width=50, show="*")
            entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)
            self.entries[key] = entry

            show_btn = tk.Button(frame, text="👁", width=3, command=lambda e=entry: self._toggle_show(e))
            show_btn.grid(row=i, column=2, pady=5)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=len(providers), column=0, columnspan=3, pady=15)

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
        # 同時寫入環境變數，讓已經 import 的模組也能讀到
        for key, entry in self.entries.items():
            val = entry.get().strip()
            if val:
                import os
                os.environ[key] = val
        messagebox.showinfo("成功", "API 金鑰已儲存")
        self.win.destroy()

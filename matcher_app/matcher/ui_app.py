"""Графічний інтерфейс MatcherApp."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import customtkinter as ctk
import pandas as pd
from tkinter import Menu, filedialog, messagebox, ttk

from .core import MatcherCore
from .exporters import export_exact, export_near, export_unmatched
from .logging_utils import setup_logging
from .models import ColumnMapping


_REQUIRED_FIELDS = {
    "name": "Назва",
    "brand": "Бренд",
    "model": "Модель",
    "film_type": "Тип плівки",
}
_OPTIONAL_FIELDS = {
    "sku": "Артикул",
    "product_id": "ID",
    "price": "Ціна",
}


class MappingDialog(ctk.CTkToplevel):
    """Діалог ручного мапінгу колонок."""

    def __init__(self, master, columns: list[str], mapping: ColumnMapping):
        super().__init__(master)
        self.title("Налаштування колонок")
        self.geometry("420x360")
        self.resizable(False, False)
        self.result: Optional[ColumnMapping] = None
        self.columns = [""] + columns
        self._inputs: dict[str, ctk.CTkOptionMenu] = {}
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)
        row = 0
        for field, label_text in _REQUIRED_FIELDS.items():
            ctk.CTkLabel(frame, text=f"{label_text} *").grid(row=row, column=0, sticky="w", pady=4)
            option = ctk.CTkOptionMenu(frame, values=self.columns)
            option.set(getattr(mapping, field) or "")
            option.grid(row=row, column=1, sticky="ew", pady=4)
            self._inputs[field] = option
            row += 1
        for field, label_text in _OPTIONAL_FIELDS.items():
            ctk.CTkLabel(frame, text=label_text).grid(row=row, column=0, sticky="w", pady=4)
            option = ctk.CTkOptionMenu(frame, values=self.columns)
            option.set(getattr(mapping, field, "") or "")
            option.grid(row=row, column=1, sticky="ew", pady=4)
            self._inputs[field] = option
            row += 1
        frame.columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(btn_frame, text="Скасувати", command=self._on_cancel).pack(side="right", padx=4)
        ctk.CTkButton(btn_frame, text="Зберегти", command=self._on_save).pack(side="right", padx=4)
        self.grab_set()
        self.focus_set()

    def _on_save(self) -> None:
        mapping = ColumnMapping()
        for field in _REQUIRED_FIELDS:
            value = self._inputs[field].get() or None
            setattr(mapping, field, value)
        mapping.sku = self._inputs["sku"].get() or None
        mapping.product_id = self._inputs["product_id"].get() or None
        mapping.price = self._inputs["price"].get() or None
        if mapping.required_missing():
            messagebox.showerror("Помилка", "Заповніть усі обов'язкові поля")
            return
        self.result = mapping
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


class MatcherAppUI:
    """Основний клас GUI."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title("Matcher App — MVP")
        self.root.geometry("980x640")
        self.core = MatcherCore()
        self.logger = setup_logging(Path.cwd())
        self.core.attach_logger(self.logger)
        self.generate_canon = ctk.BooleanVar(value=False)
        self._build_menu()
        self._build_layout()
        self.results: Optional[dict[str, pd.DataFrame]] = None

    # --- UI складання ---
    def _build_menu(self) -> None:
        menu_bar = Menu(self.root)
        file_menu = Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Завантажити мій прайс…", command=self.on_load_user)
        file_menu.add_command(label="Додати прайс постачальника…", command=self.on_add_supplier)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.root.destroy)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        match_menu = Menu(menu_bar, tearoff=False)
        match_menu.add_checkbutton(label="Генерувати canon_id", variable=self.generate_canon)
        match_menu.add_command(label="Запустити матчинг", command=self.on_run_matching)
        menu_bar.add_cascade(label="Матчинг", menu=match_menu)

        export_menu = Menu(menu_bar, tearoff=False)
        export_menu.add_command(label="Експорт Exact…", command=lambda: self.on_export("exact"))
        export_menu.add_command(label="Експорт Near…", command=lambda: self.on_export("near"))
        export_menu.add_command(label="Експорт Unmatched…", command=lambda: self.on_export("unmatched"))
        menu_bar.add_cascade(label="Експорт", menu=export_menu)

        self.root.configure(menu=menu_bar)

    def _build_layout(self) -> None:
        frame = ctk.CTkFrame(self.root)
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        columns = ("source", "rows", "note")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        self.tree.heading("source", text="Джерело")
        self.tree.heading("rows", text="Рядків")
        self.tree.heading("note", text="Примітка")
        self.tree.column("source", width=400)
        self.tree.column("rows", width=80, anchor="center")
        self.tree.column("note", width=320)
        self.tree.pack(fill="both", expand=True)
        self.status_label = ctk.CTkLabel(self.root, text="Готово")
        self.status_label.pack(fill="x", padx=12, pady=(0, 12))
        self.tree_data: dict[str, str] = {}
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        user_note = self.core.user_path.name if self.core.user_path else "Не завантажено"
        user_rows = len(self.core.user_df) if self.core.user_df is not None else 0
        self.tree.insert("", "end", values=("Мій прайс", user_rows, user_note))
        for supplier in self.core.suppliers:
            note = supplier.path.name
            rows = len(supplier.dataframe)
            self.tree.insert("", "end", values=(f"Постачальник: {note}", rows, ""))

    # --- Дії ---
    def on_load_user(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Оберіть файл мого прайсу",
            filetypes=[("Таблиці", "*.csv *.xlsx"), ("CSV", "*.csv"), ("Excel", "*.xlsx")],
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            df = self.core.load_dataframe(path)
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))
            return
        mapping = self.core.suggest_mapping("user", df)
        if mapping.required_missing():
            dialog = MappingDialog(self.root, list(df.columns), mapping)
            self.root.wait_window(dialog)
            if dialog.result is None:
                return
            mapping = dialog.result
        try:
            self.core.set_user_price(path, df, mapping)
            self.status_label.configure(text=f"Мій прайс: {len(self.core.user_df)} рядків")
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))
        self._refresh_tree()

    def on_add_supplier(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Оберіть файл постачальника",
            filetypes=[("Таблиці", "*.csv *.xlsx"), ("CSV", "*.csv"), ("Excel", "*.xlsx")],
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            df = self.core.load_dataframe(path)
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))
            return
        cache_key = f"supplier::{path.suffix.lower()}"
        mapping = self.core.suggest_mapping(cache_key, df)
        if mapping.required_missing():
            dialog = MappingDialog(self.root, list(df.columns), mapping)
            self.root.wait_window(dialog)
            if dialog.result is None:
                return
            mapping = dialog.result
        try:
            self.core.add_supplier(path, df, mapping)
            self.status_label.configure(text=f"Додано постачальника {path.name}")
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))
        self._refresh_tree()

    def on_run_matching(self) -> None:
        try:
            results = self.core.run_matching(self.generate_canon.get())
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))
            return
        self.results = results
        self.status_label.configure(text=self.core.stats_summary())

    def on_export(self, key: str) -> None:
        if not self.results or key not in self.results:
            messagebox.showwarning("Увага", "Спочатку виконайте матчинг")
            return
        df = self.results[key]
        if df is None:
            messagebox.showwarning("Увага", "Немає даних для експорту")
            return
        default_name = f"{key}.csv"
        path_str = filedialog.asksaveasfilename(
            title="Збереження CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV", "*.csv")],
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            if key == "exact":
                export_exact(df, path)
            elif key == "near":
                export_near(df, path)
            else:
                export_unmatched(df, path)
            self.status_label.configure(text=f"Експортовано {key} у {path.name}")
        except Exception as exc:
            messagebox.showerror("Помилка", str(exc))

    def run(self) -> None:
        self.root.mainloop()


__all__ = ["MatcherAppUI"]

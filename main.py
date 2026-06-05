"""
AgroTracker
Сучасний GUI-додаток для аграріїв.

Функції:
- облік полів;
- облік посівів;
- продаж культури;
- журнал робіт;
- витрати;
- аналітика прибутку.

Для запуску:
pip install customtkinter
python main.py
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict, fields as dataclass_fields
from datetime import datetime
from typing import List, Optional

try:
    import customtkinter as ctk
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Не встановлено customtkinter.\n"
        "Відкрийте Terminal у PyCharm і виконайте команду:\n"
        "pip install customtkinter"
    ) from exc


# ==========================
# НАЛАШТУВАННЯ
# ==========================

APP_NAME = "AgroTracker"
APP_VERSION = "1.1.0"

WINDOW_WIDTH = 1350
WINDOW_HEIGHT = 850

FONT_FAMILY = "Segoe UI"

CROPS = {
    "wheat": {
        "name": "Пшениця",
        "yield_avg": 6.0,
        "price_avg": 5500,
    },
    "corn": {
        "name": "Кукурудза",
        "yield_avg": 9.0,
        "price_avg": 5200,
    },
    "sunflower": {
        "name": "Соняшник",
        "yield_avg": 2.7,
        "price_avg": 12500,
    },
    "soybean": {
        "name": "Соя",
        "yield_avg": 2.4,
        "price_avg": 14500,
    },
    "rapeseed": {
        "name": "Ріпак",
        "yield_avg": 3.0,
        "price_avg": 13500,
    },
    "barley": {
        "name": "Ячмінь",
        "yield_avg": 4.8,
        "price_avg": 4800,
    },
    "sugar_beet": {
        "name": "Цукровий буряк",
        "yield_avg": 45.0,
        "price_avg": 1400,
    },
}

SOIL_TYPES = {
    "chernozem": "Чорнозем",
    "podzol": "Підзолистий",
    "grey_forest": "Сірий лісовий",
    "brown_forest": "Бурий лісовий",
    "sandy": "Піщаний",
    "clay": "Глинистий",
}

FIELD_OPERATIONS = [
    "Оранка",
    "Культивація",
    "Боронування",
    "Сівба",
    "Внесення добрив",
    "Обприскування",
    "Зрошення",
    "Збір врожаю",
    "Транспортування",
    "Сушка",
    "Зберігання",
    "Інше",
]

COLORS = {
    "bg_primary": "#0F1419",
    "bg_secondary": "#1A2332",
    "bg_tertiary": "#243447",
    "border": "#2D3E50",
    "accent": "#00D4AA",
    "accent_hover": "#00B894",
    "blue": "#00A8CC",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B6C2CF",
    "text_muted": "#6E7F91",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "danger_hover": "#C53030",
}


# ==========================
# ДОПОМІЖНІ ФУНКЦІЇ
# ==========================

def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).strip().replace(" ", "").replace(",", ".")
        if text == "":
            return default
        return float(text)
    except ValueError:
        return default


def safe_int(value, default: int = 0) -> int:
    try:
        return int(safe_float(value, default))
    except ValueError:
        return default


def money(value: float) -> str:
    return f"{value:,.0f} грн".replace(",", " ")


def tons(value: float) -> str:
    return f"{value:.1f} т"


def dataclass_from_dict(cls, data: dict):
    """
    Безпечне створення dataclass з JSON.
    Якщо у farm_data.json є старі або зайві поля, вони ігноруються.
    """
    if not isinstance(data, dict):
        return cls()

    allowed = {f.name for f in dataclass_fields(cls)}
    cleaned = {k: v for k, v in data.items() if k in allowed}
    return cls(**cleaned)


# ==========================
# МОДЕЛІ ДАНИХ
# ==========================

@dataclass
class Field:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    area: float = 0.0
    soil_type: str = ""
    status: str = "active"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Field":
        return dataclass_from_dict(cls, data)


@dataclass
class Crop:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    field_id: str = ""
    crop_type: str = ""
    planting_date: str = ""

    expected_yield: float = 0.0
    actual_yield: Optional[float] = None

    price_per_ton: float = 0.0
    total_expenses: float = 0.0

    sold_quantity_tons: float = 0.0
    sale_price_per_ton: float = 0.0
    sale_date: str = ""
    buyer: str = ""

    status: str = "planted"
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Crop":
        return dataclass_from_dict(cls, data)

    def calculate_revenue(self) -> float:
        """
        Дохід рахується тільки після продажу:
        продано тонн * ціна за тонну.
        """
        quantity = safe_float(self.sold_quantity_tons)
        price = safe_float(self.sale_price_per_ton)
        return quantity * price

    def calculate_profit_without_work_costs(self) -> float:
        return self.calculate_revenue() - safe_float(self.total_expenses)


@dataclass
class WorkRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    field_id: str = ""
    date: str = ""
    operation: str = ""
    description: str = ""
    equipment: str = ""
    workers_count: int = 1
    duration_hours: float = 0.0
    fuel_cost: float = 0.0
    other_cost: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkRecord":
        return dataclass_from_dict(cls, data)

    def get_total_cost(self) -> float:
        return safe_float(self.fuel_cost) + safe_float(self.other_cost)


# ==========================
# СЕРВІС ДАНИХ
# ==========================

class DataService:
    def __init__(self, filename: str = "farm_data.json"):
        self.filename = filename
        self.data = self._empty_data()
        self.load()

    def _empty_data(self) -> dict:
        return {
            "fields": [],
            "crops": [],
            "work_records": [],
            "last_updated": "",
        }

    def load(self):
        if not os.path.exists(self.filename):
            self.save()
            return

        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                loaded = json.load(file)

            base = self._empty_data()

            if isinstance(loaded, dict):
                base.update(loaded)

            if not isinstance(base.get("fields"), list):
                base["fields"] = []
            if not isinstance(base.get("crops"), list):
                base["crops"] = []
            if not isinstance(base.get("work_records"), list):
                base["work_records"] = []

            self.data = base

        except Exception:
            self.data = self._empty_data()
            self.save()

    def save(self):
        self.data["last_updated"] = datetime.now().isoformat()

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=2)

    # Поля

    def get_fields(self) -> List[Field]:
        result = []

        for item in self.data.get("fields", []):
            try:
                result.append(Field.from_dict(item))
            except Exception:
                pass

        return result

    def add_field(self, item: Field):
        self.data["fields"].append(item.to_dict())
        self.save()

    def update_field(self, item: Field):
        updated = False

        for index, old in enumerate(self.data["fields"]):
            if old.get("id") == item.id:
                self.data["fields"][index] = item.to_dict()
                updated = True
                break

        if not updated:
            self.data["fields"].append(item.to_dict())

        self.save()

    def delete_field(self, field_id: str):
        self.data["fields"] = [
            item for item in self.data["fields"]
            if item.get("id") != field_id
        ]

        self.data["crops"] = [
            item for item in self.data["crops"]
            if item.get("field_id") != field_id
        ]

        self.data["work_records"] = [
            item for item in self.data["work_records"]
            if item.get("field_id") != field_id
        ]

        self.save()

    # Посіви

    def get_crops(self, field_id: Optional[str] = None) -> List[Crop]:
        result = []

        for item in self.data.get("crops", []):
            try:
                crop = Crop.from_dict(item)

                if field_id is None or crop.field_id == field_id:
                    result.append(crop)

            except Exception:
                pass

        return result

    def add_crop(self, item: Crop):
        self.data["crops"].append(item.to_dict())
        self.save()

    def update_crop(self, item: Crop):
        updated = False

        for index, old in enumerate(self.data["crops"]):
            if old.get("id") == item.id:
                self.data["crops"][index] = item.to_dict()
                updated = True
                break

        if not updated:
            self.data["crops"].append(item.to_dict())

        self.save()

    def delete_crop(self, crop_id: str):
        self.data["crops"] = [
            item for item in self.data["crops"]
            if item.get("id") != crop_id
        ]
        self.save()

    # Роботи

    def get_work_records(self, field_id: Optional[str] = None) -> List[WorkRecord]:
        result = []

        for item in self.data.get("work_records", []):
            try:
                record = WorkRecord.from_dict(item)

                if field_id is None or record.field_id == field_id:
                    result.append(record)

            except Exception:
                pass

        return result

    def add_work_record(self, item: WorkRecord):
        self.data["work_records"].append(item.to_dict())
        self.save()

    def update_work_record(self, item: WorkRecord):
        updated = False

        for index, old in enumerate(self.data["work_records"]):
            if old.get("id") == item.id:
                self.data["work_records"][index] = item.to_dict()
                updated = True
                break

        if not updated:
            self.data["work_records"].append(item.to_dict())

        self.save()

    def delete_work_record(self, record_id: str):
        self.data["work_records"] = [
            item for item in self.data["work_records"]
            if item.get("id") != record_id
        ]
        self.save()

    # Аналітика

    def get_total_area(self) -> float:
        return sum(safe_float(item.area) for item in self.get_fields())

    def get_total_revenue(self) -> float:
        return sum(item.calculate_revenue() for item in self.get_crops())

    def get_total_crop_expenses(self) -> float:
        return sum(safe_float(item.total_expenses) for item in self.get_crops())

    def get_total_work_expenses(self) -> float:
        return sum(item.get_total_cost() for item in self.get_work_records())

    def get_field_revenue(self, field_id: str) -> float:
        return sum(item.calculate_revenue() for item in self.get_crops(field_id))

    def get_field_crop_expenses(self, field_id: str) -> float:
        return sum(safe_float(item.total_expenses) for item in self.get_crops(field_id))

    def get_field_work_expenses(self, field_id: str) -> float:
        return sum(item.get_total_cost() for item in self.get_work_records(field_id))


# ==========================
# СТИЛІ
# ==========================

class Styles:
    @staticmethod
    def setup():
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

    @staticmethod
    def card(parent, **kwargs):
        options = {
            "fg_color": COLORS["bg_secondary"],
            "corner_radius": 16,
            "border_width": 1,
            "border_color": COLORS["border"],
        }
        options.update(kwargs)
        return ctk.CTkFrame(parent, **options)

    @staticmethod
    def label(
        parent,
        text: str,
        size: int = 14,
        color: Optional[str] = None,
        bold: bool = False,
        anchor: str = "w",
        justify: str = "left",
        **kwargs
    ):
        if color is None:
            color = COLORS["text_primary"]

        weight = "bold" if bold else "normal"

        options = {
            "text": text,
            "font": (FONT_FAMILY, size, weight),
            "text_color": color,
            "anchor": anchor,
            "justify": justify,
        }
        options.update(kwargs)

        return ctk.CTkLabel(parent, **options)

    @staticmethod
    def button(
        parent,
        text: str,
        command=None,
        variant: str = "primary",
        width: int = 120,
        height: int = 38,
        **kwargs
    ):
        if variant == "primary":
            fg = COLORS["accent"]
            hover = COLORS["accent_hover"]
            text_color = COLORS["bg_primary"]
        elif variant == "secondary":
            fg = COLORS["bg_tertiary"]
            hover = COLORS["border"]
            text_color = COLORS["text_primary"]
        elif variant == "danger":
            fg = COLORS["error"]
            hover = COLORS["danger_hover"]
            text_color = COLORS["text_primary"]
        else:
            fg = COLORS["accent"]
            hover = COLORS["accent_hover"]
            text_color = COLORS["bg_primary"]

        options = {
            "text": text,
            "command": command,
            "width": width,
            "height": height,
            "corner_radius": 9,
            "font": (FONT_FAMILY, 13, "bold"),
            "fg_color": fg,
            "hover_color": hover,
            "text_color": text_color,
        }
        options.update(kwargs)

        return ctk.CTkButton(parent, **options)

    @staticmethod
    def entry(parent, placeholder: str = "", width: int = 200, **kwargs):
        options = {
            "width": width,
            "height": 40,
            "corner_radius": 9,
            "placeholder_text": placeholder,
            "font": (FONT_FAMILY, 13),
            "fg_color": COLORS["bg_tertiary"],
            "border_color": COLORS["border"],
            "text_color": COLORS["text_primary"],
            "placeholder_text_color": COLORS["text_muted"],
        }
        options.update(kwargs)

        return ctk.CTkEntry(parent, **options)

    @staticmethod
    def option(parent, values: list, width: int = 200, **kwargs):
        if not values:
            values = ["-"]

        options = {
            "values": values,
            "width": width,
            "height": 40,
            "corner_radius": 9,
            "font": (FONT_FAMILY, 13),
            "fg_color": COLORS["bg_tertiary"],
            "button_color": COLORS["bg_tertiary"],
            "button_hover_color": COLORS["border"],
            "dropdown_fg_color": COLORS["bg_secondary"],
            "dropdown_hover_color": COLORS["accent"],
            "text_color": COLORS["text_primary"],
        }
        options.update(kwargs)

        return ctk.CTkOptionMenu(parent, **options)

    @staticmethod
    def textbox(parent, width: int = 400, height: int = 80, **kwargs):
        options = {
            "width": width,
            "height": height,
            "corner_radius": 9,
            "font": (FONT_FAMILY, 13),
            "fg_color": COLORS["bg_tertiary"],
            "border_color": COLORS["border"],
            "text_color": COLORS["text_primary"],
            "scrollbar_button_color": COLORS["bg_tertiary"],
        }
        options.update(kwargs)

        return ctk.CTkTextbox(parent, **options)


# ==========================
# ГОЛОВНЕ ВІКНО
# ==========================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        Styles.setup()

        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_primary"])

        self.ds = DataService()
        self.current_view_id = "dashboard"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.nav_buttons = []

        self._build_sidebar()
        self._build_content()

        self.navigate("dashboard")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=260,
            fg_color=COLORS["bg_secondary"],
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(20, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=22, pady=(28, 8))

        Styles.label(
            logo_frame,
            "AGRO",
            size=26,
            color=COLORS["accent"],
            bold=True,
        ).pack(side="left")

        Styles.label(
            logo_frame,
            "TRACKER",
            size=26,
            color=COLORS["text_primary"],
            bold=True,
        ).pack(side="left", padx=(4, 0))

        Styles.label(
            self.sidebar,
            "Система управління\nфермерським господарством",
            size=12,
            color=COLORS["text_muted"],
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 28))

        nav_items = [
            ("Панель управління", "dashboard"),
            ("Поля", "fields"),
            ("Посіви", "crops"),
            ("Журнал робіт", "journal"),
            ("Аналітика", "analytics"),
        ]

        for index, (text, view_id) in enumerate(nav_items, start=2):
            button = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=lambda v=view_id: self.navigate(v),
                height=44,
                corner_radius=10,
                font=(FONT_FAMILY, 14, "bold"),
                fg_color="transparent",
                hover_color=COLORS["bg_tertiary"],
                text_color=COLORS["text_secondary"],
                anchor="w",
            )
            button.view_id = view_id
            button.grid(row=index, column=0, sticky="ew", padx=14, pady=4)
            self.nav_buttons.append(button)

        self.sidebar_stat = Styles.card(self.sidebar)
        self.sidebar_stat.grid(row=21, column=0, sticky="ew", padx=14, pady=(0, 22))

        Styles.label(
            self.sidebar_stat,
            "Загальна площа",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self.sidebar_area_label = Styles.label(
            self.sidebar_stat,
            "0.0 га",
            size=24,
            color=COLORS["accent"],
            bold=True,
        )
        self.sidebar_area_label.pack(anchor="w", padx=16, pady=(0, 16))

    def _build_content(self):
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0,
        )
        self.content.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def refresh_sidebar(self):
        self.sidebar_area_label.configure(
            text=f"{self.ds.get_total_area():.1f} га"
        )

    def navigate(self, view_id: str):
        self.current_view_id = view_id

        for button in self.nav_buttons:
            if button.view_id == view_id:
                button.configure(
                    fg_color=COLORS["accent"],
                    text_color=COLORS["bg_primary"],
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                )

        self.refresh_sidebar()

        for widget in self.content.winfo_children():
            widget.destroy()

        views = {
            "dashboard": DashboardView,
            "fields": FieldsView,
            "crops": CropsView,
            "journal": JournalView,
            "analytics": AnalyticsView,
        }

        view_class = views.get(view_id, DashboardView)
        view = view_class(self.content, self.ds, self)
        view.grid(row=0, column=0, sticky="nsew")


# ==========================
# ПАНЕЛЬ УПРАВЛІННЯ
# ==========================

class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, ds: DataService, app: App):
        super().__init__(parent, fg_color="transparent")

        self.ds = ds
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build()

    def _build(self):
        Styles.label(
            self,
            "Панель управління",
            size=30,
            bold=True,
        ).grid(row=0, column=0, sticky="w", pady=(0, 22))

        self._build_stat_cards()
        self._build_bottom()

    def _build_stat_cards(self):
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew")

        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        revenue = self.ds.get_total_revenue()
        expenses = self.ds.get_total_crop_expenses() + self.ds.get_total_work_expenses()
        profit = revenue - expenses

        active_crops = len([
            item for item in self.ds.get_crops()
            if item.status not in ("sold", "harvested")
        ])

        cards = [
            ("Загальна площа", f"{self.ds.get_total_area():.1f} га", COLORS["accent"]),
            ("Активні посіви", str(active_crops), COLORS["blue"]),
            ("Дохід від продажів", money(revenue), COLORS["success"]),
            ("Прибуток", money(profit), COLORS["success"] if profit >= 0 else COLORS["error"]),
        ]

        for index, (title, value, color) in enumerate(cards):
            card = Styles.card(stats_frame, height=112)
            card.grid(row=0, column=index, sticky="ew", padx=8)
            card.grid_propagate(False)

            Styles.label(
                card,
                value,
                size=24,
                color=color,
                bold=True,
            ).place(x=18, y=24)

            Styles.label(
                card,
                title,
                size=12,
                color=COLORS["text_muted"],
            ).place(x=18, y=68)

    def _build_bottom(self):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="nsew", pady=(22, 0))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_rowconfigure(0, weight=1)

        self._active_fields_section(bottom)
        self._recent_works_section(bottom)

    def _active_fields_section(self, parent):
        section = Styles.card(parent)
        section.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        Styles.label(
            section,
            "Поля господарства",
            size=18,
            bold=True,
        ).pack(anchor="w", padx=20, pady=(18, 10))

        scroll = ctk.CTkScrollableFrame(
            section,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        fields = self.ds.get_fields()

        if not fields:
            Styles.label(
                scroll,
                "Поки що немає доданих полів.",
                size=13,
                color=COLORS["text_muted"],
            ).pack(pady=30)
            return

        for item in fields:
            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            Styles.label(
                row,
                item.name,
                size=14,
                bold=True,
            ).pack(side="left", padx=14, pady=11)

            Styles.label(
                row,
                f"{safe_float(item.area):.1f} га",
                size=13,
                color=COLORS["text_muted"],
            ).pack(side="right", padx=14)

    def _recent_works_section(self, parent):
        section = Styles.card(parent)
        section.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        Styles.label(
            section,
            "Останні роботи",
            size=18,
            bold=True,
        ).pack(anchor="w", padx=20, pady=(18, 10))

        scroll = ctk.CTkScrollableFrame(
            section,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        works = sorted(
            self.ds.get_work_records(),
            key=lambda x: x.date,
            reverse=True,
        )

        if not works:
            Styles.label(
                scroll,
                "Поки що немає записів у журналі.",
                size=13,
                color=COLORS["text_muted"],
            ).pack(pady=30)
            return

        for item in works[:12]:
            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            Styles.label(
                row,
                item.operation,
                size=14,
                bold=True,
            ).pack(side="left", padx=14, pady=11)

            Styles.label(
                row,
                item.date,
                size=13,
                color=COLORS["text_muted"],
            ).pack(side="right", padx=14)


# ==========================
# ПОЛЯ
# ==========================

class FieldsView(ctk.CTkFrame):
    def __init__(self, parent, ds: DataService, app: App):
        super().__init__(parent, fg_color="transparent")

        self.ds = ds
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        Styles.label(
            header,
            "Поля господарства",
            size=30,
            bold=True,
        ).pack(side="left")

        Styles.button(
            header,
            "+ Додати поле",
            self._open_add_dialog,
            width=150,
        ).pack(side="right")

        self.table = Styles.card(self)
        self.table.grid(row=1, column=0, sticky="nsew")

        self.refresh()

    def refresh(self):
        for widget in self.table.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(
            self.table,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=0,
        )
        header.pack(fill="x", padx=14, pady=(14, 0))

        columns = [
            ("Назва", 220),
            ("Площа", 110),
            ("Тип ґрунту", 180),
            ("Статус", 100),
            ("Дії", 150),
        ]

        for text, width in columns:
            Styles.label(
                header,
                text,
                size=12,
                color=COLORS["text_muted"],
                width=width,
            ).pack(side="left", padx=6, pady=11)

        scroll = ctk.CTkScrollableFrame(
            self.table,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=14)

        fields = self.ds.get_fields()

        if not fields:
            Styles.label(
                scroll,
                "Немає полів. Натисніть '+ Додати поле'.",
                size=14,
                color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for item in fields:
            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            values = [
                item.name,
                f"{safe_float(item.area):.1f} га",
                SOIL_TYPES.get(item.soil_type, item.soil_type),
                "Активне",
            ]

            widths = [220, 110, 180, 100]

            for text, width in zip(values, widths):
                Styles.label(
                    row,
                    text,
                    size=13,
                    width=width,
                ).pack(side="left", padx=6, pady=10)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=8)

            Styles.button(
                actions,
                "Ред.",
                lambda f=item: self._open_edit_dialog(f),
                variant="secondary",
                width=55,
                height=30,
            ).pack(side="left", padx=3)

            Styles.button(
                actions,
                "X",
                lambda f=item: self._delete_field(f),
                variant="danger",
                width=38,
                height=30,
            ).pack(side="left", padx=3)

    def _open_add_dialog(self):
        FieldDialog(
            self,
            self.ds,
            callback=lambda: [self.refresh(), self.app.refresh_sidebar()],
        )

    def _open_edit_dialog(self, item: Field):
        FieldDialog(
            self,
            self.ds,
            field_item=item,
            callback=lambda: [self.refresh(), self.app.refresh_sidebar()],
        )

    def _delete_field(self, item: Field):
        self.ds.delete_field(item.id)
        self.refresh()
        self.app.refresh_sidebar()


class FieldDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        ds: DataService,
        field_item: Optional[Field] = None,
        callback=None,
    ):
        super().__init__(parent)

        self.ds = ds
        self.field_item = field_item
        self.callback = callback

        self.title("Поле")
        self.geometry("520x500")
        self.resizable(True, True)
        self.configure(fg_color=COLORS["bg_secondary"])
        self.grab_set()

        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        title = "Редагування поля" if self.field_item else "Нове поле"

        Styles.label(
            container,
            title,
            size=22,
            bold=True,
        ).pack(anchor="w", pady=(0, 22))

        Styles.label(
            container,
            "Назва поля",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.name_entry = Styles.entry(container, "Наприклад: Північне поле", 440)
        self.name_entry.pack(fill="x", pady=(0, 14))

        Styles.label(
            container,
            "Площа, га",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.area_entry = Styles.entry(container, "Наприклад: 50", 440)
        self.area_entry.pack(fill="x", pady=(0, 14))

        Styles.label(
            container,
            "Тип ґрунту",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.soil_menu = Styles.option(container, list(SOIL_TYPES.values()), 440)
        self.soil_menu.pack(fill="x", pady=(0, 18))

        self.message_label = Styles.label(
            container,
            "",
            size=12,
            color=COLORS["error"],
        )
        self.message_label.pack(anchor="w", pady=(0, 12))

        if self.field_item:
            self.name_entry.insert(0, self.field_item.name)
            self.area_entry.insert(0, str(self.field_item.area))

            current_soil = SOIL_TYPES.get(
                self.field_item.soil_type,
                self.field_item.soil_type,
            )

            if current_soil in SOIL_TYPES.values():
                self.soil_menu.set(current_soil)

        buttons = ctk.CTkFrame(container, fg_color="transparent")
        buttons.pack(fill="x", pady=(14, 0))

        Styles.button(
            buttons,
            "Скасувати",
            self.destroy,
            variant="secondary",
            width=130,
        ).pack(side="right", padx=(10, 0))

        Styles.button(
            buttons,
            "Зберегти",
            self._save,
            width=130,
        ).pack(side="right")

    def _save(self):
        name = self.name_entry.get().strip()
        area = safe_float(self.area_entry.get())

        if not name:
            self.message_label.configure(text="Вкажіть назву поля.")
            return

        if area <= 0:
            self.message_label.configure(text="Площа має бути більшою за 0.")
            return

        soil_value = self.soil_menu.get()
        soil_key = ""

        for key, value in SOIL_TYPES.items():
            if value == soil_value:
                soil_key = key
                break

        if self.field_item:
            self.field_item.name = name
            self.field_item.area = area
            self.field_item.soil_type = soil_key
            self.ds.update_field(self.field_item)
        else:
            self.ds.add_field(
                Field(
                    name=name,
                    area=area,
                    soil_type=soil_key,
                )
            )

        if self.callback:
            self.callback()

        self.destroy()


# ==========================
# ПОСІВИ ТА ПРОДАЖ
# ==========================

class CropsView(ctk.CTkFrame):
    def __init__(self, parent, ds: DataService, app: App):
        super().__init__(parent, fg_color="transparent")

        self.ds = ds
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        Styles.label(
            header,
            "Посіви та продажі",
            size=30,
            bold=True,
        ).pack(side="left")

        Styles.button(
            header,
            "+ Новий посів",
            self._open_add_dialog,
            width=150,
        ).pack(side="right")

        self.table = Styles.card(self)
        self.table.grid(row=1, column=0, sticky="nsew")

        self.refresh()

    def refresh(self):
        for widget in self.table.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(
            self.table,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=0,
        )
        header.pack(fill="x", padx=14, pady=(14, 0))

        columns = [
            ("Поле", 125),
            ("Культура", 130),
            ("Дата", 95),
            ("План т/га", 80),
            ("Продано", 85),
            ("Ціна", 95),
            ("Дохід", 110),
            ("Статус", 85),
            ("Дії", 190),
        ]

        for text, width in columns:
            Styles.label(
                header,
                text,
                size=12,
                color=COLORS["text_muted"],
                width=width,
            ).pack(side="left", padx=4, pady=11)

        scroll = ctk.CTkScrollableFrame(
            self.table,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=14)

        crops = self.ds.get_crops()
        fields_map = {item.id: item.name for item in self.ds.get_fields()}

        if not crops:
            Styles.label(
                scroll,
                "Немає посівів. Натисніть '+ Новий посів'.",
                size=14,
                color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        status_map = {
            "planted": "Посіяно",
            "growing": "Росте",
            "harvested": "Зібрано",
            "sold": "Продано",
        }

        for item in crops:
            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            crop_name = CROPS.get(item.crop_type, {}).get("name", item.crop_type)

            sold_text = "-"
            if safe_float(item.sold_quantity_tons) > 0:
                sold_text = tons(safe_float(item.sold_quantity_tons))

            price_text = "-"
            if safe_float(item.sale_price_per_ton) > 0:
                price_text = f"{safe_float(item.sale_price_per_ton):.0f}"

            revenue = item.calculate_revenue()
            revenue_text = "-" if revenue <= 0 else money(revenue)

            status_text = status_map.get(item.status, item.status)

            values = [
                fields_map.get(item.field_id, "Немає поля"),
                crop_name,
                item.planting_date,
                f"{safe_float(item.expected_yield):.1f}",
                sold_text,
                price_text,
                revenue_text,
                status_text,
            ]

            widths = [125, 130, 95, 80, 85, 95, 110, 85]

            for index, (text, width) in enumerate(zip(values, widths)):
                color = COLORS["text_primary"]

                if index == 7 and status_text == "Продано":
                    color = COLORS["success"]

                Styles.label(
                    row,
                    text,
                    size=13,
                    width=width,
                    color=color,
                ).pack(side="left", padx=4, pady=10)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=8)

            Styles.button(
                actions,
                "Продати",
                lambda c=item: self._open_sell_dialog(c),
                width=76,
                height=30,
            ).pack(side="left", padx=3)

            Styles.button(
                actions,
                "Ред.",
                lambda c=item: self._open_edit_dialog(c),
                variant="secondary",
                width=55,
                height=30,
            ).pack(side="left", padx=3)

            Styles.button(
                actions,
                "X",
                lambda c=item: self._delete_crop(c),
                variant="danger",
                width=38,
                height=30,
            ).pack(side="left", padx=3)

    def _open_add_dialog(self):
        CropDialog(self, self.ds, callback=self.refresh)

    def _open_edit_dialog(self, item: Crop):
        CropDialog(self, self.ds, crop_item=item, callback=self.refresh)

    def _open_sell_dialog(self, item: Crop):
        SellCropDialog(self, self.ds, item, callback=self.refresh)

    def _delete_crop(self, item: Crop):
        self.ds.delete_crop(item.id)
        self.refresh()


class CropDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        ds: DataService,
        crop_item: Optional[Crop] = None,
        callback=None,
    ):
        super().__init__(parent)

        self.ds = ds
        self.crop_item = crop_item
        self.callback = callback

        self.title("Посів")
        self.geometry("620x760")
        self.minsize(580, 620)
        self.resizable(True, True)
        self.configure(fg_color=COLORS["bg_secondary"])
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build()

    def _build(self):
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        form.grid(row=0, column=0, sticky="nsew", padx=24, pady=(24, 12))

        title = "Редагування посіву" if self.crop_item else "Новий посів"

        Styles.label(
            form,
            title,
            size=22,
            bold=True,
        ).pack(anchor="w", pady=(0, 20))

        fields = self.ds.get_fields()
        field_names = [item.name for item in fields] if fields else ["Спочатку додайте поле"]

        Styles.label(
            form,
            "Поле",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.field_menu = Styles.option(form, field_names, 520)
        self.field_menu.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Культура",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        crop_names = [item["name"] for item in CROPS.values()]
        self.crop_menu = Styles.option(form, crop_names, 520)
        self.crop_menu.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Дата посіву",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.date_entry = Styles.entry(form, "2024-04-15", 520)
        self.date_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Очікувана врожайність, т/га",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.yield_entry = Styles.entry(form, "Наприклад: 6.5", 520)
        self.yield_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Планова ціна, грн/т",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.price_entry = Styles.entry(form, "Наприклад: 6000", 520)
        self.price_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Витрати на посів, грн",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.expenses_entry = Styles.entry(form, "Насіння, добрива тощо", 520)
        self.expenses_entry.pack(fill="x", pady=(0, 12))

        if self.crop_item:
            for f in fields:
                if f.id == self.crop_item.field_id:
                    self.field_menu.set(f.name)
                    break

            crop_name = CROPS.get(
                self.crop_item.crop_type,
                {},
            ).get("name", "")

            if crop_name in crop_names:
                self.crop_menu.set(crop_name)

            self.date_entry.insert(0, self.crop_item.planting_date)
            self.yield_entry.insert(0, str(self.crop_item.expected_yield))
            self.price_entry.insert(0, str(self.crop_item.price_per_ton))
            self.expenses_entry.insert(0, str(self.crop_item.total_expenses))
        else:
            self.date_entry.insert(0, today())

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))

        self.message_label = Styles.label(
            bottom,
            "",
            size=12,
            color=COLORS["error"],
        )
        self.message_label.pack(side="left")

        Styles.button(
            bottom,
            "Скасувати",
            self.destroy,
            variant="secondary",
            width=130,
        ).pack(side="right", padx=(10, 0))

        button_text = "Зберегти" if self.crop_item else "Додати посів"

        Styles.button(
            bottom,
            button_text,
            self._save,
            width=150,
        ).pack(side="right")

    def _save(self):
        fields = self.ds.get_fields()

        if not fields:
            self.message_label.configure(text="Спочатку додайте хоча б одне поле.")
            return

        field_name = self.field_menu.get()
        field_id = None

        for item in fields:
            if item.name == field_name:
                field_id = item.id
                break

        if not field_id:
            self.message_label.configure(text="Оберіть поле.")
            return

        crop_name = self.crop_menu.get()
        crop_type = None

        for key, value in CROPS.items():
            if value["name"] == crop_name:
                crop_type = key
                break

        if not crop_type:
            self.message_label.configure(text="Оберіть культуру.")
            return

        planting_date = self.date_entry.get().strip()
        expected_yield = safe_float(self.yield_entry.get())
        price = safe_float(self.price_entry.get())
        expenses = safe_float(self.expenses_entry.get())

        if not planting_date:
            self.message_label.configure(text="Вкажіть дату посіву.")
            return

        if expected_yield <= 0:
            self.message_label.configure(text="Очікувана врожайність має бути більшою за 0.")
            return

        if self.crop_item:
            self.crop_item.field_id = field_id
            self.crop_item.crop_type = crop_type
            self.crop_item.planting_date = planting_date
            self.crop_item.expected_yield = expected_yield
            self.crop_item.price_per_ton = price
            self.crop_item.total_expenses = expenses
            self.ds.update_crop(self.crop_item)
        else:
            self.ds.add_crop(
                Crop(
                    field_id=field_id,
                    crop_type=crop_type,
                    planting_date=planting_date,
                    expected_yield=expected_yield,
                    price_per_ton=price,
                    total_expenses=expenses,
                    status="planted",
                )
            )

        if self.callback:
            self.callback()

        self.destroy()


class SellCropDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        ds: DataService,
        crop_item: Crop,
        callback=None,
    ):
        super().__init__(parent)

        self.ds = ds
        self.crop_item = crop_item
        self.callback = callback

        self.field_item = next(
            (item for item in self.ds.get_fields() if item.id == self.crop_item.field_id),
            None,
        )

        self.title("Продаж культури")
        self.geometry("620x680")
        self.resizable(True, True)
        self.configure(fg_color=COLORS["bg_secondary"])
        self.grab_set()

        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        Styles.label(
            container,
            "Продаж культури",
            size=22,
            bold=True,
        ).pack(anchor="w", pady=(0, 18))

        field_name = self.field_item.name if self.field_item else "Невідоме поле"
        crop_name = CROPS.get(self.crop_item.crop_type, {}).get(
            "name",
            self.crop_item.crop_type,
        )

        Styles.label(
            container,
            f"Поле: {field_name}",
            size=13,
            color=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        Styles.label(
            container,
            f"Культура: {crop_name}",
            size=13,
            color=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, 18))

        Styles.label(
            container,
            "Дата продажу",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.date_entry = Styles.entry(container, "2024-08-20", 460)
        self.date_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            container,
            "Продано, тонн",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.quantity_entry = Styles.entry(container, "Наприклад: 120", 460)
        self.quantity_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            container,
            "Ціна за 1 тонну, грн",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.price_entry = Styles.entry(container, "Наприклад: 6500", 460)
        self.price_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            container,
            "Покупець",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.buyer_entry = Styles.entry(container, "Назва покупця", 460)
        self.buyer_entry.pack(fill="x", pady=(0, 14))

        self.result_label = Styles.label(
            container,
            "",
            size=13,
            color=COLORS["accent"],
        )
        self.result_label.pack(anchor="w", pady=(0, 14))

        if self.crop_item.sale_date:
            self.date_entry.insert(0, self.crop_item.sale_date)
        else:
            self.date_entry.insert(0, today())

        if safe_float(self.crop_item.sold_quantity_tons) > 0:
            self.quantity_entry.insert(0, str(self.crop_item.sold_quantity_tons))

        if safe_float(self.crop_item.sale_price_per_ton) > 0:
            self.price_entry.insert(0, str(self.crop_item.sale_price_per_ton))
        elif safe_float(self.crop_item.price_per_ton) > 0:
            self.price_entry.insert(0, str(self.crop_item.price_per_ton))

        if self.crop_item.buyer:
            self.buyer_entry.insert(0, self.crop_item.buyer)

        self.quantity_entry.bind("<KeyRelease>", self._update_preview)
        self.price_entry.bind("<KeyRelease>", self._update_preview)

        buttons = ctk.CTkFrame(container, fg_color="transparent")
        buttons.pack(fill="x", pady=(10, 0))

        Styles.button(
            buttons,
            "Скасувати",
            self.destroy,
            variant="secondary",
            width=150,
        ).pack(side="right", padx=(10, 0))

        Styles.button(
            buttons,
            "Зберегти продаж",
            self._save_sale,
            width=170,
        ).pack(side="right")

        self._update_preview()

    def _update_preview(self, event=None):
        quantity = safe_float(self.quantity_entry.get())
        price = safe_float(self.price_entry.get())
        revenue = quantity * price

        if revenue > 0:
            self.result_label.configure(
                text=f"Дохід від продажу: {money(revenue)}",
                text_color=COLORS["accent"],
            )
        else:
            self.result_label.configure(text="")

    def _save_sale(self):
        sale_date = self.date_entry.get().strip()
        quantity = safe_float(self.quantity_entry.get())
        price = safe_float(self.price_entry.get())
        buyer = self.buyer_entry.get().strip()

        if not sale_date:
            self.result_label.configure(
                text="Вкажіть дату продажу.",
                text_color=COLORS["error"],
            )
            return

        if quantity <= 0:
            self.result_label.configure(
                text="Кількість проданої культури має бути більшою за 0.",
                text_color=COLORS["error"],
            )
            return

        if price <= 0:
            self.result_label.configure(
                text="Ціна за тонну має бути більшою за 0.",
                text_color=COLORS["error"],
            )
            return

        self.crop_item.sale_date = sale_date
        self.crop_item.sold_quantity_tons = quantity
        self.crop_item.sale_price_per_ton = price
        self.crop_item.buyer = buyer
        self.crop_item.price_per_ton = price
        self.crop_item.status = "sold"

        if self.field_item and safe_float(self.field_item.area) > 0:
            self.crop_item.actual_yield = quantity / safe_float(self.field_item.area)

        self.ds.update_crop(self.crop_item)

        if self.callback:
            self.callback()

        self.destroy()


# ==========================
# ЖУРНАЛ РОБІТ
# ==========================

class JournalView(ctk.CTkFrame):
    def __init__(self, parent, ds: DataService, app: App):
        super().__init__(parent, fg_color="transparent")

        self.ds = ds
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        Styles.label(
            header,
            "Журнал робіт",
            size=30,
            bold=True,
        ).pack(side="left")

        Styles.button(
            header,
            "+ Записати роботу",
            self._open_add_dialog,
            width=170,
        ).pack(side="right")

        self.table = Styles.card(self)
        self.table.grid(row=1, column=0, sticky="nsew")

        self.refresh()

    def refresh(self):
        for widget in self.table.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(
            self.table,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=0,
        )
        header.pack(fill="x", padx=14, pady=(14, 0))

        columns = [
            ("Дата", 100),
            ("Поле", 140),
            ("Операція", 170),
            ("Годин", 70),
            ("Пальне", 90),
            ("Інші", 90),
            ("Разом", 100),
            ("Дії", 150),
        ]

        for text, width in columns:
            Styles.label(
                header,
                text,
                size=12,
                color=COLORS["text_muted"],
                width=width,
            ).pack(side="left", padx=4, pady=11)

        scroll = ctk.CTkScrollableFrame(
            self.table,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=14)

        works = sorted(
            self.ds.get_work_records(),
            key=lambda item: item.date,
            reverse=True,
        )

        fields_map = {item.id: item.name for item in self.ds.get_fields()}

        if not works:
            Styles.label(
                scroll,
                "Немає робіт. Натисніть '+ Записати роботу'.",
                size=14,
                color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for item in works:
            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            values = [
                item.date,
                fields_map.get(item.field_id, "Немає поля"),
                item.operation,
                f"{safe_float(item.duration_hours):.1f}",
                money(safe_float(item.fuel_cost)),
                money(safe_float(item.other_cost)),
                money(item.get_total_cost()),
            ]

            widths = [100, 140, 170, 70, 90, 90, 100]

            for text, width in zip(values, widths):
                Styles.label(
                    row,
                    text,
                    size=13,
                    width=width,
                ).pack(side="left", padx=4, pady=10)

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=8)

            Styles.button(
                actions,
                "Ред.",
                lambda w=item: self._open_edit_dialog(w),
                variant="secondary",
                width=55,
                height=30,
            ).pack(side="left", padx=3)

            Styles.button(
                actions,
                "X",
                lambda w=item: self._delete_work(w),
                variant="danger",
                width=38,
                height=30,
            ).pack(side="left", padx=3)

    def _open_add_dialog(self):
        WorkDialog(self, self.ds, callback=self.refresh)

    def _open_edit_dialog(self, item: WorkRecord):
        WorkDialog(self, self.ds, work_item=item, callback=self.refresh)

    def _delete_work(self, item: WorkRecord):
        self.ds.delete_work_record(item.id)
        self.refresh()


class WorkDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        ds: DataService,
        work_item: Optional[WorkRecord] = None,
        callback=None,
    ):
        super().__init__(parent)

        self.ds = ds
        self.work_item = work_item
        self.callback = callback

        self.title("Робота")
        self.geometry("560x720")
        self.minsize(520, 620)
        self.resizable(True, True)
        self.configure(fg_color=COLORS["bg_secondary"])
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build()

    def _build(self):
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        form.grid(row=0, column=0, sticky="nsew", padx=24, pady=(24, 12))

        title = "Редагування роботи" if self.work_item else "Нова робота"

        Styles.label(
            form,
            title,
            size=22,
            bold=True,
        ).pack(anchor="w", pady=(0, 20))

        fields = self.ds.get_fields()
        field_names = [item.name for item in fields] if fields else ["Спочатку додайте поле"]

        Styles.label(
            form,
            "Поле",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.field_menu = Styles.option(form, field_names, 470)
        self.field_menu.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Дата",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.date_entry = Styles.entry(form, "2024-04-15", 470)
        self.date_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Операція",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.operation_menu = Styles.option(form, FIELD_OPERATIONS, 470)
        self.operation_menu.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Тривалість, годин",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.duration_entry = Styles.entry(form, "Наприклад: 8", 470)
        self.duration_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Техніка",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.equipment_entry = Styles.entry(form, "Трактор, сівалка тощо", 470)
        self.equipment_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Кількість працівників",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.workers_entry = Styles.entry(form, "Наприклад: 2", 470)
        self.workers_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Витрати на пальне, грн",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.fuel_entry = Styles.entry(form, "Наприклад: 3500", 470)
        self.fuel_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Інші витрати, грн",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.other_entry = Styles.entry(form, "Добрива, ЗЗР, ремонт, зарплата", 470)
        self.other_entry.pack(fill="x", pady=(0, 12))

        Styles.label(
            form,
            "Опис",
            size=12,
            color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 5))

        self.description_box = Styles.textbox(form, 470, 90)
        self.description_box.pack(fill="x", pady=(0, 12))

        if self.work_item:
            for f in fields:
                if f.id == self.work_item.field_id:
                    self.field_menu.set(f.name)
                    break

            self.date_entry.insert(0, self.work_item.date)

            if self.work_item.operation in FIELD_OPERATIONS:
                self.operation_menu.set(self.work_item.operation)

            self.duration_entry.insert(0, str(self.work_item.duration_hours))
            self.equipment_entry.insert(0, self.work_item.equipment)
            self.workers_entry.insert(0, str(self.work_item.workers_count))
            self.fuel_entry.insert(0, str(self.work_item.fuel_cost))
            self.other_entry.insert(0, str(self.work_item.other_cost))
            self.description_box.insert("1.0", self.work_item.description)
        else:
            self.date_entry.insert(0, today())
            self.workers_entry.insert(0, "1")

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 24))

        self.message_label = Styles.label(
            bottom,
            "",
            size=12,
            color=COLORS["error"],
        )
        self.message_label.pack(side="left")

        Styles.button(
            bottom,
            "Скасувати",
            self.destroy,
            variant="secondary",
            width=130,
        ).pack(side="right", padx=(10, 0))

        Styles.button(
            bottom,
            "Зберегти",
            self._save,
            width=130,
        ).pack(side="right")

    def _save(self):
        fields = self.ds.get_fields()

        if not fields:
            self.message_label.configure(text="Спочатку додайте хоча б одне поле.")
            return

        field_name = self.field_menu.get()
        field_id = None

        for item in fields:
            if item.name == field_name:
                field_id = item.id
                break

        if not field_id:
            self.message_label.configure(text="Оберіть поле.")
            return

        date_value = self.date_entry.get().strip()
        operation = self.operation_menu.get()
        duration = safe_float(self.duration_entry.get())
        equipment = self.equipment_entry.get().strip()
        workers = safe_int(self.workers_entry.get(), 1)
        fuel = safe_float(self.fuel_entry.get())
        other = safe_float(self.other_entry.get())
        description = self.description_box.get("1.0", "end").strip()

        if not date_value:
            self.message_label.configure(text="Вкажіть дату.")
            return

        if self.work_item:
            self.work_item.field_id = field_id
            self.work_item.date = date_value
            self.work_item.operation = operation
            self.work_item.duration_hours = duration
            self.work_item.equipment = equipment
            self.work_item.workers_count = workers
            self.work_item.fuel_cost = fuel
            self.work_item.other_cost = other
            self.work_item.description = description
            self.ds.update_work_record(self.work_item)
        else:
            self.ds.add_work_record(
                WorkRecord(
                    field_id=field_id,
                    date=date_value,
                    operation=operation,
                    duration_hours=duration,
                    equipment=equipment,
                    workers_count=workers,
                    fuel_cost=fuel,
                    other_cost=other,
                    description=description,
                )
            )

        if self.callback:
            self.callback()

        self.destroy()


# ==========================
# АНАЛІТИКА
# ==========================

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, ds: DataService, app: App):
        super().__init__(parent, fg_color="transparent")

        self.ds = ds
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build()

    def _build(self):
        Styles.label(
            self,
            "Аналітика господарства",
            size=30,
            bold=True,
        ).grid(row=0, column=0, sticky="w", pady=(0, 22))

        self._summary_cards()
        self._field_table()

    def _summary_cards(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew")

        for i in range(4):
            frame.grid_columnconfigure(i, weight=1)

        revenue = self.ds.get_total_revenue()
        crop_expenses = self.ds.get_total_crop_expenses()
        work_expenses = self.ds.get_total_work_expenses()
        expenses = crop_expenses + work_expenses
        profit = revenue - expenses
        roi = (profit / expenses * 100) if expenses > 0 else 0

        cards = [
            ("Дохід", money(revenue), COLORS["accent"]),
            ("Витрати", money(expenses), COLORS["warning"]),
            ("Прибуток", money(profit), COLORS["success"] if profit >= 0 else COLORS["error"]),
            ("Рентабельність", f"{roi:.1f}%", COLORS["blue"]),
        ]

        for index, (title, value, color) in enumerate(cards):
            card = Styles.card(frame, height=112)
            card.grid(row=0, column=index, sticky="ew", padx=8)
            card.grid_propagate(False)

            Styles.label(
                card,
                value,
                size=24,
                color=color,
                bold=True,
            ).place(x=18, y=24)

            Styles.label(
                card,
                title,
                size=12,
                color=COLORS["text_muted"],
            ).place(x=18, y=68)

    def _field_table(self):
        table = Styles.card(self)
        table.grid(row=2, column=0, sticky="nsew", pady=(22, 0))

        Styles.label(
            table,
            "Рентабельність по полях",
            size=20,
            bold=True,
        ).pack(anchor="w", padx=20, pady=(18, 10))

        header = ctk.CTkFrame(
            table,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=0,
        )
        header.pack(fill="x", padx=14)

        columns = [
            ("Поле", 170),
            ("Площа", 90),
            ("Дохід", 130),
            ("Витрати посіву", 130),
            ("Витрати робіт", 130),
            ("Прибуток", 130),
            ("ROI", 80),
        ]

        for text, width in columns:
            Styles.label(
                header,
                text,
                size=12,
                color=COLORS["text_muted"],
                width=width,
            ).pack(side="left", padx=4, pady=11)

        scroll = ctk.CTkScrollableFrame(
            table,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
        )
        scroll.pack(fill="both", expand=True, padx=14, pady=14)

        fields = self.ds.get_fields()

        if not fields:
            Styles.label(
                scroll,
                "Немає даних для аналітики.",
                size=14,
                color=COLORS["text_muted"],
            ).pack(pady=40)
            return

        for field_item in fields:
            revenue = self.ds.get_field_revenue(field_item.id)
            crop_expenses = self.ds.get_field_crop_expenses(field_item.id)
            work_expenses = self.ds.get_field_work_expenses(field_item.id)
            expenses = crop_expenses + work_expenses
            profit = revenue - expenses
            roi = (profit / expenses * 100) if expenses > 0 else 0

            row = ctk.CTkFrame(
                scroll,
                fg_color=COLORS["bg_tertiary"],
                corner_radius=10,
            )
            row.pack(fill="x", pady=4)

            values = [
                field_item.name,
                f"{safe_float(field_item.area):.1f} га",
                money(revenue),
                money(crop_expenses),
                money(work_expenses),
                money(profit),
                f"{roi:.1f}%",
            ]

            widths = [170, 90, 130, 130, 130, 130, 80]

            for index, (text, width) in enumerate(zip(values, widths)):
                color = COLORS["text_primary"]

                if index == 5:
                    color = COLORS["success"] if profit >= 0 else COLORS["error"]

                Styles.label(
                    row,
                    text,
                    size=13,
                    width=width,
                    color=color,
                ).pack(side="left", padx=4, pady=10)


# ==========================
# ЗАПУСК
# ==========================

def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
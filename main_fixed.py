import json
import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform


APP_NAME = "EntekhabReshtehAndroid"
MAX_CHOICES = 150

# ---------- colors ----------
BG = (0.96, 0.96, 0.96, 1)
ROW_BG = (1, 1, 1, 1)
TEXT = (0.08, 0.08, 0.08, 1)
MUTED = (0.38, 0.38, 0.38, 1)
BTN = (0.22, 0.45, 0.78, 1)
DANGER = (0.72, 0.16, 0.16, 1)


# =========================================================
# Resource helpers
# =========================================================

def resource_path(name: str) -> Path:
    """
    Works in normal Python and with Android/Buildozer.
    Put majors.db and optional fonts folder beside main.py.
    """
    return Path(__file__).resolve().parent / name


def app_data_dir() -> Path:
    app = App.get_running_app()
    path = Path(app.user_data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


# =========================================================
# Persian font
# =========================================================

def find_persian_font() -> str | None:
    """
    Priority:
      1) bundled project font
      2) Windows fonts for desktop testing
      3) common Android system fonts
    """
    candidates = [
        resource_path("fonts/Vazirmatn-Regular.ttf"),
        resource_path("fonts/Vazirmatn.ttf"),
        resource_path("fonts/IRANSans.ttf"),
    ]

    if os.name == "nt":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        fonts = windir / "Fonts"
        candidates.extend([
            fonts / "tahoma.ttf",
            fonts / "segoeui.ttf",
            fonts / "arial.ttf",
        ])

    candidates.extend([
        Path("/system/fonts/NotoNaskhArabic-Regular.ttf"),
        Path("/system/fonts/NotoSansArabic-Regular.ttf"),
        Path("/system/fonts/NotoSansArabicUI-Regular.ttf"),
        Path("/system/fonts/NotoSans-Regular.ttf"),
    ])

    for path in candidates:
        try:
            if path.exists():
                return str(path)
        except Exception:
            pass
    return None


PERSIAN_FONT_PATH = find_persian_font()
PERSIAN_FONT_NAME = "Roboto"

if PERSIAN_FONT_PATH:
    try:
        LabelBase.register(
            name="PersianAppFont",
            fn_regular=PERSIAN_FONT_PATH,
        )
        PERSIAN_FONT_NAME = "PersianAppFont"
    except Exception:
        pass


# =========================================================
# Persian / RTL
# =========================================================

# Local fallback shaper, so the app does not require arabic-reshaper/python-bidi
# merely to start. If those libraries are installed, they are used automatically.
_ARABIC_FORMS = {
    "ء": ("ﺀ", None, None, None), "آ": ("ﺁ", "ﺂ", None, None),
    "أ": ("ﺃ", "ﺄ", None, None), "ؤ": ("ﺅ", "ﺆ", None, None),
    "إ": ("ﺇ", "ﺈ", None, None), "ئ": ("ﺉ", "ﺊ", "ﺋ", "ﺌ"),
    "ا": ("ﺍ", "ﺎ", None, None), "ب": ("ﺏ", "ﺐ", "ﺑ", "ﺒ"),
    "ة": ("ﺓ", "ﺔ", None, None), "ت": ("ﺕ", "ﺖ", "ﺗ", "ﺘ"),
    "ث": ("ﺙ", "ﺚ", "ﺛ", "ﺜ"), "ج": ("ﺝ", "ﺞ", "ﺟ", "ﺠ"),
    "ح": ("ﺡ", "ﺢ", "ﺣ", "ﺤ"), "خ": ("ﺥ", "ﺦ", "ﺧ", "ﺨ"),
    "د": ("ﺩ", "ﺪ", None, None), "ذ": ("ﺫ", "ﺬ", None, None),
    "ر": ("ﺭ", "ﺮ", None, None), "ز": ("ﺯ", "ﺰ", None, None),
    "س": ("ﺱ", "ﺲ", "ﺳ", "ﺴ"), "ش": ("ﺵ", "ﺶ", "ﺷ", "ﺸ"),
    "ص": ("ﺹ", "ﺺ", "ﺻ", "ﺼ"), "ض": ("ﺽ", "ﺾ", "ﺿ", "ﻀ"),
    "ط": ("ﻁ", "ﻂ", "ﻃ", "ﻄ"), "ظ": ("ﻅ", "ﻆ", "ﻇ", "ﻈ"),
    "ع": ("ﻉ", "ﻊ", "ﻋ", "ﻌ"), "غ": ("ﻍ", "ﻎ", "ﻏ", "ﻐ"),
    "ف": ("ﻑ", "ﻒ", "ﻓ", "ﻔ"), "ق": ("ﻕ", "ﻖ", "ﻗ", "ﻘ"),
    "ك": ("ﻙ", "ﻚ", "ﻛ", "ﻜ"), "ک": ("ﮎ", "ﮏ", "ﮐ", "ﮑ"),
    "ل": ("ﻝ", "ﻞ", "ﻟ", "ﻠ"), "م": ("ﻡ", "ﻢ", "ﻣ", "ﻤ"),
    "ن": ("ﻥ", "ﻦ", "ﻧ", "ﻨ"), "ه": ("ﻩ", "ﻪ", "ﻫ", "ﻬ"),
    "و": ("ﻭ", "ﻮ", None, None), "ى": ("ﻯ", "ﻰ", None, None),
    "ي": ("ﻱ", "ﻲ", "ﻳ", "ﻴ"), "ی": ("ﯼ", "ﯽ", "ﯾ", "ﯿ"),
    "پ": ("ﭖ", "ﭗ", "ﭘ", "ﭙ"), "چ": ("ﭺ", "ﭻ", "ﭼ", "ﭽ"),
    "ژ": ("ﮊ", "ﮋ", None, None), "گ": ("ﮒ", "ﮓ", "ﮔ", "ﮕ"),
    "ۀ": ("ﮤ", "ﮥ", None, None),
}


def _can_connect_to_previous(ch: str) -> bool:
    forms = _ARABIC_FORMS.get(ch)
    return bool(forms and forms[1])


def _can_connect_to_next(ch: str) -> bool:
    forms = _ARABIC_FORMS.get(ch)
    return bool(forms and forms[2])


def _fallback_rtl(text: str) -> str:
    chars = list(text)
    shaped = []

    for i, ch in enumerate(chars):
        forms = _ARABIC_FORMS.get(ch)
        if not forms:
            shaped.append(ch)
            continue

        prev_ch = chars[i - 1] if i > 0 else ""
        next_ch = chars[i + 1] if i + 1 < len(chars) else ""

        join_prev = _can_connect_to_next(prev_ch) and _can_connect_to_previous(ch)
        join_next = _can_connect_to_next(ch) and _can_connect_to_previous(next_ch)

        isolated, final, initial, medial = forms

        if join_prev and join_next and medial:
            shaped.append(medial)
        elif join_prev and final:
            shaped.append(final)
        elif join_next and initial:
            shaped.append(initial)
        else:
            shaped.append(isolated)

    visual = "".join(shaped)[::-1]

    # Keep numeric / latin runs in their natural order.
    visual = re.sub(
        r"[A-Za-z0-9۰-۹٠-٩._/+%:-]+",
        lambda m: m.group(0)[::-1],
        visual,
    )

    return visual.translate(
        str.maketrans({
            "(": ")", ")": "(",
            "[": "]", "]": "[",
            "{": "}", "}": "{",
            "<": ">", ">": "<",
            "«": "»", "»": "«",
        })
    )


def fa(value) -> str:
    """
    Proper RTL when arabic_reshaper + python-bidi are available.
    Safe local fallback otherwise.
    """
    text = str(value or "")
    if not text:
        return ""

    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return _fallback_rtl(text)


def normalize_digits(value) -> str:
    value = str(value or "").strip()
    fa_digits = "۰۱۲۳۴۵۶۷۸۹"
    ar_digits = "٠١٢٣٤٥٦٧٨٩"
    en_digits = "0123456789"

    for src, dst in zip(fa_digits, en_digits):
        value = value.replace(src, dst)
    for src, dst in zip(ar_digits, en_digits):
        value = value.replace(src, dst)

    return value


# =========================================================
# Widget helpers
# =========================================================

def make_label(text="", **kwargs):
    kwargs.setdefault("font_name", PERSIAN_FONT_NAME)
    kwargs.setdefault("color", TEXT)
    return Label(text=text, **kwargs)


def make_button(text="", **kwargs):
    kwargs.setdefault("font_name", PERSIAN_FONT_NAME)
    kwargs.setdefault("background_normal", "")
    kwargs.setdefault("background_color", BTN)
    kwargs.setdefault("color", (1, 1, 1, 1))
    return Button(text=text, **kwargs)


# =========================================================
# Database
# =========================================================

class MajorDatabase:
    def __init__(self):
        self.path = resource_path("majors.db")

    def get(self, code: str):
        if not self.path.exists():
            raise FileNotFoundError(
                f"majors.db پیدا نشد:\n{self.path}"
            )

        with sqlite3.connect(str(self.path)) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                """
                SELECT
                    code,
                    group_name,
                    admission,
                    course,
                    major,
                    university,
                    province,
                    semester,
                    gender,
                    notes
                FROM majors
                WHERE code = ?
                """,
                (str(code),),
            ).fetchone()

        return dict(row) if row else None


# =========================================================
# RecycleView row
# =========================================================

class ChoiceRow(RecycleDataViewBehavior, BoxLayout):
    row_index = NumericProperty(0)
    priority = StringProperty("")
    code = StringProperty("")
    major = StringProperty("")
    university = StringProperty("")
    course = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(3),
            padding=(dp(3), dp(3)),
            **kwargs,
        )

        self.item = None

        # Visual order from LEFT to RIGHT.
        # Therefore priority ends up at the RIGHT side of the screen.
        self.delete_btn = make_button(
            "×",
            size_hint_x=None,
            width=dp(44),
            font_size="20sp",
            background_color=DANGER,
        )
        self.delete_btn.bind(on_release=self._delete)
        self.add_widget(self.delete_btn)

        self.course_lbl = make_label(
            size_hint_x=.12,
            halign="center",
            valign="middle",
            font_size="12sp",
        )
        self.add_widget(self.course_lbl)

        self.univ_lbl = make_label(
            size_hint_x=.30,
            halign="right",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="left",
        )
        self.add_widget(self.univ_lbl)

        self.major_lbl = make_label(
            size_hint_x=.27,
            halign="right",
            valign="middle",
            font_size="12sp",
            shorten=True,
            shorten_from="left",
        )
        self.add_widget(self.major_lbl)

        self.code_lbl = make_label(
            size_hint_x=.14,
            halign="center",
            valign="middle",
            font_size="12sp",
        )
        self.add_widget(self.code_lbl)

        self.priority_lbl = make_label(
            size_hint_x=.09,
            halign="center",
            valign="middle",
            font_size="12sp",
        )
        self.add_widget(self.priority_lbl)

        for widget in [
            self.course_lbl,
            self.univ_lbl,
            self.major_lbl,
            self.code_lbl,
            self.priority_lbl,
        ]:
            widget.bind(size=self._fit_text)
            widget.bind(on_touch_down=self._details_touch)

    @staticmethod
    def _fit_text(instance, _):
        instance.text_size = instance.size

    def refresh_view_attrs(self, rv, index, data):
        self.row_index = index
        self.item = data.get("item")
        self.priority = data.get("priority", "")
        self.code = data.get("code", "—")
        self.major = data.get("major", "—")
        self.university = data.get("university", "—")
        self.course = data.get("course", "—")

        result = super().refresh_view_attrs(rv, index, data)
        self._sync()
        return result

    def _sync(self):
        self.priority_lbl.text = self.priority
        self.code_lbl.text = self.code
        self.major_lbl.text = fa(self.major)
        self.univ_lbl.text = fa(self.university)
        self.course_lbl.text = fa(self.course)

        has_item = self.item is not None
        self.delete_btn.disabled = not has_item
        self.delete_btn.opacity = 1 if has_item else 0.15

    def _delete(self, *_):
        if self.item is not None:
            App.get_running_app().delete_choice(self.row_index)

    def _details_touch(self, widget, touch):
        if self.item is not None and widget.collide_point(*touch.pos):
            App.get_running_app().show_details(
                self.item,
                self.row_index + 1,
            )
            return True
        return False


class ChoicesRV(RecycleView):
    pass


# =========================================================
# Main UI
# =========================================================

class RootUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(5),
            padding=dp(6),
            **kwargs,
        )

        # ---------- top bar ----------
        top = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(6),
        )

        self.pdf_btn = make_button(
            "PDF",
            size_hint_x=.13,
        )
        self.pdf_btn.bind(
            on_release=lambda *_: App.get_running_app().export_pdf()
        )
        top.add_widget(self.pdf_btn)

        self.add_btn = make_button(
            fa("ثبت"),
            size_hint_x=.14,
        )
        self.add_btn.bind(
            on_release=lambda *_: App.get_running_app().add_choice()
        )
        top.add_widget(self.add_btn)

        self.priority_input = TextInput(
            hint_text=fa("اولویت"),
            multiline=False,
            input_filter="int",
            halign="center",
            size_hint_x=.16,
            font_size="16sp",
            font_name=PERSIAN_FONT_NAME,
            foreground_color=TEXT,
            background_color=(1, 1, 1, 1),
        )
        top.add_widget(self.priority_input)

        self.code_input = TextInput(
            hint_text=fa("کد رشته"),
            multiline=False,
            input_filter="int",
            halign="center",
            size_hint_x=.22,
            font_size="16sp",
            font_name=PERSIAN_FONT_NAME,
            foreground_color=TEXT,
            background_color=(1, 1, 1, 1),
        )
        self.code_input.bind(
            on_text_validate=lambda *_: App.get_running_app().add_choice()
        )
        top.add_widget(self.code_input)

        title = make_label(
            fa("انتخاب رشته آفلاین"),
            size_hint_x=.35,
            halign="right",
            valign="middle",
            font_size="18sp",
        )
        title.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
        top.add_widget(title)

        self.add_widget(top)

        # ---------- table header ----------
        header = BoxLayout(
            size_hint_y=None,
            height=dp(32),
            spacing=dp(3),
            padding=(dp(3), 0),
        )

        # Same visual order as row widgets: left -> right
        header_specs = [
            ("حذف", None, dp(44)),
            ("دوره", .12, None),
            ("دانشگاه", .30, None),
            ("رشته", .27, None),
            ("کدرشته", .14, None),
            ("اولویت", .09, None),
        ]

        for text, size_hint_x, width in header_specs:
            kwargs = {
                "halign": "center",
                "valign": "middle",
                "font_size": "11sp",
            }
            if width is not None:
                kwargs["size_hint_x"] = None
                kwargs["width"] = width
            else:
                kwargs["size_hint_x"] = size_hint_x

            lbl = make_label(fa(text), **kwargs)
            lbl.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
            header.add_widget(lbl)

        self.add_widget(header)

        # ---------- list ----------
        self.rv = ChoicesRV()

        layout = RecycleBoxLayout(
            default_size=(None, dp(52)),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation="vertical",
            spacing=dp(1),
        )
        layout.bind(minimum_height=layout.setter("height"))

        self.rv.add_widget(layout)
        self.rv.layout_manager = layout
        self.rv.viewclass = ChoiceRow

        self.add_widget(self.rv)

        # ---------- bottom ----------
        bottom = BoxLayout(
            size_hint_y=None,
            height=dp(34),
            spacing=dp(6),
        )

        self.status = make_label(
            fa("آماده"),
            halign="right",
            valign="middle",
            font_size="11sp",
        )
        self.status.bind(
            size=lambda inst, _: setattr(inst, "text_size", inst.size)
        )
        bottom.add_widget(self.status)

        self.count = make_label(
            "0 / 150",
            size_hint_x=.20,
            halign="center",
            valign="middle",
            font_size="12sp",
        )
        self.count.bind(
            size=lambda inst, _: setattr(inst, "text_size", inst.size)
        )
        bottom.add_widget(self.count)

        self.add_widget(bottom)


# =========================================================
# App
# =========================================================

class EntekhabApp(App):
    title = "Entekhab Reshteh"

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = "below_target"

        # Desktop preview roughly matching a landscape phone/tablet.
        if platform != "android":
            Window.size = (1100, 600)

        self.db = MajorDatabase()
        self.choices = [None] * MAX_CHOICES
        self.root_ui = RootUI()

        self.load_choices()
        Clock.schedule_once(lambda *_: self.refresh(), 0)

        return self.root_ui

    @property
    def save_path(self) -> Path:
        return app_data_dir() / "choices.json"

    def load_choices(self):
        try:
            if self.save_path.exists():
                raw = json.loads(
                    self.save_path.read_text(encoding="utf-8")
                )
                if isinstance(raw, list):
                    self.choices = (
                        raw + [None] * MAX_CHOICES
                    )[:MAX_CHOICES]
        except Exception:
            self.choices = [None] * MAX_CHOICES

    def save_choices(self):
        self.save_path.write_text(
            json.dumps(
                self.choices,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def set_status(self, text: str):
        self.root_ui.status.text = fa(text)

    # -----------------------------------------------------
    # Add
    # -----------------------------------------------------

    def add_choice(self):
        code = normalize_digits(self.root_ui.code_input.text)
        priority_text = normalize_digits(
            self.root_ui.priority_input.text
        )

        if not code or not priority_text:
            self.alert("کد رشته و اولویت را وارد کنید")
            return

        if not code.isdigit() or not priority_text.isdigit():
            self.alert("کد رشته و اولویت باید عدد باشند")
            return

        priority = int(priority_text)

        if not 1 <= priority <= MAX_CHOICES:
            self.alert("اولویت باید بین 1 تا 150 باشد")
            return

        try:
            item = self.db.get(code)
        except Exception as exc:
            self.alert(str(exc))
            return

        if not item:
            self.alert(f"کدرشته {code} پیدا نشد")
            return

        # Remove duplicate code from old position.
        for i, old in enumerate(self.choices):
            if old and str(old.get("code")) == code:
                self.choices[i] = None

        target = priority - 1

        # If empty: place exactly at requested priority.
        if self.choices[target] is None:
            self.choices[target] = item

        # If occupied: shift everything down by one.
        else:
            carry = item
            for i in range(target, MAX_CHOICES):
                current = self.choices[i]
                self.choices[i] = carry
                carry = current
                if carry is None:
                    break

        self.save_choices()

        self.root_ui.code_input.text = ""
        self.root_ui.priority_input.text = ""

        self.set_status(
            f"کدرشته {code} در اولویت {priority} ثبت شد"
        )
        self.refresh(scroll_to=target)

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    def delete_choice(self, index: int):
        if 0 <= index < MAX_CHOICES:
            if self.choices[index] is not None:
                self.choices[index] = None
                self.save_choices()
                self.set_status(
                    f"اولویت {index + 1} حذف شد"
                )
                self.refresh()

    # -----------------------------------------------------
    # Refresh
    # -----------------------------------------------------

    def refresh(self, scroll_to=None):
        data = []
        count = 0

        for i in range(MAX_CHOICES):
            item = self.choices[i]

            if item:
                count += 1
                data.append({
                    "priority": str(i + 1),
                    "code": str(item.get("code", "—")),
                    "major": item.get("major", "—"),
                    "university": item.get("university", "—"),
                    "course": item.get("course", "—"),
                    "item": item,
                })
            else:
                data.append({
                    "priority": str(i + 1),
                    "code": "—",
                    "major": "—",
                    "university": "—",
                    "course": "—",
                    "item": None,
                })

        self.root_ui.rv.data = data
        self.root_ui.count.text = f"{count} / 150"

        if scroll_to is not None:
            self.root_ui.rv.scroll_y = max(
                0,
                min(
                    1,
                    1 - (
                        scroll_to /
                        max(1, MAX_CHOICES - 1)
                    ),
                ),
            )

    # -----------------------------------------------------
    # Details
    # -----------------------------------------------------

    def show_details(self, item: dict, priority: int):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5),
        )

        fields = [
            ("اولویت", priority),
            ("کدرشته", item.get("code", "—")),
            ("رشته", item.get("major", "—")),
            ("دانشگاه", item.get("university", "—")),
            ("استان", item.get("province", "—")),
            ("دوره", item.get("course", "—")),
            ("پذیرش", item.get("admission", "—")),
            ("نیمسال", item.get("semester", "—")),
            ("جنسیت", item.get("gender", "—")),
            ("توضیحات", item.get("notes") or "—"),
        ]

        scroll = ScrollView()

        inner = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4),
        )
        inner.bind(
            minimum_height=inner.setter("height")
        )

        for key, value in fields:
            lbl = make_label(
                fa(f"{key}: {value}"),
                size_hint_y=None,
                height=dp(38),
                halign="right",
                valign="middle",
                font_size="13sp",
            )
            lbl.bind(
                size=lambda inst, _: setattr(
                    inst,
                    "text_size",
                    inst.size,
                )
            )
            inner.add_widget(lbl)

        scroll.add_widget(inner)
        box.add_widget(scroll)

        close_btn = make_button(
            fa("بستن"),
            size_hint_y=None,
            height=dp(44),
        )
        box.add_widget(close_btn)

        popup = Popup(
            title=fa("جزئیات انتخاب"),
            title_font=PERSIAN_FONT_NAME,
            content=box,
            size_hint=(.86, .88),
        )

        close_btn.bind(
            on_release=popup.dismiss
        )
        popup.open()

    # -----------------------------------------------------
    # Generic alert
    # -----------------------------------------------------

    def alert(self, message: str):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8),
        )

        lbl = make_label(
            fa(message),
            halign="center",
            valign="middle",
        )
        lbl.bind(
            size=lambda inst, _: setattr(
                inst,
                "text_size",
                inst.size,
            )
        )

        btn = make_button(
            fa("باشه"),
            size_hint_y=None,
            height=dp(44),
        )

        box.add_widget(lbl)
        box.add_widget(btn)

        popup = Popup(
            title=fa("پیام"),
            title_font=PERSIAN_FONT_NAME,
            content=box,
            size_hint=(.68, .48),
        )

        btn.bind(on_release=popup.dismiss)
        popup.open()

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    def _pdf_font_path(self):
        # Prefer bundled font, then current UI/system font.
        bundled = resource_path("fonts/Vazirmatn-Regular.ttf")
        if bundled.exists():
            return str(bundled)

        return PERSIAN_FONT_PATH
    def save_pdf_to_android_downloads(self, source_path):
        """
        PDF ساخته‌شده را در Android 10+ داخل:
        Download/EntekhabReshteh/
        ذخیره می‌کند.
        """

        if platform != "android":
            return source_path

        try:
            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            MediaStore = autoclass(
                "android.provider.MediaStore"
            )
            ContentValues = autoclass(
                "android.content.ContentValues"
            )

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            filename = Path(source_path).name

            values = ContentValues()

            values.put(
                MediaStore.MediaColumns.DISPLAY_NAME,
                filename
            )

            values.put(
                MediaStore.MediaColumns.MIME_TYPE,
                "application/pdf"
            )

            values.put(
                MediaStore.MediaColumns.RELATIVE_PATH,
                "Download/EntekhabReshteh"
            )

            uri = resolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                values
            )

            if uri is None:
                raise Exception("امکان ایجاد فایل در Downloads وجود ندارد")

            output_stream = resolver.openOutputStream(uri)

            with open(source_path, "rb") as source_file:
                while True:
                    chunk = source_file.read(1024 * 64)

                    if not chunk:
                        break

                    output_stream.write(chunk)

            output_stream.flush()
            output_stream.close()

            return uri

        except Exception as e:
            raise Exception(
                f"خطا در ذخیره PDF در Downloads:\n{e}"
            )

    def export_pdf(self):
        rows = []

        # فقط انتخاب‌های پرشده
        for i, item in enumerate(self.choices):
            if item:
                row = dict(item)
                row["priority"] = i + 1
                rows.append(row)

        if not rows:
            self.alert("هیچ انتخابی برای خروجی PDF وجود ندارد")
            return

        # کتابخانه PDF
        try:
            from fpdf import FPDF
        except Exception:
            self.alert(
                "برای PDF باید پکیج fpdf2 نصب یا داخل APK قرار داده شود"
            )
            return

        # فونت فارسی
        font_path = self._pdf_font_path()

        if not font_path:
            self.alert("فونت فارسی مناسب برای PDF پیدا نشد")
            return

        # اسم فایل با تاریخ و ساعت
        filename = datetime.now().strftime(
            "entekhab_resht_%Y-%m-%d_%H-%M-%S.pdf"
        )

        # فایل اول داخل فضای داخلی برنامه ساخته می‌شود
        output_path = Path(self.user_data_dir) / filename

        try:
            pdf = FPDF(
                orientation="L",
                unit="mm",
                format="A4",
            )

            pdf.set_auto_page_break(
                auto=True,
                margin=7,
            )

            pdf.add_font(
                "Fa",
                fname=font_path,
            )

            pdf.add_page()

            # عنوان
            pdf.set_font("Fa", size=8)

            pdf.cell(
                0,
                7,
                fa("لیست انتخاب رشته"),
                align="C",
                new_x="LMARGIN",
                new_y="NEXT",
            )

            # ستون‌های جدول
            headers = [
                "اولویت",
                "کدرشته",
                "رشته",
                "دانشگاه",
                "استان",
                "دوره",
                "پذیرش",
                "نیمسال",
            ]

            widths = [
                13,
                22,
                48,
                68,
                35,
                25,
                28,
                25,
            ]

            pdf.set_font("Fa", size=5.5)

            # هدر جدول
            for header, width in zip(headers, widths):
                pdf.cell(
                    width,
                    7,
                    fa(header),
                    border=1,
                    align="C",
                )

            pdf.ln()

            # ردیف‌ها
            for row in rows:

                values = [
                    str(row["priority"]),
                    str(row.get("code", "")),
                    row.get("major", ""),
                    row.get("university", ""),
                    row.get("province", ""),
                    row.get("course", ""),
                    row.get("admission", ""),
                    row.get("semester", ""),
                ]

                for j, (value, width) in enumerate(
                    zip(values, widths)
                ):

                    if j < 2:
                        text = str(value)
                    else:
                        text = fa(str(value))

                    # جلوگیری از خیلی بلند شدن متن
                    if len(text) > 55:
                        text = text[:52] + "..."

                    pdf.cell(
                        width,
                        6.5,
                        text,
                        border=1,
                        align="C" if j < 2 else "R",
                    )

                pdf.ln()

            # ذخیره فایل موقت
            pdf.output(str(output_path))

        except Exception as exc:
            self.alert(
                f"خطا در ساخت PDF:\n{exc}"
            )
            return

        # -----------------------------
        # Android
        # -----------------------------
        if platform == "android":

            try:
                from jnius import autoclass

                PythonActivity = autoclass(
                    "org.kivy.android.PythonActivity"
                )

                MediaStore = autoclass(
                    "android.provider.MediaStore"
                )

                ContentValues = autoclass(
                    "android.content.ContentValues"
                )

                activity = PythonActivity.mActivity
                resolver = activity.getContentResolver()

                values = ContentValues()

                values.put(
                    MediaStore.MediaColumns.DISPLAY_NAME,
                    filename
                )

                values.put(
                    MediaStore.MediaColumns.MIME_TYPE,
                    "application/pdf"
                )

                values.put(
                    MediaStore.MediaColumns.RELATIVE_PATH,
                    "Download/EntekhabReshteh"
                )

                uri = resolver.insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                    values
                )

                if uri is None:
                    raise Exception(
                        "امکان ایجاد فایل در پوشه Downloads وجود ندارد"
                    )

                output_stream = resolver.openOutputStream(uri)

                with open(output_path, "rb") as source_file:

                    while True:
                        chunk = source_file.read(
                            1024 * 64
                        )

                        if not chunk:
                            break

                        output_stream.write(chunk)

                output_stream.flush()
                output_stream.close()

                self.set_status(
                    "PDF در پوشه Downloads ذخیره شد"
                )

                self.alert(
                    "PDF با موفقیت ذخیره شد\n\n"
                    "Download / EntekhabReshteh"
                )

            except Exception as exc:

                self.alert(
                    f"خطا در ذخیره PDF در Downloads:\n{exc}"
                )

        # -----------------------------
        # Windows / Desktop
        # -----------------------------
        else:

            self.set_status(
                f"PDF ساخته شد: {filename}"
            )

            self.alert(
                f"PDF ساخته شد:\n{output_path}"
            )

if __name__ == "__main__":
    EntekhabApp().run()

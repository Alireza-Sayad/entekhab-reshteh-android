import html
import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from kivy.config import Config
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
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import platform

APP_NAME = "EntekhabReshtehAndroid"
MAX_CHOICES = 150

# ------------------------------------------------------------
# Desktop phone preview
# ------------------------------------------------------------
# روی ویندوز برنامه با ابعاد نزدیک به اسکرین‌شات گوشی باز می‌شود.
# روی Android این بخش اثری ندارد.
if platform != "android":
    Window.size = (1280, 576)

Window.clearcolor = (0.96, 0.96, 0.96, 1)
Window.softinput_mode = "below_target"

BLUE = (0.16, 0.43, 0.78, 1)
RED = (0.76, 0.12, 0.12, 1)
TEXT = (0.10, 0.10, 0.10, 1)
MUTED = (0.40, 0.40, 0.40, 1)
WHITE = (1, 1, 1, 1)
POPUP_BG = (0.13, 0.13, 0.13, 1)


# ------------------------------------------------------------
# Paths / font
# ------------------------------------------------------------
def resource_path(name):
    return Path(__file__).resolve().parent / name


BUNDLED_FONT = resource_path("fonts/Vazirmatn-Regular.ttf")


def find_persian_font():
    """
    اولویت قطعی با فونت داخل خود پروژه است تا ظاهر ویندوز و Android یکی باشد.
    اگر فونت bundle نشده باشد، فقط برای جلوگیری از crash از فونت سیستم استفاده می‌کنیم.
    """
    candidates = [
        BUNDLED_FONT,
        resource_path("fonts/Vazirmatn.ttf"),
        resource_path("fonts/IRANSans.ttf"),
    ]

    if platform == "android":
        candidates += [
            Path("/system/fonts/NotoSansArabic-Regular.ttf"),
            Path("/system/fonts/NotoNaskhArabic-Regular.ttf"),
            Path("/system/fonts/NotoSansArabicUI-Regular.ttf"),
        ]
    else:
        candidates += [
            Path(r"C:\Windows\Fonts\tahoma.ttf"),
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
        ]

    for p in candidates:
        try:
            if Path(p).exists():
                return str(p)
        except Exception:
            pass
    return None


PERSIAN_FONT_PATH = find_persian_font()
APP_FONT = "Roboto"

if PERSIAN_FONT_PATH:
    try:
        LabelBase.register(name="PersianAppFont", fn_regular=PERSIAN_FONT_PATH)
        APP_FONT = "PersianAppFont"
    except Exception:
        pass


# ------------------------------------------------------------
# Persian / RTL helpers
# ------------------------------------------------------------
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


def _can_connect_left(ch):
    forms = _ARABIC_FORMS.get(ch)
    return bool(forms and forms[1])


def _can_connect_right(ch):
    forms = _ARABIC_FORMS.get(ch)
    return bool(forms and forms[2])


def _fallback_fa(text):
    text = str(text or "")
    chars = list(text)
    out = []

    for i, ch in enumerate(chars):
        forms = _ARABIC_FORMS.get(ch)
        if not forms:
            out.append(ch)
            continue

        prev = chars[i - 1] if i else ""
        nxt = chars[i + 1] if i + 1 < len(chars) else ""

        join_prev = _can_connect_right(ch) and _can_connect_left(prev)
        join_next = _can_connect_left(ch) and _can_connect_right(nxt)

        isolated, final, initial, medial = forms

        if join_prev and join_next and medial:
            out.append(medial)
        elif join_prev and final:
            out.append(final)
        elif join_next and initial:
            out.append(initial)
        else:
            out.append(isolated)

    visual = "".join(out)[::-1]
    visual = re.sub(
        r"[A-Za-z0-9۰-۹٠-٩._/+%-]+",
        lambda m: m.group(0)[::-1],
        visual,
    )
    visual = visual.translate(
        str.maketrans({
            "(": ")", ")": "(",
            "[": "]", "]": "[",
            "{": "}", "}": "{",
            "<": ">", ">": "<",
            "«": "»", "»": "«",
        })
    )
    return visual


def fa(text):
    """
    اگر arabic-reshaper/python-bidi موجود باشند از آن‌ها استفاده می‌کند.
    در غیر این صورت بدون crash از shaper داخلی استفاده می‌شود.
    """
    text = str(text or "")
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return _fallback_fa(text)


def normalize_digits(value):
    value = str(value or "")
    fa_digits = "۰۱۲۳۴۵۶۷۸۹"
    ar_digits = "٠١٢٣٤٥٦٧٨٩"
    en_digits = "0123456789"

    for a, b in zip(fa_digits, en_digits):
        value = value.replace(a, b)
    for a, b in zip(ar_digits, en_digits):
        value = value.replace(a, b)

    return value.strip()


def app_data_dir():
    app = App.get_running_app()
    p = Path(app.user_data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ------------------------------------------------------------
# UI widget helpers
# ------------------------------------------------------------
def label(text="", **kwargs):
    kwargs.setdefault("font_name", APP_FONT)
    kwargs.setdefault("color", TEXT)
    kwargs.setdefault("halign", "center")
    kwargs.setdefault("valign", "middle")
    w = Label(text=text, **kwargs)
    w.bind(size=lambda inst, _: setattr(inst, "text_size", inst.size))
    return w


def button(text="", **kwargs):
    kwargs.setdefault("font_name", APP_FONT)
    kwargs.setdefault("background_normal", "")
    kwargs.setdefault("background_color", BLUE)
    kwargs.setdefault("color", WHITE)
    return Button(text=text, **kwargs)


def text_input(**kwargs):
    kwargs.setdefault("font_name", APP_FONT)
    kwargs.setdefault("multiline", False)
    kwargs.setdefault("input_filter", "int")
    kwargs.setdefault("input_type", "number")
    kwargs.setdefault("halign", "center")
    kwargs.setdefault("font_size", "16sp")
    kwargs.setdefault("foreground_color", TEXT)
    kwargs.setdefault("background_color", WHITE)
    kwargs.setdefault("cursor_color", BLUE)
    return TextInput(**kwargs)


# ------------------------------------------------------------
# Database
# ------------------------------------------------------------
class MajorDatabase:
    def __init__(self):
        self.path = resource_path("majors.db")

    def get(self, code):
        if not self.path.exists():
            raise FileNotFoundError(f"majors.db پیدا نشد: {self.path}")

        with sqlite3.connect(str(self.path)) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                """
                SELECT
                    code, group_name, admission, course, major,
                    university, province, semester, gender, notes
                FROM majors
                WHERE code = ?
                """,
                (str(code),),
            ).fetchone()

        return dict(row) if row else None


# ------------------------------------------------------------
# RecycleView row
# ------------------------------------------------------------
class ChoiceRow(RecycleDataViewBehavior, BoxLayout):
    index = NumericProperty(0)
    priority = StringProperty("")
    code = StringProperty("")
    major = StringProperty("")
    university = StringProperty("")
    course = StringProperty("")
    item = None

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(4),
            padding=(dp(3), dp(2)),
            **kwargs,
        )

        self.delete_btn = button(
            text=fa("حذف"),
            size_hint_x=None,
            width=dp(58),
            font_size="11sp",
            background_color=RED,
        )
        self.delete_btn.bind(on_release=self._delete)
        self.add_widget(self.delete_btn)

        self.course_lbl = label(size_hint_x=.12, font_size="11sp")
        self.add_widget(self.course_lbl)

        self.univ_lbl = label(
            size_hint_x=.30,
            halign="right",
            font_size="11sp",
            shorten=True,
            shorten_from="left",
        )
        self.add_widget(self.univ_lbl)

        self.major_lbl = label(
            size_hint_x=.30,
            halign="right",
            font_size="11sp",
            shorten=True,
            shorten_from="left",
        )
        self.add_widget(self.major_lbl)

        self.code_lbl = label(size_hint_x=.15, font_size="11.5sp")
        self.add_widget(self.code_lbl)

        self.priority_lbl = label(size_hint_x=.10, font_size="11.5sp")
        self.add_widget(self.priority_lbl)

        for w in (
            self.course_lbl,
            self.univ_lbl,
            self.major_lbl,
            self.code_lbl,
            self.priority_lbl,
        ):
            w.bind(on_touch_down=self._details_touch)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.item = data.get("item")
        self.priority = data.get("priority", "")
        self.code = data.get("code", "")
        self.major = data.get("major", "")
        self.university = data.get("university", "")
        self.course = data.get("course", "")
        result = super().refresh_view_attrs(rv, index, data)
        self._sync()
        return result

    def refresh_view_layout(self, rv, index, layout, viewport):
        super().refresh_view_layout(rv, index, layout, viewport)
        self._sync()

    def _sync(self):
        self.priority_lbl.text = self.priority
        self.code_lbl.text = self.code
        self.major_lbl.text = fa(self.major) if self.major else ""
        self.univ_lbl.text = fa(self.university) if self.university else ""
        self.course_lbl.text = fa(self.course) if self.course else ""

        if self.item is None:
            # ردیف خالی واقعاً خالی باشد؛ بدون مربع، dash یا آیکن خراب.
            self.delete_btn.text = ""
            self.delete_btn.disabled = True
            self.delete_btn.opacity = 0.08
        else:
            self.delete_btn.text = fa("حذف")
            self.delete_btn.disabled = False
            self.delete_btn.opacity = 1

    def _delete(self, *_):
        if self.item:
            App.get_running_app().delete_choice(self.index)

    def _details_touch(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.item:
            App.get_running_app().show_details(self.item, self.index + 1)
            return True
        return False


class ChoicesRV(RecycleView):
    pass


# ------------------------------------------------------------
# Root UI
# ------------------------------------------------------------
class RootUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(4),
            padding=(dp(8), dp(6)),
            **kwargs,
        )

        # Top bar
        top = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(7))

        self.pdf_btn = button(
            text=fa("خروجی"),
            size_hint_x=.13,
            font_size="11.5sp",
        )
        self.pdf_btn.bind(on_release=lambda *_: App.get_running_app().export_html())
        top.add_widget(self.pdf_btn)

        self.add_btn = button(
            text=fa("ثبت"),
            size_hint_x=.14,
            font_size="15sp",
        )
        self.add_btn.bind(on_release=lambda *_: App.get_running_app().add_choice())
        top.add_widget(self.add_btn)

        self.priority_input = text_input(
            hint_text=fa("اولویت"),
            size_hint_x=.17,
        )
        self.priority_input.bind(on_text_validate=lambda *_: App.get_running_app().add_choice())
        top.add_widget(self.priority_input)

        self.code_input = text_input(
            hint_text=fa("کد رشته"),
            size_hint_x=.23,
        )
        self.code_input.bind(on_text_validate=lambda *_: App.get_running_app().add_choice())
        top.add_widget(self.code_input)

        title = label(
            text=fa("انتخاب رشته آفلاین"),
            size_hint_x=.33,
            halign="right",
            font_size="18sp",
        )
        top.add_widget(title)

        self.add_widget(top)

        # Header aligned exactly with row columns.
        header = BoxLayout(
            size_hint_y=None,
            height=dp(30),
            spacing=dp(4),
            padding=(dp(3), 0),
        )

        delete_header = label(
            text=fa("حذف"),
            size_hint_x=None,
            width=dp(58),
            font_size="11sp",
        )
        header.add_widget(delete_header)

        for text, sx in (
            ("دوره", .12),
            ("دانشگاه", .30),
            ("رشته", .30),
            ("کدرشته", .15),
            ("اولویت", .10),
        ):
            header.add_widget(
                label(
                    text=fa(text),
                    size_hint_x=sx,
                    font_size="11sp",
                )
            )

        self.add_widget(header)

        # Table
        self.rv = ChoicesRV()
        from kivy.uix.recycleboxlayout import RecycleBoxLayout

        layout = RecycleBoxLayout(
            default_size=(None, dp(50)),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation="vertical",
        )
        layout.bind(minimum_height=layout.setter("height"))
        self.rv.layout_manager = layout
        self.rv.viewclass = ChoiceRow
        self.rv.add_widget(layout)
        self.add_widget(self.rv)

        # Footer
        bottom = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))

        self.status = label(
            text=fa("آماده"),
            halign="right",
            font_size="11sp",
        )
        bottom.add_widget(self.status)

        # فقط ASCII؛ دیگر کاراکتر عجیب بین اعداد نداریم.
        self.count = label(
            text="0 / 150",
            size_hint_x=.16,
            font_size="11sp",
        )
        bottom.add_widget(self.count)

        self.add_widget(bottom)


# ------------------------------------------------------------
# Main App
# ------------------------------------------------------------
class EntekhabApp(App):
    title = "Entekhab Reshteh"

    def build(self):
        self.db = MajorDatabase()
        if platform == "android":
            try:
                Window.softinput_mode = "resize"
            except Exception:
                pass
        self.choices = [None] * MAX_CHOICES
        self.root_ui = RootUI()
        self.load_choices()
        Clock.schedule_once(lambda *_: self.refresh(), 0)
        return self.root_ui

    @property
    def save_path(self):
        return app_data_dir() / "choices.json"

    def load_choices(self):
        try:
            if self.save_path.exists():
                raw = json.loads(self.save_path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    self.choices = (raw + [None] * MAX_CHOICES)[:MAX_CHOICES]
        except Exception:
            self.choices = [None] * MAX_CHOICES

    def save_choices(self):
        self.save_path.write_text(
            json.dumps(self.choices, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_status(self, text):
        self.root_ui.status.text = fa(text)

    def add_choice(self):
        code = normalize_digits(self.root_ui.code_input.text)
        p = normalize_digits(self.root_ui.priority_input.text)

        if not code or not p.isdigit():
            self.alert("کد رشته و اولویت را وارد کنید")
            return

        priority = int(p)
        if not 1 <= priority <= MAX_CHOICES:
            self.alert("اولویت باید بین 1 تا 150 باشد")
            return

        try:
            item = self.db.get(code)
        except Exception as exc:
            self.alert(f"خطا در دیتابیس: {exc}")
            return

        if not item:
            self.alert(f"کدرشته {code} پیدا نشد")
            return

        # Duplicate code: remove old occurrence first.
        for i, old in enumerate(self.choices):
            if old and str(old.get("code")) == code:
                self.choices[i] = None

        idx = priority - 1

        if self.choices[idx] is None:
            self.choices[idx] = item
        else:
            carry = item
            for i in range(idx, MAX_CHOICES):
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

        self.refresh(scroll_to=idx)

    def delete_choice(self, index):
        if 0 <= index < MAX_CHOICES and self.choices[index] is not None:
            self.choices[index] = None
            self.save_choices()
            self.set_status(f"اولویت {index + 1} حذف شد")
            self.refresh()

    def refresh(self, scroll_to=None):
        data = []
        count = 0

        for i in range(MAX_CHOICES):
            item = self.choices[i]

            if item:
                count += 1
                data.append({
                    "priority": str(i + 1),
                    "code": str(item.get("code", "")),
                    "major": item.get("major", ""),
                    "university": item.get("university", ""),
                    "course": item.get("course", ""),
                    "item": item,
                })
            else:
                # ردیف خالی: فقط شماره اولویت نمایش داده شود.
                data.append({
                    "priority": str(i + 1),
                    "code": "",
                    "major": "",
                    "university": "",
                    "course": "",
                    "item": None,
                })

        self.root_ui.rv.data = data
        self.root_ui.count.text = f"{count} / {MAX_CHOICES}"

        if scroll_to is not None:
            self.root_ui.rv.scroll_y = max(
                0,
                min(1, 1 - (scroll_to / max(1, MAX_CHOICES - 1))),
            )

    # --------------------------------------------------------
    # Popups
    # --------------------------------------------------------
    def _make_popup(self, title, content, size_hint):
        return Popup(
            title=fa(title),
            title_font=APP_FONT,
            title_size="15sp",
            content=content,
            size_hint=size_hint,
            background_color=POPUP_BG,
            separator_color=(0.18, 0.72, 0.90, 1),
        )

    def show_details(self, item, priority):
        # فاصله افقی بیشتر تا متن به لبه‌های Popup نچسبد.
        box = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(14), dp(28), dp(16)],
            spacing=dp(10),
        )

        scroll = ScrollView()
        inner = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
            padding=[dp(8), dp(4), dp(8), dp(4)],
        )
        inner.bind(minimum_height=inner.setter("height"))

        fields = [
            ("اولویت", priority),
            ("کدرشته", item.get("code")),
            ("رشته", item.get("major")),
            ("دانشگاه", item.get("university")),
            ("استان", item.get("province")),
            ("دوره", item.get("course")),
            ("پذیرش", item.get("admission")),
            ("نیمسال", item.get("semester")),
            ("جنسیت", item.get("gender")),
            ("توضیحات", item.get("notes") or "-"),
        ]

        for k, v in fields:
            lbl = label(
                text=fa(f"{k}: {v}"),
                size_hint_y=None,
                height=dp(38),
                halign="right",
                valign="middle",
                font_size="11.5sp",
                # Popup تیره است؛ متن را کاملاً روشن می‌کنیم.
                color=(1, 1, 1, 1),
                padding=(dp(18), dp(2)),
            )
            inner.add_widget(lbl)

        scroll.add_widget(inner)
        box.add_widget(scroll)

        close_btn = button(
            text=fa("بستن"),
            size_hint_y=None,
            height=dp(44),
            font_size="11sp",
        )
        box.add_widget(close_btn)

        pop = self._make_popup(
            "جزئیات انتخاب",
            box,
            (.82, .84),
        )
        close_btn.bind(on_release=pop.dismiss)
        pop.open()

    def alert(self, message):
        box = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(18), dp(24), dp(18)],
            spacing=dp(12),
        )

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
        )

        lbl = label(
            text=fa(message),
            size_hint_y=None,
            halign="right",
            valign="top",
            font_size="14sp",
            color=(1, 1, 1, 1),
            padding=(dp(16), dp(10)),
        )

        def _update_height(inst, _):
            inst.text_size = (max(dp(100), inst.width - dp(24)), None)
            inst.texture_update()
            inst.height = max(dp(90), inst.texture_size[1] + dp(30))

        lbl.bind(width=_update_height)
        _update_height(lbl, None)

        scroll.add_widget(lbl)

        ok_btn = button(
            text=fa("باشه"),
            size_hint_y=None,
            height=dp(48),
            font_size="14sp",
        )

        box.add_widget(scroll)
        box.add_widget(ok_btn)

        pop = self._make_popup(
            "پیام",
            box,
            (.84, .72),
        )

        ok_btn.bind(on_release=pop.dismiss)
        pop.open()

    # --------------------------------------------------------
    # HTML export
    # --------------------------------------------------------
    def _desktop_export_dir(self):
        downloads = Path.home() / "Downloads"
        if not downloads.exists():
            downloads = app_data_dir()

        target = downloads / "EntekhabReshteh"
        target.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def _html_cell(value):
        return html.escape(str(value or ""), quote=True)

    def _build_export_html(self, rows):
        body_rows = []

        for row in rows:
            cells = [
                row["priority"],
                row.get("code", ""),
                row.get("major", ""),
                row.get("university", ""),
                row.get("province", ""),
                row.get("course", ""),
                row.get("admission", ""),
                row.get("semester", ""),
                row.get("gender", ""),
                row.get("notes", ""),
            ]

            body_rows.append(
                "<tr>" +
                "".join(
                    f"<td>{self._html_cell(value)}</td>"
                    for value in cells
                ) +
                "</tr>"
            )

        generated_at = datetime.now().strftime("%Y/%m/%d - %H:%M")

        return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>لیست انتخاب رشته</title>
<style>
    @page {{
        size: A4 landscape;
        margin: 10mm;
    }}

    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
        color: #111111;
        direction: rtl;
        font-family: Tahoma, Arial, "Noto Sans Arabic", sans-serif;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    body {{
        padding: 14px;
    }}

    .page {{
        width: 100%;
        max-width: 1120px;
        margin: 0 auto;
    }}

    h1 {{
        margin: 0 0 14px;
        text-align: center;
        font-size: 20px;
        font-weight: 700;
    }}

    .meta {{
        margin: 0 0 10px;
        text-align: center;
        color: #555;
        font-size: 11px;
    }}

    table {{
        width: 100%;
        margin: 0 auto;
        border-collapse: collapse;
        table-layout: fixed;
        direction: rtl;
        font-size: 10px;
    }}

    th, td {{
        border: 1px solid #b9b9b9;
        padding: 6px 5px;
        vertical-align: middle;
        text-align: right;
        line-height: 1.65;
        overflow-wrap: anywhere;
    }}

    th {{
        background: #ebebeb;
        text-align: center;
        font-weight: 700;
        white-space: nowrap;
    }}

    td:nth-child(1),
    td:nth-child(2) {{
        text-align: center;
        direction: ltr;
    }}

    th:nth-child(1) {{ width: 5%; }}
    th:nth-child(2) {{ width: 8%; }}
    th:nth-child(3) {{ width: 15%; }}
    th:nth-child(4) {{ width: 20%; }}
    th:nth-child(5) {{ width: 10%; }}
    th:nth-child(6) {{ width: 7%; }}
    th:nth-child(7) {{ width: 9%; }}
    th:nth-child(8) {{ width: 8%; }}
    th:nth-child(9) {{ width: 7%; }}
    th:nth-child(10) {{ width: 11%; }}

    @media print {{
        body {{
            padding: 0;
        }}

        .page {{
            max-width: none;
        }}

        thead {{
            display: table-header-group;
        }}

        tr {{
            break-inside: avoid;
            page-break-inside: avoid;
        }}
    }}
</style>
</head>
<body>
<div class="page">
    <h1>لیست انتخاب رشته</h1>
    <div class="meta">تعداد انتخاب‌ها: {len(rows)} &nbsp; | &nbsp; زمان خروجی: {generated_at}</div>

    <table>
        <thead>
            <tr>
                <th>اولویت</th>
                <th>کدرشته</th>
                <th>رشته</th>
                <th>دانشگاه</th>
                <th>استان</th>
                <th>دوره</th>
                <th>پذیرش</th>
                <th>نیمسال</th>
                <th>جنسیت</th>
                <th>توضیحات</th>
            </tr>
        </thead>
        <tbody>
            {''.join(body_rows)}
        </tbody>
    </table>
</div>
</body>
</html>
"""

    def export_html(self):
        rows = []

        for i, item in enumerate(self.choices):
            if item:
                row = dict(item)
                row["priority"] = i + 1
                rows.append(row)

        if not rows:
            self.alert("هیچ انتخابی برای خروجی وجود ندارد")
            return

        filename = datetime.now().strftime(
            "entekhab_resht_%Y-%m-%d_%H-%M-%S.html"
        )

        try:
            html_text = self._build_export_html(rows)
            temp_path = app_data_dir() / filename
            temp_path.write_text(html_text, encoding="utf-8")
        except Exception as exc:
            self.alert(f"خطا در ساخت خروجی: {exc}")
            return

        if platform == "android":
            self._save_html_android_downloads(temp_path, filename)
        else:
            final_path = self._desktop_export_dir() / filename

            try:
                final_path.write_text(html_text, encoding="utf-8")
            except Exception as exc:
                self.alert(f"خروجی ساخته شد ولی ذخیره نشد: {exc}")
                return

            self.set_status(f"خروجی ساخته شد: {filename}")

            # روی ویندوز مستقیم در مرورگر باز می‌شود تا همان خروجی Android را ببینی.
            try:
                import webbrowser
                webbrowser.open(final_path.as_uri())
            except Exception:
                pass

            self.alert(
                "خروجی HTML ساخته شد\n"
                f"{final_path}\n\n"
                "برای PDF در مرورگر Print / چاپ را بزن و Save as PDF را انتخاب کن."
            )

    def _save_html_android_downloads(self, source_path, filename):
        """
        Android 10+:
        ذخیره HTML در Download/EntekhabReshteh با MediaStore.
        سپس تلاش برای باز کردن با مرورگر/فایل منیجر.
        """
        try:
            from jnius import autoclass, cast

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            MediaStore = autoclass("android.provider.MediaStore")
            ContentValues = autoclass("android.content.ContentValues")
            Intent = autoclass("android.content.Intent")
            Build = autoclass("android.os.Build")

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()

            values = ContentValues()
            values.put("_display_name", filename)
            values.put("mime_type", "text/html")

            # Android 10+
            if Build.VERSION.SDK_INT >= 29:
                values.put("relative_path", "Download/EntekhabReshteh")
                values.put("is_pending", 1)

            uri = resolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                values
            )

            if uri is None:
                raise RuntimeError("MediaStore فایل خروجی را ایجاد نکرد")

            stream = resolver.openOutputStream(uri)
            if stream is None:
                raise RuntimeError("امکان نوشتن فایل خروجی وجود ندارد")

            try:
                with open(source_path, "rb") as src:
                    while True:
                        chunk = src.read(65536)
                        if not chunk:
                            break
                        stream.write(chunk)
                stream.flush()
            finally:
                stream.close()

            if Build.VERSION.SDK_INT >= 29:
                done = ContentValues()
                done.put("is_pending", 0)
                resolver.update(uri, done, None, None)

            self.set_status("خروجی در Downloads ذخیره شد")

            # Try open with browser/file viewer
            try:
                view_intent = Intent(Intent.ACTION_VIEW)
                view_intent.setDataAndType(uri, "text/html")
                view_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                chooser = Intent.createChooser(
                    view_intent,
                    fa("باز کردن خروجی با")
                )
                activity.startActivity(chooser)

                self.alert(
                    "خروجی HTML با موفقیت ذخیره شد.\n\n"
                    "مسیر:\nDownload / EntekhabReshteh\n\n"
                    "مرورگر را انتخاب کن و برای PDF از Print / چاپ → Save as PDF استفاده کن."
                )
                return

            except Exception as first_exc:
                # Share fallback
                try:
                    send_intent = Intent(Intent.ACTION_SEND)
                    send_intent.setType("text/html")
                    send_intent.putExtra(
                        Intent.EXTRA_STREAM,
                        cast("android.os.Parcelable", uri)
                    )
                    send_intent.addFlags(
                        Intent.FLAG_GRANT_READ_URI_PERMISSION
                    )
                    chooser = Intent.createChooser(
                        send_intent,
                        fa("باز کردن یا اشتراک خروجی")
                    )
                    activity.startActivity(chooser)

                    self.alert(
                        "خروجی HTML ذخیره شد.\n\n"
                        "مسیر:\nDownload / EntekhabReshteh\n\n"
                        "از پنجره بازشده مرورگر یا فایل‌منیجر را انتخاب کن."
                    )
                    return
                except Exception as second_exc:
                    self.alert(
                        "خروجی HTML ذخیره شد اما باز کردن خودکار انجام نشد.\n\n"
                        "مسیر:\nDownload / EntekhabReshteh\n\n"
                        "فایل را از File Manager باز کن.\n\n"
                        f"خطای باز کردن:\n{first_exc}\n{second_exc}"
                    )
                    return

        except Exception as exc:
            self.alert(
                "خطا در ذخیره خروجی:\n\n"
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    EntekhabApp().run()

import sys
import subprocess
import json
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QLineEdit, QStackedWidget, QGridLayout,
    QGraphicsDropShadowEffect, QComboBox, QScrollArea, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPixmap

BG_COLOR = "#050505"
CARD_BG = "#0a0a0a"
BORDER_COLOR = "#1a1a1a"
ACCENT_COLOR = "#ffffff"
SECONDARY_TEXT = "#666666"

def apply_glow(widget, color="#ffffff", strength=15):
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(strength)
    glow.setColor(QColor(color))
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)

class ModeCard(QFrame):
    def __init__(self, title, icon_text, mode_id, callback):
        super().__init__()
        self.mode_id = mode_id
        self.callback = callback
        self.setFixedSize(155, 115)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        self.icon_label = QLabel(icon_text)
        self.icon_label.setStyleSheet("font-size: 24px; color: white; background: transparent; border: none;")
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; font-weight: 800; color: white; background: transparent; border: none;")
        self.sub_label = QLabel("Click to activate")
        self.sub_label.setStyleSheet("font-size: 8px; color: #666666; background: transparent; border: none;")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.sub_label)
        self.set_active(False)

    def set_active(self, is_active):
        border = "white" if is_active else "#1a1a1a"
        bg = "#111111" if is_active else "#0a0a0a"
        self.setStyleSheet(f"ModeCard {{ background: {bg}; border: 1px solid {border}; border-radius: 12px; }}")
        if is_active:
            apply_glow(self, "#ffffff", 15)
        else:
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        self.callback(self.mode_id)

class KXRMacroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KXR MACRO • PREMIUM")
        self.setFixedSize(800, 650)
        self.setStyleSheet(f"background-color: {BG_COLOR}; color: white; font-family: 'Segoe UI Variable', sans-serif;")

        self.active_mode = "drag"
        self.inputs = {}
        self.proc = None
        self.ahk_file = "macro.ahk"
        self.AHK = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"

        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(30, 20, 30, 20)

        self.setup_nav_bar()

        self.header_lay = QHBoxLayout()
        self.main_title = QLabel("System Control")
        self.main_title.setStyleSheet("font-size: 24px; font-weight: 800; margin: 10px 0;")
        self.header_lay.addWidget(self.main_title)
        self.header_lay.addStretch()

        self.status_ind = QLabel("● INACTIVE")
        self.status_ind.setStyleSheet("background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 8px; padding: 6px 15px; font-size: 10px; font-weight: bold; color: #555;")
        self.header_lay.addWidget(self.status_ind)
        self.main_layout.addLayout(self.header_lay)

        self.card_container = QWidget()
        card_lay = QHBoxLayout(self.card_container)
        card_lay.setContentsMargins(0, 0, 0, 10)
        modes = [("Drag Macro", "🔍", "drag"), ("Double Edit", "⚡", "double"), ("Auto Pick", "📦", "auto"), ("Build Mode", "⬢", "build")]
        self.cards = {}
        for t, ic, mid in modes:
            card = ModeCard(t, ic, mid, self.switch_mode)
            card_lay.addWidget(card)
            self.cards[mid] = card
        self.main_layout.addWidget(self.card_container)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.setup_dashboard_page()
        self.setup_settings_page()
        self.setup_about_page()

        self.setup_bottom_bar()
        self.switch_page(0)
        self.switch_mode("drag")

    def setup_nav_bar(self):
        nav = QHBoxLayout()
        self.nav_btns = []
        menu = [("DASHBOARD", 0), ("SETTINGS", 1), ("ABOUT", 2)]
        for name, idx in menu:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, i=idx: self.switch_page(i))
            nav.addWidget(btn)
            self.nav_btns.append(btn)
        nav.addStretch()
        self.main_layout.addLayout(nav)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.card_container.setVisible(index == 0)
        for i, btn in enumerate(self.nav_btns):
            color = "white" if i == index else "#666"
            border = "2px solid white" if i == index else "none"
            btn.setStyleSheet(f"border: none; border-bottom: {border}; color: {color}; font-size: 11px; font-weight: bold; padding: 10px 20px;")

    def setup_dashboard_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)

        info_lay = QHBoxLayout()
        self.info_boxes = {}
        for label in ["ACTIVE MODE", "TRIGGER", "LATENCY"]:
            box = QFrame()
            box.setStyleSheet("background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; padding: 15px;")
            v = QVBoxLayout(box)
            top_label = QLabel(label)
            top_label.setStyleSheet("color: #444; font-size: 9px; font-weight: bold;")
            v.addWidget(top_label)
            val = QLabel("None")
            val.setStyleSheet("font-size: 16px; font-weight: 800;")
            v.addWidget(val)
            info_lay.addWidget(box)
            self.info_boxes[label] = val
        lay.addLayout(info_lay)

        self.quick_frame = QFrame()
        self.quick_frame.setStyleSheet("background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; margin-top: 15px;")
        qlay = QVBoxLayout(self.quick_frame)
        self.quick_content = QGridLayout()
        quick_title = QLabel("⚡ Quick Actions")
        quick_title.setStyleSheet("font-weight: bold; color: #888; border: none;")
        qlay.addWidget(quick_title)
        qlay.addLayout(self.quick_content)
        lay.addWidget(self.quick_frame)
        lay.addStretch()
        self.stack.addWidget(page)

    def setup_settings_page(self):
        page = QWidget()
        main_lay = QHBoxLayout(page)
        main_lay.setContentsMargins(0, 10, 0, 0)

        self.settings_menu = QListWidget()
        self.settings_menu.setFixedWidth(180)
        self.settings_menu.setStyleSheet("""
            QListWidget {
                background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px;
                padding: 10px; outline: none;
            }
            QListWidget::item {
                padding: 12px; color: #666; font-weight: bold; border-radius: 8px; margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background: #111; color: white; border: 1px solid #333;
            }
        """)

        self.settings_stack = QStackedWidget()
        self.settings_stack.setStyleSheet("background: #0a0a0a; border: 1px solid #1a1a1a; border-radius: 12px; padding: 20px;")

        self.create_settings_subpage("Drag Macro", ["Edit Key", "Hold Key", "Delay (ms)", "Smoothing"])
        self.create_settings_subpage("Double Edit", ["Macro Key", "First Key", "Second Key"])
        self.create_settings_subpage("Auto Pick", ["Pickup Key", "Trigger Button", "CPS Limit"])
        self.create_settings_subpage("General", ["Auto-start", "Hide to tray", "Resolution"])

        self.settings_menu.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        self.settings_menu.setCurrentRow(0)

        main_lay.addWidget(self.settings_menu)
        main_lay.addWidget(self.settings_stack)
        self.stack.addWidget(page)

    def create_settings_subpage(self, name, fields):
        item = QListWidgetItem(name)
        self.settings_menu.addItem(item)

        sub_page = QWidget()
        lay = QVBoxLayout(sub_page)

        title = QLabel(f"{name.upper()} CONFIGURATION")
        title.setStyleSheet("font-weight: 900; color: #444; font-size: 11px; letter-spacing: 1px; margin-bottom: 10px;")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(15)

        self.inputs[name] = {}

        for i, f in enumerate(fields):
            v = QVBoxLayout()

            label = QLabel(f)
            label.setStyleSheet("color: #666; font-size: 10px; font-weight: bold;")
            v.addWidget(label)

            inp = QLineEdit()
            inp.setPlaceholderText("Default")
            inp.setStyleSheet("background: #050505; border: 1px solid #222; border-radius: 6px; padding: 10px; color: white;")
            v.addWidget(inp)

            self.inputs[name][f] = inp
            grid.addLayout(v, i // 2, i % 2)

        lay.addLayout(grid)
        lay.addStretch()
        self.settings_stack.addWidget(sub_page)

    def setup_about_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capy = QLabel()
        pix = QPixmap("image_ac2683.jpg")
        if not pix.isNull():
            capy.setPixmap(pix.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lay.addWidget(capy)
        title = QLabel("KXR MACRO • V4.2 PREMIUM")
        title.setStyleSheet("font-weight: 900; margin-top: 15px; letter-spacing: 2px;")
        lay.addWidget(title)
        self.stack.addWidget(page)

    def switch_mode(self, mode_id):
        self.active_mode = mode_id
        for mid, card in self.cards.items():
            card.set_active(mid == mode_id)

        self.info_boxes["ACTIVE MODE"].setText(mode_id.capitalize())

        if mode_id == "drag":
            self.info_boxes["TRIGGER"].setText("Q")
            self.info_boxes["LATENCY"].setText(self.get_drag_delay())
        elif mode_id == "auto":
            self.info_boxes["TRIGGER"].setText(self.get_auto_trigger())
            self.info_boxes["LATENCY"].setText(self.get_auto_delay())
        elif mode_id == "double":
            self.info_boxes["TRIGGER"].setText(self.get_double_macro_key())
            self.info_boxes["LATENCY"].setText("None")
        else:
            self.info_boxes["TRIGGER"].setText("V")
            self.info_boxes["LATENCY"].setText("None")

        while self.quick_content.count():
            item = self.quick_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

        if mode_id == "build":
            label = QLabel("COMING SOON...")
            label.setStyleSheet("font-weight: bold; color: #333;")
            self.quick_content.addWidget(label, 0, 0)
        elif mode_id == "drag":
            self.add_quick_field("Quick Bind", self.get_drag_edit_key(), 0, 0)
            self.add_quick_field("Speed", self.get_drag_delay(), 0, 1)
        elif mode_id == "auto":
            self.add_quick_field("Pickup", self.get_auto_pickup_key(), 0, 0)
            self.add_quick_field("Speed", self.get_auto_delay(), 0, 1)
        elif mode_id == "double":
            self.add_quick_field("Macro Key", self.get_double_macro_key(), 0, 0)
            self.add_quick_field("First Key", self.get_double_first_key(), 0, 1)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def add_quick_field(self, title, value, row, col):
        v = QVBoxLayout()

        top = QLabel(title)
        top.setStyleSheet("font-size: 9px; color: #555;")
        v.addWidget(top)

        inp = QLineEdit("Default")
        inp.setStyleSheet("background: transparent; border: none; font-weight: bold; font-size: 14px;")
        inp.setText(value if value else "Default")
        v.addWidget(inp)

        self.quick_content.addLayout(v, row, col)

    def setup_bottom_bar(self):
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 10, 0, 0)

        footer = QLabel("F2 Emergency Exit  •  Stable Build")
        footer.setStyleSheet("color: #444; font-size: 10px; font-weight: bold;")
        bottom.addWidget(footer)
        bottom.addStretch()

        self.start_btn = QPushButton("LAUNCH MACRO")
        self.start_btn.setFixedSize(160, 45)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: white; color: black; font-weight: 900;
                border-radius: 8px; font-size: 11px; letter-spacing: 1px;
            }
            QPushButton:hover { background: #dddddd; }
        """)
        apply_glow(self.start_btn, "#ffffff", 15)
        self.start_btn.clicked.connect(self.start_macro)

        bottom.addWidget(self.start_btn)
        self.main_layout.addLayout(bottom)

    def get_input_text(self, section, field, fallback):
        if section in self.inputs and field in self.inputs[section]:
            value = self.inputs[section][field].text().strip()
            if value:
                return value
        return fallback

    def get_drag_edit_key(self):
        return self.get_input_text("Drag Macro", "Edit Key", "q").lower()

    def get_drag_hold_key(self):
        return self.get_input_text("Drag Macro", "Hold Key", "p").lower()

    def get_drag_delay(self):
        return self.get_input_text("Drag Macro", "Delay (ms)", "15")

    def get_drag_smoothing(self):
        return self.get_input_text("Drag Macro", "Smoothing", "Default")

    def get_double_macro_key(self):
        return self.get_input_text("Double Edit", "Macro Key", "q").lower()

    def get_double_first_key(self):
        return self.get_input_text("Double Edit", "First Key", "q").lower()

    def get_double_second_key(self):
        return self.get_input_text("Double Edit", "Second Key", "p").lower()

    def get_auto_pickup_key(self):
        return self.get_input_text("Auto Pick", "Pickup Key", "e").lower()

    def get_auto_trigger(self):
        return self.get_input_text("Auto Pick", "Trigger Button", "xbutton1").lower()

    def get_auto_delay(self):
        return self.get_input_text("Auto Pick", "CPS Limit", "50")

    def escape_ahk_key(self, key):
        key = key.strip()
        return key.replace('"', '""')

    def normalize_delay(self, value, fallback):
        try:
            n = int(str(value).strip())
            if n < 0:
                return str(fallback)
            return str(n)
        except:
            return str(fallback)

    def drag_script(self):
        edit = self.escape_ahk_key(self.get_drag_edit_key())
        hold = self.escape_ahk_key(self.get_drag_hold_key())
        delay = self.normalize_delay(self.get_drag_delay(), 15)

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${edit}:: {{
    if (!enabled)
        return

    SendEvent("{{{edit} down}}")
    Sleep({delay})
    SendEvent("{{{edit} up}}")

    Sleep({delay})

    SendEvent("{{{hold} down}}")
    KeyWait "{edit}"
    SendEvent("{{{hold} up}}")

    Sleep({delay})

    SendEvent("{{{edit} down}}")
    Sleep({delay})
    SendEvent("{{{edit} up}}")
}}

End::ExitApp
"""

    def double_script(self):
        macro_key = self.escape_ahk_key(self.get_double_macro_key())
        first_key = self.escape_ahk_key(self.get_double_first_key())
        second_key = self.escape_ahk_key(self.get_double_second_key())

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${macro_key}:: {{
    if (!enabled)
        return

    SendEvent("{{{first_key} down}}")
    Sleep(15)
    SendEvent("{{{first_key} up}}")

    Sleep(15)

    SendEvent("{{{second_key} down}}")
    Sleep(15)
    SendEvent("{{{second_key} up}}")
}}

End::ExitApp
"""

    def auto_script(self):
        pickup = self.escape_ahk_key(self.get_auto_pickup_key())
        trigger = self.escape_ahk_key(self.get_auto_trigger())
        delay = self.normalize_delay(self.get_auto_delay(), 50)

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${trigger}:: {{
    while GetKeyState("{trigger}", "P") {{
        if (!enabled)
            break
        SendEvent("{{{pickup}}}")
        Sleep({delay})
    }}
}}

End::ExitApp
"""

    def build_script(self):
        return """#Requires AutoHotkey v2.0
#SingleInstance Force
End::ExitApp
"""

    def start_macro(self):
        self.stop_macro()

        if self.active_mode == "drag":
            code = self.drag_script()
        elif self.active_mode == "auto":
            code = self.auto_script()
        elif self.active_mode == "double":
            code = self.double_script()
        else:
            code = self.build_script()

        with open(self.ahk_file, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            self.proc = subprocess.Popen([self.AHK, self.ahk_file])
            self.status_ind.setText("● ACTIVE")
            self.status_ind.setStyleSheet("""
                background: #0d0d0d;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 6px 15px;
                font-size: 10px;
                font-weight: bold;
                color: #22c55e;
            """)
        except:
            self.proc = None
            self.status_ind.setText("● ERROR")
            self.status_ind.setStyleSheet("""
                background: #0d0d0d;
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 6px 15px;
                font-size: 10px;
                font-weight: bold;
                color: #ef4444;
            """)

    def stop_macro(self):
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass
            self.proc = None

        self.status_ind.setText("● INACTIVE")
        self.status_ind.setStyleSheet("""
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 8px;
            padding: 6px 15px;
            font-size: 10px;
            font-weight: bold;
            color: #555;
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KXRMacroApp()
    window.show()
    sys.exit(app.exec())

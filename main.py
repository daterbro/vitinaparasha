import sys
import os
import subprocess

from modules import *
from widgets import *

os.environ["QT_FONT_DPI"] = "96"

widgets = None


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        global widgets
        widgets = self.ui

        Settings.ENABLE_CUSTOM_TITLE_BAR = True

        title = "PyDracula Macro"
        description = "Drag Macro and AutoPick"
        self.setWindowTitle(title)
        widgets.titleRightInfo.setText(description)

        widgets.toggleButton.clicked.connect(lambda: UIFunctions.toggleMenu(self, True))
        UIFunctions.uiDefinitions(self)

        widgets.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        widgets.btn_home.clicked.connect(self.buttonClick)
        widgets.btn_widgets.clicked.connect(self.buttonClick)
        widgets.btn_new.clicked.connect(self.buttonClick)
        widgets.btn_save.clicked.connect(self.start_macro)

        def openCloseLeftBox():
            UIFunctions.toggleLeftBox(self, True)

        widgets.toggleLeftBox.clicked.connect(openCloseLeftBox)
        widgets.extraCloseColumnBtn.clicked.connect(openCloseLeftBox)

        def openCloseRightBox():
            UIFunctions.toggleRightBox(self, True)

        widgets.settingsTopBtn.clicked.connect(openCloseRightBox)

        self.proc = None
        self.ahk_file = "macro.ahk"
        self.AHK = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
        self.active_tab = "drag"

        self.build_home_page()
        self.build_drag_page()
        self.build_auto_page()

        self.show()

        useCustomTheme = False
        themeFile = "themes\\py_dracula_light.qss"

        if useCustomTheme:
            UIFunctions.theme(self, themeFile, True)
            AppFunctions.setThemeHack(self)

        widgets.stackedWidget.setCurrentWidget(widgets.home)
        widgets.btn_home.setStyleSheet(UIFunctions.selectMenu(widgets.btn_home.styleSheet()))

    def clear_page(self, page):
        old_layout = page.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                child_layout = item.layout()
                if widget is not None:
                    widget.deleteLater()
                if child_layout is not None:
                    self.clear_layout(child_layout)
            old_layout.deleteLater()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            if child_layout is not None:
                self.clear_layout(child_layout)

    def make_input(self, title, default):
        block = QFrame()
        block.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.03);
                border-radius: 10px;
            }
        "")

        layout = QVBoxLayout(block)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setStyleSheet("font-size: 12px; color: rgb(170, 170, 170);")

        entry = QLineEdit()
        entry.setText(default)
        entry.setMinimumHeight(40)

        layout.addWidget(label)
        layout.addWidget(entry)

        return block, entry

    def build_home_page(self):
        self.clear_page(widgets.home)

        layout = QVBoxLayout(widgets.home)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Macro Control")
        title.setStyleSheet("font-size: 28px; font-weight: 700;")

        subtitle = QLabel("F1 — enable / disable | End — exit macro")
        subtitle.setStyleSheet("font-size: 13px; color: rgb(170,170,170);")

        status_card = QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.04);
                border-radius: 16px;
            }
        "")

        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 20, 20, 20)
        status_layout.setSpacing(10)

        self.status_title = QLabel("Status")
        self.status_title.setStyleSheet("font-size: 14px; color: rgb(170,170,170);")

        self.status_value = QLabel("disabled")
        self.status_value.setStyleSheet("font-size: 24px; font-weight: 700; color: rgb(170,170,170);")

        self.mode_value = QLabel("Current mode: Drag Macro")
        self.mode_value.setStyleSheet("font-size: 14px; color: rgb(170,170,170);")

        self.ahk_path_label = QLabel(f"AHK: {self.AHK}")
        self.ahk_path_label.setWordWrap(True)
        self.ahk_path_label.setStyleSheet("font-size: 12px; color: rgb(130,130,130);")

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(12)

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")

        self.start_btn.setMinimumHeight(42)
        self.stop_btn.setMinimumHeight(42)

        self.start_btn.clicked.connect(self.start_macro)
        self.stop_btn.clicked.connect(self.stop_macro)

        buttons_row.addWidget(self.start_btn)
        buttons_row.addWidget(self.stop_btn)

        status_layout.addWidget(self.status_title)
        status_layout.addWidget(self.status_value)
        status_layout.addWidget(self.mode_value)
        status_layout.addWidget(self.ahk_path_label)
        status_layout.addLayout(buttons_row)

        info = QLabel("Open Drag Macro or AutoPick from the left menu, edit keys and delay, then press Start.")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; color: rgb(170,170,170);")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(status_card)
        layout.addWidget(info)
        layout.addStretch()

    def build_drag_page(self):
        self.clear_page(widgets.new_page)

        layout = QVBoxLayout(widgets.new_page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Drag Macro")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")

        desc = QLabel("Press the edit key to run the drag macro sequence.")
        desc.setStyleSheet("font-size: 13px; color: rgb(170,170,170);")

        block1, self.drag_edit = self.make_input("Edit Key", "q")
        block2, self.drag_select = self.make_input("Select Key", "p")
        block3, self.drag_delay = self.make_input("Delay (ms)", "15")

        actions = QHBoxLayout()
        actions.setSpacing(12)

        drag_start = QPushButton("Start Drag Macro")
        drag_stop = QPushButton("Stop")

        drag_start.setMinimumHeight(42)
        drag_stop.setMinimumHeight(42)

        drag_start.clicked.connect(lambda: self.start_from_page("drag"))
        drag_stop.clicked.connect(self.stop_macro)

        actions.addWidget(drag_start)
        actions.addWidget(drag_stop)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(block1)
        layout.addWidget(block2)
        layout.addWidget(block3)
        layout.addLayout(actions)
        layout.addStretch()

    def build_auto_page(self):
        self.clear_page(widgets.widgets)

        layout = QVBoxLayout(widgets.widgets)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("AutoPick")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")

        desc = QLabel("Hold the trigger key to repeatedly send the pickup key.")
        desc.setStyleSheet("font-size: 13px; color: rgb(170,170,170);")

        block1, self.auto_loot = self.make_input("Pickup Key (E)", "e")
        block2, self.auto_trigger = self.make_input("Macro Key (Mouse4)", "xbutton1")
        block3, self.auto_delay = self.make_input("Delay (ms)", "50")

        actions = QHBoxLayout()
        actions.setSpacing(12)

        auto_start = QPushButton("Start AutoPick")
        auto_stop = QPushButton("Stop")

        auto_start.setMinimumHeight(42)
        auto_stop.setMinimumHeight(42)

        auto_start.clicked.connect(lambda: self.start_from_page("auto"))
        auto_stop.clicked.connect(self.stop_macro)

        actions.addWidget(auto_start)
        actions.addWidget(auto_stop)

        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(block1)
        layout.addWidget(block2)
        layout.addWidget(block3)
        layout.addLayout(actions)
        layout.addStretch()

    def drag_script(self):
        e = self.drag_edit.text().strip().lower()
        h = self.drag_select.text().strip().lower()
        d = self.drag_delay.text().strip()

        if not d.isdigit():
            d = "15"

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${e}:: {{
    if (!enabled)
        return

    SendEvent("{{{e} down}}")
    Sleep({d})
    SendEvent("{{{e} up}}")

    Sleep({d})

    SendEvent("{{{h} down}}")
    KeyWait "{e}"
    SendEvent("{{{h} up}}")

    Sleep({d})

    SendEvent("{{{e} down}}")
    Sleep({d})
    SendEvent("{{{e} up}}")
}}

End::ExitApp
"""

    def auto_script(self):
        loot = self.auto_loot.text().strip().lower()
        trig = self.auto_trigger.text().strip().lower()
        d = self.auto_delay.text().strip()

        if not d.isdigit():
            d = "50"

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${trig}:: {{
    if (!enabled)
        return

    while GetKeyState("{trig}", "P") {{
        Send("{{{loot}}}")
        Sleep({d})
    }}
}}

End::ExitApp
"""

    def update_status_ui(self, active):
        if active:
            self.status_value.setText("active")
            self.status_value.setStyleSheet("font-size: 24px; font-weight: 700; color: rgb(0, 255, 136);")
        else:
            self.status_value.setText("disabled")
            self.status_value.setStyleSheet("font-size: 24px; font-weight: 700; color: rgb(170,170,170);")

        mode_name = "Drag Macro" if self.active_tab == "drag" else "AutoPick"
        self.mode_value.setText(f"Current mode: {mode_name}")

    def start_from_page(self, tab):
        self.active_tab = tab
        self.start_macro()

    def start_macro(self):
        self.stop_macro()

        if not os.path.exists(self.AHK):
            self.status_value.setText("AHK not found")
            self.status_value.setStyleSheet("font-size: 24px; font-weight: 700; color: rgb(255, 85, 127);")
            return

        code = self.drag_script() if self.active_tab == "drag" else self.auto_script()

        with open(self.ahk_file, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            self.proc = subprocess.Popen([self.AHK, self.ahk_file])
            self.update_status_ui(True)
        except Exception:
            self.status_value.setText("start error")
            self.status_value.setStyleSheet("font-size: 24px; font-weight: 700; color: rgb(255, 85, 127);")

    def stop_macro(self):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None

        self.update_status_ui(False)

    def buttonClick(self):
        btn = self.sender()
        btnName = btn.objectName()

        if btnName == "btn_home":
            widgets.stackedWidget.setCurrentWidget(widgets.home)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        if btnName == "btn_widgets":
            self.active_tab = "auto"
            self.mode_value.setText("Current mode: AutoPick")
            widgets.stackedWidget.setCurrentWidget(widgets.widgets)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        if btnName == "btn_new":
            self.active_tab = "drag"
            self.mode_value.setText("Current mode: Drag Macro")
            widgets.stackedWidget.setCurrentWidget(widgets.new_page)
            UIFunctions.resetStyle(self, btnName)
            btn.setStyleSheet(UIFunctions.selectMenu(btn.styleSheet()))

        if btnName == "btn_save":
            self.start_macro()

        print(f'Button "{btnName}" pressed!')

    def resizeEvent(self, event):
        UIFunctions.resize_grips(self)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        self.dragPos = event.globalPos()

        if event.buttons() == Qt.LeftButton:
            print("Mouse click: LEFT CLICK")
        if event.buttons() == Qt.RightButton:
            print("Mouse click: RIGHT CLICK")

        super().mousePressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow()
    sys.exit(app.exec_())

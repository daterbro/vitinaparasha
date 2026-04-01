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

        widgets.stackedWidget.setCurrentWidget(widgets.home)

    def make_input(self, title, default):
        block = QFrame()
        block.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.03);
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(block)

        label = QLabel(title)
        entry = QLineEdit()
        entry.setText(default)

        layout.addWidget(label)
        layout.addWidget(entry)

        return block, entry

    def build_home_page(self):
        layout = QVBoxLayout(widgets.home)

        self.status_value = QLabel("disabled")
        self.mode_value = QLabel("Current mode: Drag Macro")

        btn_start = QPushButton("Start")
        btn_stop = QPushButton("Stop")

        btn_start.clicked.connect(self.start_macro)
        btn_stop.clicked.connect(self.stop_macro)

        layout.addWidget(self.status_value)
        layout.addWidget(self.mode_value)
        layout.addWidget(btn_start)
        layout.addWidget(btn_stop)

    def build_drag_page(self):
        layout = QVBoxLayout(widgets.new_page)

        _, self.drag_edit = self.make_input("Edit Key", "q")
        _, self.drag_select = self.make_input("Select Key", "p")
        _, self.drag_delay = self.make_input("Delay", "15")

    def build_auto_page(self):
        layout = QVBoxLayout(widgets.widgets)

        _, self.auto_loot = self.make_input("Loot", "e")
        _, self.auto_trigger = self.make_input("Trigger", "xbutton1")
        _, self.auto_delay = self.make_input("Delay", "50")

    def drag_script(self):
        e = self.drag_edit.text()
        h = self.drag_select.text()
        d = self.drag_delay.text()

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

global enabled := true
F1::enabled := !enabled

*${e}:: {{
    SendEvent("{{{e} down}}")
    Sleep({d})
    SendEvent("{{{e} up}}")

    SendEvent("{{{h} down}}")
    KeyWait "{e}"
    SendEvent("{{{h} up}}")
}}

End::ExitApp
"""

    def auto_script(self):
        loot = self.auto_loot.text()
        trig = self.auto_trigger.text()
        d = self.auto_delay.text()

        return f"""#Requires AutoHotkey v2.0
#SingleInstance Force

*${trig}:: {{
    while GetKeyState("{trig}", "P") {{
        Send("{{{loot}}}")
        Sleep({d})
    }}
}}

End::ExitApp
"""

    def start_macro(self):
        self.stop_macro()

        code = self.drag_script() if self.active_tab == "drag" else self.auto_script()

        with open(self.ahk_file, "w") as f:
            f.write(code)

        self.proc = subprocess.Popen([self.AHK, self.ahk_file])
        self.status_value.setText("active")

    def stop_macro(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

        self.status_value.setText("disabled")

    def buttonClick(self):
        btn = self.sender().objectName()

        if btn == "btn_widgets":
            self.active_tab = "auto"

        if btn == "btn_new":
            self.active_tab = "drag"

        if btn == "btn_save":
            self.start_macro()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

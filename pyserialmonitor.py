import time
import threading
from PySide2.QtWidgets import QMainWindow, QApplication, QGridLayout, QAction, QWidget, QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox, QTextEdit, QStackedWidget, QSpinBox, QSplitter, QPlainTextEdit
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor
import serial
from serial.tools import list_ports


STANDARD_BAUDRATES = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 128000, 256000]
STOPBITS = [1, 2]
ENCODINGS = ["ascii", "utf-8", "utf-16", "utf-32"]



class SerialDeviceGui(QWidget):

    def __init__(self, gui_parent, name="Default"):
        super().__init__()
        self.name = name
        self.serial = None
        self.gui_parent = gui_parent

        self.layout = QGridLayout()
        self._setup()
        self.setLayout(self.layout)


    def remove(self):
        self.gui_parent.remove_device(self)


    def read(self):
        if self.serial:
            if self.serial.in_waiting > 0:
                return self.serial.read(self.serial.in_waiting).decode(self.encoding, errors='ignore')


    def write(self, bytes):
        if self.serial:
            self.serial.write(bytes)


    def apply(self):
        self.name = self.name_entry.text()
        self.gui_parent.update_device_list()
        if self.baudrate_entry_checkbox.isChecked():
            baudrate = int(self.baudrate_entry_standard.currentText())
        else:
            baudrate = self.baudrate_entry_manual.value()
        if self.location_entry_checkbox.isChecked():
            location = self.location_entry_existing.currentText().split()[0]
        else:
            location = self.location_entry_manual.text()
        stopbits = int(self.stopbits_entry.currentText())
        self.encoding = self.encoding_entry.currentText()
        if self.serial:
            self.serial.close()
        self.serial = serial.Serial(location, baudrate, stopbits=stopbits)


    def update_locations(self):
        devices = list_ports.comports(True)
        devices = [str(d) for d in devices]
        self.location_entry_existing.clear()
        self.location_entry_existing.addItems(devices)


    def update_location_existing(self):
        if self.location_entry_checkbox.isChecked():
            self.location_entry.setCurrentWidget(self.location_entry_existing)
        else:
            self.location_entry_manual.setText(self.location_entry_existing.currentText())
            self.location_entry.setCurrentWidget(self.location_entry_manual)


    def update_baudrate_standard(self):
        if self.baudrate_entry_checkbox.isChecked():
            self.baudrate_entry.setCurrentWidget(self.baudrate_entry_standard)
        else:
            self.baudrate_entry_manual.setValue(int(self.baudrate_entry_standard.currentText()))
            self.baudrate_entry.setCurrentWidget(self.baudrate_entry_manual)


    def _setup(self):
        self.name_entry = QLineEdit()
        self.name_entry.setText(self.name)

        self.location_entry = QStackedWidget()
        self.location_entry.setFixedHeight(25) # FIXME: set policy not size
        self.location_entry_existing = QComboBox()
        self.location_entry_manual = QLineEdit()
        self.location_entry.addWidget(self.location_entry_existing)
        self.location_entry.addWidget(self.location_entry_manual)
        self.location_entry_checkbox = QCheckBox("Existing")
        self.location_entry_checkbox.setCheckState(Qt.Checked)
        self.location_entry_checkbox.stateChanged.connect(self.update_location_existing)
        location_entry_refresh = QPushButton("Refresh")
        location_entry_refresh.clicked.connect(self.update_locations)

        self.baudrate_entry = QStackedWidget()
        self.baudrate_entry.setFixedHeight(25) # FIXME: set policy not size
        self.baudrate_entry_standard = QComboBox()
        self.baudrate_entry_manual = QSpinBox()
        self.baudrate_entry_manual.setRange(0, 16000000)
        self.baudrate_entry.addWidget(self.baudrate_entry_standard)
        self.baudrate_entry.addWidget(self.baudrate_entry_manual)
        self.baudrate_entry_standard.addItems([str(s) for s in STANDARD_BAUDRATES])
        self.baudrate_entry_checkbox = QCheckBox("Standard Rate")
        self.baudrate_entry_checkbox.setCheckState(Qt.Checked)
        self.baudrate_entry_checkbox.stateChanged.connect(self.update_baudrate_standard)

        self.encoding_entry = QComboBox()
        self.encoding_entry.addItems(ENCODINGS)

        self.stopbits_entry = QComboBox()
        self.stopbits_entry.addItems([str(s) for s in STOPBITS])

        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove)

        n = 0
        self.layout.addWidget(QLabel("name:"), n, 0, 1, 1)
        self.layout.addWidget(self.name_entry, n, 1, 1, -1)
        n += 1
        self.layout.addWidget(QLabel("location:"), n, 0, 1, 1)
        self.layout.addWidget(self.location_entry, n, 1, 1, 1)
        self.layout.addWidget(self.location_entry_checkbox, n, 2, 1, 1)
        self.layout.addWidget(location_entry_refresh, n, 3, 1, 1)
        n += 1
        self.layout.addWidget(QLabel("baudrate:"), n, 0, 1, 1)
        self.layout.addWidget(self.baudrate_entry, n, 1, 1, 1)
        self.layout.addWidget(self.baudrate_entry_checkbox, n, 2, 1, -1)
        n += 1
        self.layout.addWidget(QLabel("encoding:"), n, 0, 1, 1)
        self.layout.addWidget(self.encoding_entry, n, 1, 1, -1)
        n += 1
        self.layout.addWidget(QLabel("stopbits:"), n, 0, 1, 1)
        self.layout.addWidget(self.stopbits_entry, n, 1, 1, -1)
        n += 1
        self.layout.addWidget(apply_button, n, 0, 1, -1)
        n += 1
        self.layout.addWidget(remove_button, n, 0, 1, -1)
        n += 1
        self.layout.addWidget(QLabel(), n, 0, -1, -1)

        self.update_baudrate_standard()
        self.update_location_existing()



class SerialDevicesGui(QWidget):

    def __init__(self):
        super().__init__()

        self.serial_device_list = []
        self.current_serial_device = None
        self.monotonic_device_num = 0

        self.layout = QGridLayout()
        self._setup()
        self.setLayout(self.layout)


    def update_device_list(self):
        self.serial_devices.clear()
        device_names = [d.name for d in self.serial_device_list]
        self.serial_devices.addItems(device_names)
        if len(self.serial_device_list) == 0:
            self.new_device()
        self.set_device(self.current_serial_device)


    def new_device(self):
        new_device = SerialDeviceGui(self, f"device_{self.monotonic_device_num}")
        self.serial_device_list.append(new_device)
        self.current_serial_device = new_device
        self.monotonic_device_num += 1
        self.update_device_list()


    def remove_device(self, device):
        self.serial_device_list.remove(device)
        self.layout.removeWidget(device)
        device.setParent(None)
        self.layout.update()
        self.update_device_list()


    def set_device(self, device):
        if len(self.serial_device_list) > 1:
            self.layout.removeWidget(self.current_serial_device)
            self.current_serial_device.setParent(None)
        self.current_serial_device = device
        self.layout.addWidget(device, 2, 0, -1, -1)
        self.layout.update()


    def select_device(self):
        device = self.serial_devices.currentText()
        for d in self.serial_device_list:
            if d.name == device:
                self.set_device(d)



    def _setup(self):
        new_device = QPushButton("New Device")
        new_device.clicked.connect(self.new_device)

        self.serial_devices = QComboBox()
        self.serial_devices.setInsertPolicy(QComboBox.InsertAtBottom)
        self.serial_devices.currentIndexChanged.connect(self.select_device)

        n = 0
        self.layout.addWidget(new_device, n, 0, 1, 1)
        n += 1
        self.layout.addWidget(self.serial_devices, n, 0, 1, 1)

        self.new_device()



class SerialInputGui(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QGridLayout()
        self._setup()
        self.setLayout(self.layout)


    def send(self):
        text = self.text.toPlainText()
        self.text.clear()


    def send_if_checked(self):
        if self.send_on_enter.isChecked():
            self.send()


    def _setup(self):
        self.text = QPlainTextEdit()
        self.text.setReadOnly(False)
        #self.text.returnPressed.connect(self.send_if_checked)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send)

        self.send_on_enter = QCheckBox("Send on Enter")
        self.send_on_enter.setCheckState(Qt.Checked)

        self.layout.addWidget(self.text, 0, 0, -1, 1)
        self.layout.addWidget(send_button, 0, 1, 1, 1)
        self.layout.addWidget(self.send_on_enter, 1, 1, 1, 1)



class SerialMonitorGui(QWidget):

    def __init__(self, gui_parent):
        super().__init__()
        self.gui_parent = gui_parent
        self.layout = QGridLayout()
        self._setup()
        self.setLayout(self.layout)
        x = threading.Thread(target=self._run)
        x.start()


    def _run(self):
        while (1):
            # Read anything and write to console
            for s in self.gui_parent.serial_device.serial_device_list:
                text = s.read()
                if text:
                    text = text.strip()
                    text = text.replace("\n", f"\n{s.name}: ")
                    self.text.append(f"{s.name}: {text}")
                    self.text.moveCursor(QTextCursor.End)
            time.sleep(0.01)


    def _setup(self):
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.layout.addWidget(self.text, 0, 0, -1, -1)



class ApplicationGui(QWidget):

    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self._setup()
        self.setLayout(self.layout)


    def serial_monitor_save(self):
        pass


    def serial_device_save(self):
        pass


    def _setup(self):
        self.serial_input = SerialInputGui()
        self.serial_device = SerialDevicesGui()
        self.serial_monitor = SerialMonitorGui(self)

        hsplitter = QSplitter()
        hsplitter.setRubberBand(-1)
        hsplitter.setHandleWidth(10)
        hsplitter.setOrientation(Qt.Horizontal)
        hsplitter.addWidget(self.serial_monitor)
        hsplitter.addWidget(self.serial_device)

        vsplitter = QSplitter()
        vsplitter.setRubberBand(-1)
        vsplitter.setHandleWidth(10)
        vsplitter.setOrientation(Qt.Vertical)
        vsplitter.addWidget(hsplitter)
        vsplitter.addWidget(self.serial_input)

        self.layout.addWidget(vsplitter, 0, 0, 1, 1)



class ApplicationMain(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Monitor")
        self.setGeometry(100,100,400,400)
        self.app = ApplicationGui()
        self._setup()
        self.setCentralWidget(self.app)


    def _setup(self):
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")
        options_menu = main_menu.addMenu("Options")

        file_menu_save = QAction("Save", self)
        file_menu_save.setShortcut("Ctrl+s")
        file_menu_save.triggered.connect(self.app.serial_monitor_save)
        file_menu.addAction(file_menu_save)

        file_menu_save_config = QAction("Save Configuration", self)
        file_menu_save_config.triggered.connect(self.app.serial_device_save)
        file_menu.addAction(file_menu_save_config)

        file_menu_exit = QAction("Exit", self)
        file_menu_exit.setShortcut("Ctrl+c")
        file_menu_exit.triggered.connect(self.close)
        file_menu.addAction(file_menu_exit)




if __name__ == "__main__":
    import sys
    qapplication = QApplication(sys.argv)
    application = ApplicationMain()
    application.show()
    sys.exit(qapplication.exec_())

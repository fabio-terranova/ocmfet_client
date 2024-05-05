from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)
from scipy.signal import butter, iirnotch


class DataProcessingWidget(QWidget):
    def __init__(self, fs, data_processer, bandpass, notch, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.fs = fs * 1e3
        self.data_processer = data_processer
        self.bandpass = bandpass
        self.notch = notch
        self.init_ui()

    def init_ui(self):
        self.notch_group = QGroupBox("Notch filter")
        self.notch_group.setCheckable(True)
        self.notch_group.setChecked(False)
        self.notch_group.toggled.connect(self.update_filters)
        self.notch_spin = QDoubleSpinBox()
        self.notch_spin.setRange(1, self.fs / 2)
        self.notch_spin.setSuffix(" Hz")
        self.notch_spin.setValue(self.notch[0])
        self.notch_spin.valueChanged.connect(self.update_filters)
        self.q_label = QLabel("Q")
        self.q_spin = QSpinBox()
        self.q_spin.setRange(10, 100)
        self.q_spin.setValue(self.notch[1])
        self.q_spin.valueChanged.connect(self.update_filters)

        self.bandpass_group = QGroupBox("Bandpass filter")
        self.bandpass_group.setCheckable(True)
        self.bandpass_group.setChecked(False)
        self.bandpass_group.toggled.connect(self.update_filters)
        self.low_label = QLabel("Low")
        self.low_spin = QDoubleSpinBox()
        self.low_spin.setRange(0.01, self.fs / 2)
        self.low_spin.setSuffix(" Hz")
        self.low_spin.setValue(self.bandpass[0][0])
        self.low_spin.valueChanged.connect(self.update_filters)
        self.high_label = QLabel("High")
        self.high_spin = QDoubleSpinBox()
        self.high_spin.setRange(1, self.fs / 2 - 1)
        self.high_spin.setSuffix(" Hz")
        self.high_spin.setValue(self.bandpass[0][1])
        self.high_spin.valueChanged.connect(self.update_filters)
        self.order_label = QLabel("Order")
        self.order_spin = QSpinBox()
        self.order_spin.setRange(1, 10)
        self.order_spin.setValue(self.bandpass[1])
        self.order_spin.valueChanged.connect(self.update_filters)

        self.layout = QHBoxLayout()

        self.notch_layout = QHBoxLayout()
        self.notch_layout.addWidget(self.notch_spin)
        self.notch_layout.addWidget(self.q_label)
        self.notch_layout.addWidget(self.q_spin)
        self.notch_group.setLayout(self.notch_layout)

        self.bandpass_layout = QHBoxLayout()
        self.bandpass_layout.addWidget(self.low_label)
        self.bandpass_layout.addWidget(self.low_spin)
        self.bandpass_layout.addWidget(self.high_label)
        self.bandpass_layout.addWidget(self.high_spin)
        self.bandpass_layout.addWidget(self.order_label)
        self.bandpass_layout.addWidget(self.order_spin)
        self.bandpass_group.setLayout(self.bandpass_layout)

        self.layout.addWidget(self.notch_group)
        self.layout.addWidget(self.bandpass_group)
        self.setLayout(self.layout)

    def update_filters(self):
        if self.high_spin.value() <= self.low_spin.value():
            self.high_spin.setValue(self.low_spin.value() + 1)

        self.bandpass = (
            (self.low_spin.value(), self.high_spin.value()),
            self.order_spin.value(),
        )
        self.notch = (self.notch_spin.value(), self.q_spin.value())

        self.data_processer.change_filters(self.get_filters())

    def get_filters(self):
        filters = []

        if self.notch_group.isChecked():
            b, a = iirnotch(self.notch[0], self.notch[1], fs=self.fs)
            filters.append((b, a))
        if self.bandpass_group.isChecked():
            b, a = butter(2, self.bandpass[0], btype="bandpass", fs=self.fs)
            filters.append((b, a))

        return filters

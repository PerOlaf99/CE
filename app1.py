import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QCheckBox, QGridLayout, QFileDialog)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.signal import find_peaks
from scipy.integrate import simpson

class ElectropherogramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Electropherogram Analyzer")
        self.resize(1300, 800)
        
        self.data = None
        self.active_channels = {'CH1': False, 'CH2': True, 'CH3': False, 'CH4': False, 'Current': False}
        self.peaks = [] # List of dicts: {'scan': x, 'area': y}

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # --- Sidebar: Plate Map & Toggles ---
        sidebar = QVBoxLayout()
        plate_grid = QGridLayout()
        # Create 96 buttons (simplified to 2x2 for brevity, replace with nested loop)
        for i in range(4):
            btn = QPushButton(f"Well {i+1}")
            plate_grid.addWidget(btn, i//2, i%2)
        sidebar.addLayout(plate_grid)

        for ch in self.active_channels:
            cb = QCheckBox(ch)
            cb.setChecked(self.active_channels[ch])
            cb.stateChanged.connect(lambda state, c=ch: self.toggle_channel(c, state))
            sidebar.addWidget(cb)
        
        load_btn = QPushButton("Load Data")
        load_btn.clicked.connect(self.load_data)
        sidebar.addWidget(load_btn)

        # --- Plot Area ---
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # --- Peak Table ---
        self.peak_table = QTableWidget(0, 3)
        self.peak_table.setHorizontalHeaderLabels(['Scan', 'Ht', 'Area'])

        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.canvas, 3)
        main_layout.addWidget(self.peak_table, 1)
        
        self.setCentralWidget(main_widget)

    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File")
        if filename:
            self.data = pd.read_csv(filename, sep='\t', skiprows=35, header=0, engine='python')
            self.data.columns = self.data.columns.str.strip()
            self.data = self.data.apply(pd.to_numeric, errors='coerce').fillna(0)
            self.update_plot()

    def toggle_channel(self, channel, state):
        self.active_channels[channel] = (state == 2)
        self.update_plot()

    def update_plot(self):
        if self.data is None: return
        self.ax.clear()
        scan = self.data.iloc[:, 0]
        
        for i, (name, active) in enumerate(self.active_channels.items()):
            if active:
                # Assuming columns follow index 1, 2, 3, 4, 5
                self.ax.plot(scan, self.data.iloc[:, i+1], label=name)
        
        self.ax.legend()
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes != self.ax or self.data is None: return
        
        # Calculate area around click
        scan_val = event.xdata
        idx = (self.data.iloc[:, 0] - scan_val).abs().idxmin()
        
        # Integration window
        start, end = max(0, idx-10), min(len(self.data), idx+10)
        y_data = self.data.iloc[start:end, 2] # Default to CH2
        area = simpson(y=y_data, dx=1)
        
        # Update Table
        row = self.peak_table.rowCount()
        self.peak_table.insertRow(row)
        self.peak_table.setItem(row, 0, QTableWidgetItem(f"{scan_val:.1f}"))
        self.peak_table.setItem(row, 1, QTableWidgetItem(f"{event.ydata:.1f}"))
        self.peak_table.setItem(row, 2, QTableWidgetItem(f"{area:.1f}"))
        
        # Mark on plot
        self.ax.plot(scan_val, event.ydata, 'rx')
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ElectropherogramApp()
    window.show()
    sys.exit(app.exec_())

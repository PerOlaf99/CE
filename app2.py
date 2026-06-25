import sys
import os
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from scipy.signal import find_peaks
from scipy.integrate import simpson

class ElectropherogramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Electropherogram Analyzer")
        self.resize(1400, 850)
        self.all_data = {}
        self.well_list = [f"{r}{c:02d}" for r in 'ABCDEFGH' for c in range(1, 13)]
        self.current_idx = 0
        self.active_channels = {'CH1': False, 'CH2': True, 'CH3': False, 'CH4': False, 'Current': False}
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        layout = QHBoxLayout(main_widget)
        
        # --- Sidebar ---
        sidebar = QVBoxLayout()
        
        # Nav Arrows
        nav_layout = QHBoxLayout()
        prev_btn = QPushButton("← Prev"); prev_btn.clicked.connect(self.prev_well)
        next_btn = QPushButton("Next →"); next_btn.clicked.connect(self.next_well)
        nav_layout.addWidget(prev_btn); nav_layout.addWidget(next_btn)
        sidebar.addLayout(nav_layout)
        
        # Plate Map
        self.plate_grid = QGridLayout()
        self.well_buttons = {}
        for i, well in enumerate(self.well_list):
            btn = QPushButton(well); btn.setFixedSize(30, 30)
            btn.clicked.connect(lambda checked, w=well: self.load_well(w))
            self.plate_grid.addWidget(btn, i//12, i%12)
            self.well_buttons[well] = btn
        sidebar.addLayout(self.plate_grid)
        
        # Controls
        for ch in self.active_channels:
            cb = QCheckBox(ch); cb.setChecked(self.active_channels[ch])
            cb.stateChanged.connect(lambda state, c=ch: self.update_plot())
            sidebar.addWidget(cb)
            
        self.threshold_slider = QSlider(Qt.Horizontal); self.threshold_slider.setRange(1, 5000)
        sidebar.addWidget(QLabel("Peak Height Threshold")); sidebar.addWidget(self.threshold_slider)
        
        load_btn = QPushButton("Load Folder"); load_btn.clicked.connect(self.load_folder)
        sidebar.addWidget(load_btn)
        
        # --- Plot Area ---
        plot_area = QVBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self) # X/Y Zoom tool
        plot_area.addWidget(self.toolbar)
        plot_area.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()
        
        layout.addLayout(sidebar, 1); layout.addLayout(plot_area, 4)
        self.setCentralWidget(main_widget)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Data Folder")
        if folder:
            for f in os.listdir(folder):
                if f.endswith('.txt'):
                    well = f.split('.')[0]
                    if well in self.well_list:
                        df = pd.read_csv(os.path.join(folder, f), sep='\t', skiprows=35, header=0, engine='python')
                        self.all_data[well] = df.apply(pd.to_numeric, errors='coerce').fillna(0)
                        self.well_buttons[well].setStyleSheet("background-color: lightgreen")

    def load_well(self, well):
        if well in self.all_data:
            self.current_idx = self.well_list.index(well)
            self.update_plot()

    def prev_well(self): self.current_idx = max(0, self.current_idx - 1); self.update_plot()
    def next_well(self): self.current_idx = min(len(self.well_list)-1, self.current_idx + 1); self.update_plot()

    def update_plot(self):
        well = self.well_list[self.current_idx]
        if well not in self.all_data: return
        df = self.all_data[well]
        self.ax.clear(); self.ax2.clear()
        
        # Plot Logic
        scan = df.iloc[:, 0]
        threshold = self.threshold_slider.value()
        
        for i, (name, active) in enumerate(self.active_channels.items()):
            if active:
                y = df.iloc[:, i+1]
                if name == 'Current': self.ax2.plot(scan, y, 'r--', label='Current')
                else: 
                    self.ax.plot(scan, y, label=name)
                    # Auto Peak Detection
                    peaks, _ = find_peaks(y, height=threshold)
                    self.ax.plot(scan.iloc[peaks], y.iloc[peaks], 'rx')
                    # Calculate Area
                    for p in peaks:
                        start, end = max(0, p-5), min(len(y), p+5)
                        area = simpson(y=y.iloc[start:end], dx=1)
                        self.ax.annotate(f"{area:.0f}", (scan.iloc[p], y.iloc[p]))
        
        self.ax.set_title(f"Well {well}")
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ElectropherogramApp()
    window.show()
    sys.exit(app.exec_())

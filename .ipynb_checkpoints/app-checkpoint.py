import os
import glob
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_prominences
from scipy.integrate import trapezoid
from sklearn.ensemble import RandomForestClassifier

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class ElectropherogramGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ML Electropherogram Peak Analyzer")
        self.root.geometry("1200x800")
        
        # State variables
        self.folder_path = ""
        self.csv_files = []
        self.current_file_idx = 0
        self.master_df = pd.DataFrame()
        self.file_data = {} # Stores {filename: (time, signal)}
        self.clf = RandomForestClassifier(random_state=42)
        self.is_trained = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # --- TOP CONTROL PANEL ---
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(top_frame, text="Select Folder", command=self.load_folder, bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        self.lbl_folder = tk.Label(top_frame, text="No folder selected", textvar="", font=("Arial", 9, "italic"))
        self.lbl_folder.pack(side=tk.LEFT, padx=5)
        
        # --- MIDDLE MAIN SPLIT ---
        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Left Panel: File list and ML Controls
        left_panel = tk.Frame(main_frame, width=250, bd=1, relief=tk.SOLID, padx=5, pady=5)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="CSV Files", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        self.file_listbox = tk.Listbox(left_panel, selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_selected)
        
        # ML controls frame
        ml_frame = tk.LabelFrame(left_panel, text="ML Status & Actions", padx=5, pady=5)
        ml_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.lbl_status = tk.Label(ml_frame, text="Model status: Untrained", fg="red", font=("Arial", 9, "bold"))
        self.lbl_status.pack(anchor=tk.W, pady=2)
        
        tk.Button(ml_frame, text="Train ML on Labels", command=self.train_ml, bg="#4CAF50", fg="white", width=20).pack(pady=3)
        tk.Button(ml_frame, text="Export CSV Results", command=self.export_results, bg="#FF9800", fg="white", width=20).pack(pady=3)
        
        # Right Panel: Plot and Click Data
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Canvas for matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Matplotlib toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, right_panel)
        self.toolbar.update()
        
        # Connect the click picker event
        self.fig.canvas.mpl_connect('pick_event', self.on_peak_clicked)

    # ---------------------------------------------------------
    # DATA PROCESSING PIPELINE
    # ---------------------------------------------------------
    def load_folder(self):
        self.folder_path = filedialog.askdirectory()
        if not self.folder_path:
            return
        
        self.lbl_folder.config(text=os.path.basename(self.folder_path))
        self.csv_files = sorted(glob.glob(os.path.join(self.folder_path, "*.csv")))
        
        if not self.csv_files:
            messagebox.showerror("Error", "No CSV files found in this folder.")
            return
        
        self.file_listbox.delete(0, tk.END)
        for f in self.csv_files:
            self.file_listbox.insert(tk.END, os.path.basename(f))
            
        self.process_all_files()
        self.file_listbox.selection_set(0)
        self.load_file(0)
        
    def process_all_files(self):
        """Processes files to find peaks and build features beforehand."""
        all_peaks = []
        self.file_data.clear()
        
        for file_path in self.csv_files:
            fname = os.path.basename(file_path)
            try:
                df = pd.read_csv(file_path)
                # Auto detect common column name cases
                time_col = [c for c in df.columns if 'time' in c.lower()][0]
                sig_col = [c for c in df.columns if 'signal' in c.lower() or 'intens' in c.lower()][0]
                
                t = df[time_col].values
                sig = df[sig_col].values
                self.file_data[fname] = (t, sig)
                
                # Baseline feature calculations
                peaks, _ = find_peaks(sig, distance=30, prominence=0.5)
                if len(peaks) == 0: continue
                
                noise_mask = np.ones(len(sig), dtype=bool)
                for p in peaks:
                    noise_mask[max(0, p-15):min(len(sig), p+15)] = False
                noise_std = np.std(sig[noise_mask]) if np.any(noise_mask) else 1e-6
                
                prominences = peak_prominences(sig, peaks)[0]
                
                for i, p_idx in enumerate(peaks):
                    left = max(0, p_idx - 25)
                    right = min(len(t), p_idx + 25)
                    y_base = np.linspace(sig[left], sig[right], right - left)
                    auc = trapezoid(sig[left:right] - y_base, t[left:right])
                    
                    all_peaks.append({
                        'filename': fname,
                        'peak_id': i,
                        'time': t[p_idx],
                        'intensity': sig[p_idx],
                        'height': prominences[i],
                        'auc': auc,
                        'snr': prominences[i] / noise_std,
                        'user_label': -1,       # -1 = Unlabeled, 0 = Noise, 1 = Valid Peak
                        'ml_prediction': -1     # Match user label initially
                    })
            except Exception as e:
                print(f"Failed to process {fname}: {e}")
                
        self.master_df = pd.DataFrame(all_peaks)

    # ---------------------------------------------------------
    # GUI INTERACTIONS & PLOTTING
    # ---------------------------------------------------------
    def on_file_selected(self, event):
        idx = self.file_listbox.curselection()
        if idx:
            self.load_file(idx[0])
            
    def load_file(self, index):
        self.current_file_idx = index
        fname = os.path.basename(self.csv_files[index])
        
        if fname not in self.file_data or self.master_df.empty:
            return
            
        t, sig = self.file_data[fname]
        file_peaks = self.master_df[self.master_df['filename'] == fname]
        
        self.ax.clear()
        self.ax.plot(t, sig, color='black', alpha=0.6, label="Electropherogram")
        
        # Plot peak points dynamically based on classification or label status
        for idx, row in file_peaks.iterrows():
            # Color priority: User Override Label -> ML Prediction -> Unlabeled Default (Gray)
            if row['user_label'] == 1:
                color, marker = 'green', 'o'
            elif row['user_label'] == 0:
                color, marker = 'red', 'X'
            elif self.is_trained and row['ml_prediction'] == 1:
                color, marker = '#81C784', 'o' # Lighter green
            elif self.is_trained and row['ml_prediction'] == 0:
                color, marker = '#E57373', 'X' # Lighter red
            else:
                color, marker = 'gray', '^'
                
            # picker=5 makes points clickable within 5 pixels radius
            self.ax.plot(row['time'], row['intensity'], marker=marker, color=color, 
                         markersize=9, picker=5, label=f"pk_{idx}")
            
            self.ax.text(row['time'], row['intensity'] + (max(sig)*0.02), 
                         f"SNR:{row['snr']:.1f}", fontsize=8, color='blue', ha='center')

        self.ax.set_title(f"File: {fname} (Left-Click Peak icon to Toggle: Valid/Noise/Reset)")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Intensity")
        self.canvas.draw()
        
    def on_peak_clicked(self, event):
        """Toggles peak user_label status on user click event."""
        # Find which exact plot handle was selected using the matrix tracker label
        lbl = event.artist.get_label()
        if not lbl.startswith("pk_"):
            return
            
        master_row_idx = int(lbl.split("_")[1])
        current_status = self.master_df.at[master_row_idx, 'user_label']
        
        # Cycle states: Unlabeled (-1) -> Valid Peak (1) -> Noise (0) -> Unlabeled (-1)
        if current_status == -1:   next_status = 1
        elif current_status == 1:  next_status = 0
        else:                      next_status = -1
        
        self.master_df.at[master_row_idx, 'user_label'] = next_status
        
        # Instant refresh plot screen layout
        self.load_file(self.current_file_idx)

    # ---------------------------------------------------------
    # MACHINE LEARNING ENGINE
    # ---------------------------------------------------------
    def train_ml(self):
        if self.master_df.empty:
            return
            
        # Extract records where user actually assigned validation tags (0 or 1)
        training_set = self.master_df[self.master_df['user_label'].isin([0, 1])]
        


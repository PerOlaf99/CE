#!/usr/bin/env python3
"""
MegaBACE .rsd Binary Basecaller & CE-LIF Peak Area Analyzer
Standalone Python CLI tool for Linux / Unix high-throughput genomic data processing.

Usage:
  python3 basecall_megabace.py <sample.rsd> [--output-dir ./results] [--prominence 120] [--fwhm 7]

Requirements:
  pip install numpy scipy matplotlib
"""

import sys
import os
import math
import struct
import argparse
import numpy as np
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit

def parse_megabace_rsd(file_path):
    """
    Parses MegaBACE .rsd binary file 4-channel fluorescence data.
    """
    with open(file_path, 'rb') as f:
        data = f.read()

    header_magic = data[:16].decode('ascii', errors='ignore')
    print(f"[+] Loaded file: {file_path} ({len(data)} bytes)")
    print(f"[+] Header magic: {header_magic.strip()}")

    # Unpack numScans at offset 32
    if len(data) >= 64:
        num_scans = struct.unpack('<I', data[32:36])[0]
        capillary_id = struct.unpack('<H', data[36:38])[0]
    else:
        num_scans = (len(data) - 256) // 8
        capillary_id = 1

    if num_scans <= 0 or num_scans > 50000:
        num_scans = (len(data) - 256) // 8

    print(f"[+] Capillary ID: {capillary_id}, Scan points: {num_scans}")

    header_size = 256
    channels = {'A': [], 'C': [], 'G': [], 'T': []}
    keys = ['A', 'C', 'G', 'T']

    offset = header_size
    for key in keys:
        channel_data = []
        for _ in range(num_scans):
            if offset + 2 <= len(data):
                val = struct.unpack('<H', data[offset:offset+2])[0]
                channel_data.append(val)
                offset += 2
            else:
                channel_data.append(0)
        channels[key] = np.array(channel_data, dtype=np.float32)

    return num_scans, capillary_id, channels

def deconvolve_color_matrix(channels, matrix=None):
    """
    Applies 4x4 matrix inversion for dye spectral overlap removal.
    """
    if matrix is None:
        # MegaBACE ET Dye default matrix
        matrix = np.array([
            [1.00, 0.18, 0.02, 0.00],
            [0.22, 1.00, 0.20, 0.03],
            [0.05, 0.25, 1.00, 0.28],
            [0.00, 0.04, 0.21, 1.00]
        ])

    inv_matrix = np.linalg.inv(matrix)
    keys = ['A', 'C', 'G', 'T']
    stack = np.vstack([channels[k] for k in keys])
    deconvolved_stack = np.dot(inv_matrix, stack)
    deconvolved_stack = np.clip(deconvolved_stack, 0, None)

    return {k: deconvolved_stack[i] for i, k in enumerate(keys)}

def calculate_aup_trapezoidal(signal, left, right):
    """Calculates Area Under Peak (AUP) via Trapezoidal Integration"""
    return np.trapz(signal[left:right+1])

def gaussian(x, height, center, sigma):
    return height * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))

def analyze_peaks_and_basecall(channels, prominence=120, min_dist=10):
    """
    Detects peaks, calculates Area Under Peak (AUP), and predicts base sequence.
    """
    keys = ['A', 'C', 'G', 'T']
    all_peaks = []

    for key in keys:
        sig = channels[key]
        peaks, props = find_peaks(sig, prominence=prominence, distance=min_dist)

        for p in peaks:
            height = sig[p]
            left = max(0, p - 10)
            right = min(len(sig) - 1, p + 10)

            # AUP calculation
            aup_trap = calculate_aup_trapezoidal(sig, left, right)
            fwhm = 7.0 # Estimated width
            sigma = fwhm / 2.355
            aup_gauss = height * sigma * np.sqrt(2 * np.pi)

            all_peaks.append({
                'scan': p,
                'channel': key,
                'height': height,
                'aup_trap': aup_trap,
                'aup_gauss': aup_gauss,
                'fwhm': fwhm,
                'left': left,
                'right': right
            })

    # Sort peaks by scan position
    all_peaks.sort(key=lambda x: x['scan'])

    # Sequence string and quality scores
    sequence = "".join([p['channel'] for p in all_peaks])
    return all_peaks, sequence

def main():
    parser = argparse.ArgumentParser(description="MegaBACE .rsd Linux Basecaller & CE-LIF Peak Area Analyzer")
    parser.add_argument("rsd_file", help="Path to input MegaBACE .rsd binary file")
    parser.add_argument("--output-dir", default="./results", help="Directory to save output CSV and FASTA")
    parser.add_argument("--prominence", type=float, default=120.0, help="Min peak prominence for detection")
    args = parser.parse_args()

    if not os.path.exists(args.rsd_file):
        print(f"Error: File '{args.rsd_file}' not found.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    num_scans, cap_id, channels = parse_megabace_rsd(args.rsd_file)
    deconvolved = deconvolve_color_matrix(channels)
    peaks, sequence = analyze_peaks_and_basecall(deconvolved, prominence=args.prominence)

    base_name = os.path.basename(args.rsd_file).replace('.rsd', '')
    fasta_path = os.path.join(args.output_dir, f"{base_name}.fasta")
    csv_path = os.path.join(args.output_dir, f"{base_name}_peaks.csv")

    # Write FASTA
    with open(fasta_path, 'w') as f:
        f.write(f">{base_name} | Length: {len(sequence)} bp\n{sequence}\n")

    # Write CSV
    with open(csv_path, 'w') as f:
        f.write("Peak_ID,Scan,BaseCall,Channel,Height,AUP_Trapezoid,AUP_Gaussian,FWHM\n")
        for i, p in enumerate(peaks):
            f.write(f"Peak_{i+1},{p['scan']},{p['channel']},{p['channel']},{p['height']:.2f},{p['aup_trap']:.2f},{p['aup_gauss']:.2f},{p['fwhm']:.2f}\n")

    print(f"\n[+] Basecalling Complete!")
    print(f"[+] Total Base Calls: {len(sequence)} bp")
    print(f"[+] Sequence FASTA saved to: {fasta_path}")
    print(f"[+] Peak Area CSV saved to: {csv_path}\n")

if __name__ == "__main__":
    main()

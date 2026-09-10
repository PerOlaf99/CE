#!/usr/bin/env python3
import os, sys, json, re
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI
import extract_training_data as etd
import numpy as np
from Bio import Align

FILES = [
 'A01_2050_2411.json', 'A01_2411_2761.json', 'A01_2761_3010.json',
 'A01_3000_4100.json', 'A01_4100_5000.json', 'A01_5000_5800.json',
 'A01_5800_6350.json', 'A01_6350_6700.json', 'A01_6690_7350.json',
 'A01_7320_7800.json', 'A01_7800_8600.json', 'A01_8600_9332.json',
]

def win_range(fn):
    m = re.search(r'A01_(\d+)_(\d+)\.json', fn)
    return int(m.group(1)), int(m.group(2))

def main():
    gui = SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    seqs = []
    for fn in FILES:
        r0, r1 = win_range(fn)
        d = json.load(open(os.path.join(HERE, fn)))
        gui.load_settings_from_dict(d)
        gui.region_auto_check.setChecked(False)
        gui.region_hybrid_check.setChecked(False)
        gui.region_start_spin.setValue(r0)
        gui.region_stop_spin.setValue(r1)
        gui._run_basecall()
        seq = gui._manual_sequence or ''
        seqs.append((fn, r0, r1, seq))
    print('=== per-window calls ===')
    tot = 0
    for fn, r0, r1, seq in seqs:
        tot += len(seq)
        print(f'{fn} [{r0},{r1}]: len={len(seq)}')
    combined = ''.join(s for _,_,_,s in seqs)
    combined = ''.join(c for c in combined if c in 'ACGTN')
    print(f'\n=== concatenated full read len={len(combined)} (sum windows={tot}) ===')
    print(combined[:160], '...', combined[-40:])
    with open('/tmp/opencode/A01_full_scan.fa', 'w') as f:
        f.write('>A01_full_scan\n' + combined + '\n')

    dd = etd.parse_esd(os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1', 'A01.esd'))
    esd = dd['sequence']
    esd = ''.join(c for c in esd if c in 'ACGTN')
    print(f'ESD full read: n={len(esd)}')

    # global pairwise alignment vs ESD
    al = Align.PairwiseAligner()
    al.mode = 'global'
    al.match_score = 1
    al.mismatch_score = -2
    al.open_gap_score = -3
    al.extend_gap_score = -1
    res = al.align(combined, esd)
    best = res[0]
    a, b = best
    aln_len = len(a)
    ident = sum(1 for x, y in zip(a, b) if x == y and x != '-')
    # identity over aligned (non-gap) positions
    non_gap = sum(1 for x, y in zip(a, b) if x != '-' and y != '-')
    print('\n=== global align call-vs-ESD ===')
    print(f'aligned length={aln_len} matches={ident} non_gap_cols={non_gap}')
    print(f'identity (matches/non_gap) = {100*ident/non_gap:.2f}%')
    print(f'coverage (query bases aligned to ESD) = {non_gap}/{len(combined)} = {100*non_gap/len(combined):.2f}%')
    # show aligned snippet
    print(best)

if __name__ == '__main__':
    main()

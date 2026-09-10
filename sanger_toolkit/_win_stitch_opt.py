#!/usr/bin/env python3
import os, sys, json, subprocess, tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PyQt5.QtWidgets import QApplication

ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct'))
sys.path.insert(0, HERE)
from blast_check import REF

WIN = {
 'A01_[2050_2750].json':  (2050, 2750),
 'A01_[2650_3350].json':  (2650, 3350),
 'A01_[3250_3950].json':  (3250, 3950),
 'A01_[3850_4550].json':  (3850, 4550),
 'A01_[4450_5150].json':  (4450, 5150),
}

app = QApplication(sys.argv)
from sequencing_gui_V15 import SequencingGUI

def call_window(gui, r0, r1):
    gui.region_auto_check.setChecked(False)
    gui.region_hybrid_check.setChecked(False)
    gui.region_start_spin.setValue(r0)
    gui.region_stop_spin.setValue(r1)
    gui._run_basecall()
    return gui._manual_sequence or ''

def blast_region(seq):
    ref = ''.join(l.strip() for l in open(REF) if not l.startswith('>'))
    seq = ''.join(c for c in seq if c in 'ACGT')
    if not seq:
        return None
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td,'m.fa'),'w').write('>M13\n'+ref+'\n')
        open(os.path.join(td,'q.fa'),'w').write('>q\n'+seq+'\n')
        subprocess.run(['makeblastdb','-in',os.path.join(td,'m.fa'),'-dbtype','nucl','-out',os.path.join(td,'db')],check=True,capture_output=True)
        o=os.path.join(td,'o.txt')
        subprocess.run(['blastn','-db',os.path.join(td,'db'),'-query',os.path.join(td,'q.fa'),
                        '-task','megablast','-outfmt','6 qstart qend sstart send pident length bitscore','-out',o],check=True,capture_output=True)
        rows=[l.split() for l in open(o) if l.strip()]
        if not rows: return None
        r=max(rows,key=lambda x:float(x[6]))
        qs,qe,ss,se=map(int,r[:4]); pid=float(r[4])
        # reverse orientation (ss>se): base i -> M13 ss-i
        if ss <= se:
            cov=[(m,b) for m,b in zip(range(ss,se+1),seq[qs-1:qe])]
        else:
            cov=[(ss-i,b) for i,b in zip(range(qs-1,qe),seq[qs-1:qe])]
        cov.sort()
        return {'qstart':qs,'qend':qe,'m13s':min(ss,se),'m13e':max(ss,se),'pid':pid,'len':qe-qs+1,'cov':cov}

def main():
    gui=SequencingGUI()
    gui.well_combo.setCurrentText('A01')
    gui._load_data()
    results=[]
    for sf,(r0,r1) in WIN.items():
        d=json.load(open(os.path.join(HERE,'opt_windows',sf)))
        gui.load_settings_from_dict(d)
        seq=call_window(gui,r0,r1)
        b=blast_region(seq)
        print(f'{sf} [{r0},{r1}]: call_len={len(seq)}', end='')
        if b:
            print(f"  M13={b['m13s']}-{b['m13e']} id={b['pid']:.2f}% aln={b['len']}bp")
            results.append((sf,r0,r1,b))
        else:
            print('  NO ALIGN')
    # Merge by M13 coordinate, first (earliest-scan) window wins for shared M13 pos.
    m13_win={}
    seen={}
    for sf,r0,r1,b in results:
        for m,c in b['cov']:
            if m not in m13_win and sf not in seen.get(m,[]):
                m13_win[m]=c
    mpos=sorted(m13_win)
    combined=''.join(m13_win[m] for m in mpos)
    print(f'\n=== combined M13-anchored len={len(combined)} span={mpos[0]}-{mpos[-1]} ===')
    print(combined)
    with open('/tmp/opencode/combined_opt_A01.fa','w') as f:
        f.write('>combined_opt_A01\n'+combined+'\n')
    # identity vs M13 ref
    ref=''.join(l.strip() for l in open(REF) if not l.startswith('>'))
    sub=ref[mpos[0]-1:mpos[-1]]
    matched=sum(1 for m,c in m13_win.items() if c==ref[m-1].upper())
    print(f'\nMATCHED bases vs M13 within span: {matched}/{len(mpos)} = {100*matched/len(mpos):.2f}%')

if __name__=='__main__':
    main()

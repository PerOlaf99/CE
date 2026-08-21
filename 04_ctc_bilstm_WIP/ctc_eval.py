#!/usr/bin/env python3
"""ctc_eval.py - greedy-decode the trained CTC basecaller and score vs M13."""
import os, sys
import numpy as np

__version__ = '0.2'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

IDX2C = {1: 'A', 2: 'C', 3: 'G', 4: 'T', 5: 'N'}


def greedy_decode(pred):
    idx = pred.argmax(-1)
    out, prev = [], -1
    for k in idx:
        if k != prev and k != 0:
            out.append(IDX2C.get(int(k), 'N'))
        prev = k
    return ''.join(out)


def main():
    wells = sys.argv[1:] or ['A01', 'B02', 'C03', 'D04']
    import tensorflow as tf
    model = tf.keras.models.load_model(
        os.path.join(HERE, 'ctc_basecaller_v1.keras'), compile=False)
    import ctc_train as ct
    import perfect_basecaller as pb
    ref = pb.load_clean_ref()
    accs = []
    for w in wells:
        r = ct.load_well(w)
        if r is None:
            continue
        sep, _ = r
        p = model.predict(sep[None], verbose=0)
        seq = greedy_decode(p[0])
        a = pb.perbase_vs_ref(seq, ref)
        accs.append(a)
        print(f'{w}: len={len(seq)} acc={a:.4f}', flush=True)
    if accs:
        print(f'mean: {np.mean(accs):.4f}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""ctc_debug.py - gradient probe + single-batch overfit test."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import numpy as np
import tensorflow as tf
import ctc_train as ct

r = ct.load_well('A01')
X, Y = ct.pad_batch([r])
print('T,L =', X.shape[1], Y.shape[1], flush=True)

model = ct.make_model()
with tf.GradientTape() as tape:
    yp = model(X, training=True)
    loss = tf.reduce_mean(model.loss(Y, yp))
g = tape.gradient(loss, model.trainable_variables)
norms = [float(tf.norm(gg)) for gg in g if gg is not None]
gnorm = float(np.sqrt(sum(n * n for n in norms)))
print(f'initial loss {float(loss):.1f}  grad-global-norm {gnorm:.4g}', flush=True)

opt = tf.keras.optimizers.Adam(1e-3)


@tf.function(reduce_retracing=True)
def step():
    with tf.GradientTape() as tape:
        yp = model(X, training=True)
        l = tf.reduce_mean(model.loss(Y, yp))
    gv = tape.gradient(l, model.trainable_variables)
    opt.apply_gradients(zip(gv, model.trainable_variables))
    return l


for i in range(300):
    l = float(step())
    if i % 25 == 0 or i == 299:
        print(f'step {i:3d}: {l:.1f}', flush=True)

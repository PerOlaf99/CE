import sys
sys.path.insert(0, '/workspace')
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace.spectral import deconvolve

f = '/tmp/opencode/rsd/MB1000_M13_DT/A01.rsd'
rsd = RsdFile(f); tr = rsd.extract_traces()
order = rsd.metadata.channel_order
bc = BaseCaller(channel_order=order, trim=False)
call = bc.call(tr)
base = sigmod.subtract_baseline_multi(tr)
sep = deconvolve(base, None, True)
norm = sigmod.normalize_channels(sep)
sm = np.vstack([sigmod.smooth(norm[c], window=3) for c in range(4)])

# untrimmed call positions
pos = call.positions.astype(int)
n = len(pos)
print('untrimmed call len:', n, 'first pos:', pos[0], 'last pos:', pos[-1])
print('head positions 0..10:', pos[:11])
print('tail positions -11..:', pos[-11:])

# For head (read 0..115) and tail (read 585..756), assess peak separation & strength
def assess(lo, hi, label):
    seg = pos[lo:hi]
    gaps = np.diff(seg)
    med = np.median(gaps)
    h = [sm[order.index(call.bases[j]), seg[j]] if call.bases[j] in order else 0.0
         for j in range(lo, hi)]
    print(f'{label}: read[{lo}:{hi}] n={len(seg)} span={seg[-1]-seg[0]} med_gap={med:.1f} '
          f'med_h={np.median(h):.2f} q25_h={np.percentile(h,25):.2f}')

assess(0, 115, 'HEAD')
assess(585, n, 'TAIL')

# count how many peaks detectable per channel in tail trace region (last 2000 points)
for c in range(4):
    ch = sm[c]
    noise = _noise_level(ch)
    pk, props = sigmod.detect_peaks(ch[-2000:], min_distance=2,
                                    min_prominence=max(0.001, 2.0 * noise))
    print(f'tail region last 2000pts ch{order[c]}: peaks(2xnoise)={pk.size} '
          f'max_h={ch[-2000:].max():.2f}')

# Signal level profile across full trace (sum of channels), to see head/tail amplitude
total = np.sum(norm, axis=0)
print('total signal: head(first 2000pts) max=%.2f  mid max=%.2f  tail(last 2000pts) max=%.2f'
      % (total[:2000].max(), total[4000:5000].max(), total[-2000:].max()))

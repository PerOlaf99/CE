"""Round-trip tests: simulate -> write RSD -> parse -> basecall -> compare."""

import numpy as np

from megabace.basecall import BaseCaller
from megabace.rsd import RsdFile, extract_traces
from megabace.spectral import estimate_matrix, deconvolve
from megabace.simulate import (
    DEFAULT_MATRIX,
    random_sequence,
    simulate_traces,
    write_rsd,
)

TRUE_MATRIX = np.array(
    [
        [1.00, 0.20, 0.05, 0.03],
        [0.18, 1.00, 0.22, 0.06],
        [0.06, 0.24, 1.00, 0.20],
        [0.04, 0.07, 0.22, 1.00],
    ],
    dtype=np.float64,
)

ORDER = "ACGT"


def _edit_distance(a: str, b: str) -> int:
    m, n = len(a), len(b)
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1)
    dp[0, :] = np.arange(n + 1)
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + c)
    return int(dp[m, n])


def _make_fixture(tmp_path, length=600, seed=3, channel_order=ORDER):
    seq = random_sequence(length, seed=seed)
    traces, pos = simulate_traces(seq, matrix=TRUE_MATRIX, seed=seed)
    rsd_path = tmp_path / "sample.rsd"
    write_rsd(rsd_path, traces, sequence=seq, channel_order=channel_order)
    return seq, traces, rsd_path


def test_parse_layout(tmp_path):
    seq, traces, rsd_path = _make_fixture(tmp_path, length=400, seed=9)
    rsd = RsdFile(rsd_path)
    assert rsd.n_points == traces.shape[1]
    assert rsd.metadata.channel_order == ORDER
    assert rsd.metadata.sample_name == "sample"
    assert rsd.metadata.well_id == "A01"


def test_extract_recovers_traces(tmp_path):
    seq, traces, rsd_path = _make_fixture(tmp_path)
    rsd = RsdFile(rsd_path)
    got = extract_traces(rsd)
    assert got.shape == traces.shape
    err = np.mean(np.abs(got - traces)) / (np.ptp(traces) + 1e-9)
    assert err < 0.01


def test_matrix_estimation(tmp_path):
    seq, traces, rsd_path = _make_fixture(tmp_path, length=800, seed=7)
    est = estimate_matrix(traces)
    sep_true = deconvolve(traces, TRUE_MATRIX)
    sep_est = deconvolve(traces, est)
    # Estimated separation should be nearly as good as the true matrix at
    # recovering channel purity (dominant channel fraction per peak).
    def purity(sep):
        n = sep.shape[1]
        vals = sep[:, :: max(1, n // 2000)]
        dom = vals.max(axis=0)
        sec = np.sort(vals, axis=0)[-2, :]
        return float(np.mean(dom / (dom + sec + 1e-9)))

    assert purity(sep_est) > purity(sep_true) - 0.15


def test_basecall_accuracy(tmp_path):
    for seed in (1, 2, 3):
        seq, traces, rsd_path = _make_fixture(tmp_path, length=600, seed=seed)
        rsd = RsdFile(rsd_path)
        got = extract_traces(rsd)
        call = BaseCaller(
            matrix=TRUE_MATRIX, quality_scale=1.5, channel_order=ORDER
        ).call(got)
        ed = _edit_distance(seq, call.bases)
        acc = 1.0 - ed / len(seq)
        assert acc > 0.99, f"seed {seed}: accuracy {acc:.4f} too low"


def test_automatic_matrix_basecall(tmp_path):
    # Without the true matrix, rely on pure-pixel estimation.
    seq, traces, rsd_path = _make_fixture(tmp_path, length=600, seed=5)
    rsd = RsdFile(rsd_path)
    got = extract_traces(rsd)
    call = BaseCaller(estimate_matrix=True, channel_order=ORDER).call(got)
    ed = _edit_distance(seq, call.bases)
    acc = 1.0 - ed / len(seq)
    assert acc > 0.98, f"accuracy with estimated matrix {acc:.4f} too low"


def test_metadata_roundtrip(tmp_path):
    seq, traces, rsd_path = _make_fixture(tmp_path, length=50, seed=9)
    rsd = RsdFile(rsd_path)
    assert rsd.metadata.bar_code.startswith("synthetic_")
    assert "ET Terminators" in rsd.metadata.raw.decode("latin-1", "replace")
    assert len(rsd.metadata.channel_bases) == 4

#!/usr/bin/env bash
# weekend_v9.sh - headless, resumable v9 weekend training + eval.
# Run:  nohup ./weekend_v9.sh > weekend_v9.out 2>&1 &
# Resumable: each stage is skipped if its outputs already exist.
set -u
cd "$(dirname "$0")"

LOG=weekend_v9.log
TS() { date '+%Y-%m-%d %H:%M:%S'; }

step() { echo "[$(TS)] === $* ===" | tee -a "$LOG"; }

step "weekend v9 run start"
PY="python3 -B"

RESUME=${1:-auto}

# Stage 1: build adaptive-width training set (96 wells)
if [ -f v9_weekend_r0.npz ] && [ -f v9_weekend_r7.npz ]; then
  step "Stage 1 SKIP (v9_weekend_r*.npz present)"
else
  step "Stage 1 build v9 training set"
  $PY build_v9_weekend.py >> "$LOG" 2>&1
  echo "build rc=$?" | tee -a "$LOG"
fi

# Stage 2: train 8 region CNNs (resumable per region inside train_v9_weekend)
step "Stage 2 train v9 region CNNs"
$PY train_v9_weekend.py --log weekend_v9.log 2>&1 | tee -a "$LOG"
echo "train rc=$?" | tee -a "$LOG"

# Stage 3: build corr features from v9 CNNs (only if train produced models)
if [ -f base_caller_model_v9_r3.keras ] && [ ! -f corr_training_v9.npz ]; then
  step "Stage 3 build v9 corrector features"
  $PY build_corr_v9.py >> "$LOG" 2>&1
  echo "corr-set rc=$?" | tee -a "$LOG"
elif [ -f corr_training_v9.npz ]; then
  step "Stage 3 SKIP (corr_training_v9.npz present)"
else
  step "Stage 3 SKIP (v9 models not complete yet)"
fi

# Stage 4: train v9 corrector MLPs (resumable per region inside train_corr)
if [ -f corr_training_v9.npz ] && [ ! -f base_caller_model_v9_corr_r3.keras ]; then
  step "Stage 4 train v9 corrector"
  $PY train_corr.py --npz corr_training_v9.npz --prefix base_caller_model_v9_corr 2>&1 | tee -a "$LOG"
  echo "corr-train rc=$?" | tee -a "$LOG"
elif [ -f base_caller_model_v9_corr_r3.keras ]; then
  step "Stage 4 SKIP (v9 correctors present)"
else
  step "Stage 4 SKIP (no corr_training_v9.npz)"
fi

# Stage 5: full de-novo eval, CNN only, and +corr
step "Stage 5 full de-novo eval"
if [ -f base_caller_model_v9_r3.keras ]; then
  $PY eval_v9_weekend.py --prefix base_caller_model_v9 >> "$LOG" 2>&1
  echo "eval(cnn) rc=$?" | tee -a "$LOG"
fi
if [ -f base_caller_model_v9_corr_r3.keras ]; then
  $PY eval_v9_weekend.py --prefix base_caller_model_v9 --corr >> "$LOG" 2>&1
  echo "eval(+corr) rc=$?" | tee -a "$LOG"
fi

# Stage 6: local git commit (NO push; push on Monday)
step "Stage 6 git commit (local only)"
git -C .. add 02_denovo_cnn_ensemble_91.53pct/build_v9_weekend.py \
  02_denovo_cnn_ensemble_91.53pct/train_v9_weekend.py \
  02_denovo_cnn_ensemble_91.53pct/build_corr_v9.py \
  02_denovo_cnn_ensemble_91.53pct/eval_v9_weekend.py \
  02_denovo_cnn_ensemble_91.53pct/weekend_v9.sh 2>&1 | tee -a "$LOG"
git -C .. add 02_denovo_cnn_ensemble_91.53pct/weekend_v9.log 2>/dev/null
git -C .. commit -m "v9 weekend: adaptive-width jitter CNNs + corr + full de-novo eval" 2>&1 | tee -a "$LOG"
step "weekend v9 run COMPLETE"
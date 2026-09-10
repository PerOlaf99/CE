#!/usr/bin/env python3
"""
Watchdog for the per-window basecall optimizer over the weekend.

Monitors the X=700/Y=100 ('coarse') optimizer run in opt_windows_esd/:
  - ADOPTS an already-running optimize_windows_esd.py process (no duplicates).
  - If the coarse process dies BEFORE all 12 window JSONs exist -> hang/crash
    -> relaunch that run from scratch.
  - When all 12 coarse JSONs exist -> auto-launch the FINE run
    (X=100, Y=10, 81 windows) into opt_windows_fine/.
  - Detects hang: proc alive but no new JSON for HANG_MINUTES -> kill+relaunch.

Run detached once:
    setsid nohup python3 watch_optimizer.py < /dev/null > watch.log 2>&1 &
State survives because the watchdog only spawns/adopts and advances stage.
"""
import os, sys, time, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, 'opt_windows_esd')
FINE_OUTDIR = os.path.join(HERE, 'opt_windows_fine')
STAGE_LOCK = os.path.join(HERE, '.watch_stage')
HANG_MINUTES = 25

BASE_CMD = [
    sys.executable, os.path.join(HERE, 'optimize_windows_esd.py'),
    '--well', 'A01', '--method', 'greedy', '--tune-matrix', 'diag',
    '--maxiter', '40', '--popsize', '12', '--workers', '6', '--seed', '1',
]
FINE_ARGS = ['--win-size', '100', '--overlap', '10', '--min-win', '2050', '--max-win', '9350']


def count_json(d):
    return len(glob.glob(os.path.join(d, '*.json')))


def newest_json_mtime(d):
    """Newest mtime among JSONs in d. The optimizer OVERWRITES window files
    as it re-refines them, so mtime (not count) is the true activity signal."""
    files = glob.glob(os.path.join(d, '*.json'))
    if not files:
        return None
    return max(os.path.getmtime(f) for f in files)


def any_run_proc():
    out = subprocess.run(
        ['pgrep', '-f', 'optimize_windows_esd.py'], capture_output=True, text=True)
    return [int(p) for p in out.stdout.split() if p.strip()]


def log(msg):
    line = time.strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg
    print(line, flush=True)
    with open(os.path.join(HERE, 'watch.log'), 'a') as f:
        f.write(line + '\n')


def launch(cmd, outdir, runlog):
    os.makedirs(outdir, exist_ok=True)
    with open(runlog, 'w') as f:
        p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT,
                             cwd=HERE, start_new_session=True)
    log(f'launched pid {p.pid}: {" ".join(cmd[-8:])}')
    return p.pid


def stage_now():
    if os.path.exists(STAGE_LOCK):
        with open(STAGE_LOCK) as f:
            s = f.read().strip()
        if s in ('coarse', 'fine'):
            return s
    return 'coarse'


def watch_run(stage, last_json_count):
    """Ensure exactly the right process is running for `stage`. Returns (pid, alive)."""
    procs = any_run_proc()
    # right-config process = any that has the stage's min-win (coarse=2050 both, so use args)
    pids = procs
    if pids:
        pid = pids[0]
        alive = True
        log(f'({stage}) adopting running pid {pid}')
        return pid, True
    # none running -> launch for this stage
    if stage == 'coarse':
        cmd = BASE_CMD + ['--outdir', OUTDIR]
        outdir, runlog = OUTDIR, os.path.join(HERE, 'opt_esd_run.log')
        expected = 12
    else:
        cmd = BASE_CMD + FINE_ARGS + ['--outdir', FINE_OUTDIR]
        outdir, runlog = FINE_OUTDIR, os.path.join(HERE, 'opt_fine_run.log')
        expected = 81
    pid = launch(cmd, outdir, runlog)
    return pid, True


def main():
    log('=== watchdog started ===')
    stage = stage_now()
    log(f'stage={stage}')

    last_json_count = count_json(OUTDIR) if stage == 'coarse' else count_json(FINE_OUTDIR)
    last_mtime = newest_json_mtime(OUTDIR) if stage == 'coarse' else newest_json_mtime(FINE_OUTDIR)
    last_activity = time.time()
    pid, alive = watch_run(stage, last_json_count)

    while True:
        time.sleep(45)
        procs = any_run_proc()
        alive = len(procs) > 0

        outdir = OUTDIR if stage == 'coarse' else FINE_OUTDIR
        n = count_json(outdir)
        mt = newest_json_mtime(outdir)

        # mtime is the activity signal: fires on both new AND overwritten JSONs.
        if mt is not None and (last_mtime is None or mt > last_mtime):
            last_activity = time.time()

        if stage == 'coarse' and n >= 12:
            log(f'COARSE COMPLETE ({n}/12). Advancing to FINE run.')
            with open(STAGE_LOCK, 'w') as f:
                f.write('fine')
            stage = 'fine'
            last_json_count = count_json(FINE_OUTDIR)
            last_mtime = newest_json_mtime(FINE_OUTDIR)
            last_activity = time.time()
            time.sleep(2)
            pid, alive = watch_run(stage, last_json_count)
            continue
        if not alive:
            log(f'{"fine" if stage == "fine" else "coarse"} proc dead with {n}/{81 if stage == "fine" else 12} jsons -> relaunch crash/hang')
            time.sleep(3)
            last_activity = time.time()
            pid, alive = watch_run(stage, last_json_count)
        elif time.time() - last_activity > HANG_MINUTES * 60:
            log(f'{stage.upper()} HANG ({HANG_MINUTES} min no JSON write, proc alive) -> kill+relaunch')
            for p in procs:
                subprocess.run(['kill', '-9', str(p)])
            time.sleep(4)
            last_activity = time.time()
            pid, alive = watch_run(stage, last_json_count)
        last_json_count = n
        last_mtime = mt


if __name__ == '__main__':
    main()

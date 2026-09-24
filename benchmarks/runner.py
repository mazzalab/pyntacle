"""Run one argv and measure it. Knows nothing about pyntacle.

Measurement (spec section 7):
  * wall time around the child, perf_counter;
  * user/sys CPU and ru_maxrss from os.wait4 on the child -- exact for this
    child and the descendants it reaped, unlike RUSAGE_CHILDREN which is
    cumulative over the whole harness session;
  * a psutil sampler (100 ms) over the whole process tree for peak/mean CPU%
    and the *summed* RSS of all processes, which is what matters when a tool
    forks workers (old brute force uses multiprocessing);
  * I/O counters, best effort.

Limits: a wall timeout and a memory cap. The cap is enforced by the sampler
on tree RSS, not RLIMIT_AS -- address-space limits kill OpenMP/numpy
processes that reserve large virtual ranges they never touch.

Thread pinning: the child's CPU affinity is set to the CPUs it is given
(default: the first `threads` this process is allowed on -- inside a PBS
cpuset those are the job's cores), and the usual BLAS/OpenMP thread
variables are set to `threads`.
"""

import os
import shutil
import signal
import subprocess
import threading
import time

import psutil

SAMPLE_S = 0.1
TASKSET = shutil.which("taskset")
THREAD_VARS = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
               "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS")


def child_env(threads):
    env = dict(os.environ)
    for var in THREAD_VARS:
        env[var] = str(threads)
    # CPU against CPU: old imports numba.cuda
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["NUMBA_DISABLE_CUDA"] = "1"
    env["PYTHONWARNINGS"] = "ignore"
    env["MPLBACKEND"] = "Agg"
    return env


def _cpus_for(threads):
    allowed = sorted(os.sched_getaffinity(0))
    return allowed[:max(1, threads)]


def _tree(proc):
    try:
        return [proc] + proc.children(recursive=True)
    except psutil.Error:
        return [proc]


def _kill_group(pgid):
    # the child leads its own session, so its whole tree -- including workers
    # orphaned by an early exit -- shares this process group
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class _Sampler(threading.Thread):
    """Samples the child's process tree until told to stop; enforces limits."""

    def __init__(self, pid, t0, timeout_s, mem_cap_mb):
        super().__init__(daemon=True)
        self.pid, self.t0 = pid, t0
        self.timeout_s, self.cap = timeout_s, mem_cap_mb * 1024 * 1024
        self.proc = psutil.Process(pid)
        self.stop = threading.Event()
        self.peak_rss = 0
        self.cpu_samples = []
        self.io_read = self.io_write = 0
        self.status = None
        self._cpu_by_pid = {}

    def run(self):
        last_cpu, last_t = 0.0, self.t0
        while not self.stop.wait(SAMPLE_S):
            now = time.perf_counter()
            rss = 0
            for p in _tree(self.proc):
                try:
                    with p.oneshot():
                        rss += p.memory_info().rss
                        ct = p.cpu_times()
                        self._cpu_by_pid[p.pid] = ct.user + ct.system
                        try:
                            io = p.io_counters()
                            self.io_read = max(self.io_read, io.read_chars)
                            self.io_write = max(self.io_write, io.write_chars)
                        except (psutil.Error, AttributeError):
                            pass
                except psutil.Error:
                    pass
            # CPU of exited workers stays in the dict, so the total never drops
            cpu_total = sum(self._cpu_by_pid.values())
            self.peak_rss = max(self.peak_rss, rss)
            self.cpu_samples.append(100.0 * (cpu_total - last_cpu) / (now - last_t))
            last_cpu, last_t = cpu_total, now

            if rss > self.cap:
                self.status = "oom"
                _kill_group(self.pid)
                return
            if now - self.t0 > self.timeout_s:
                self.status = "timeout"
                _kill_group(self.pid)
                return


def run(argv, threads=1, timeout_s=600, mem_cap_mb=8192, cwd=None, log_path=None, cpus=None):
    """Execute argv once; return a dict of the section-7 fields.

    `cpus` pins the child to those CPUs; by default the first `threads`
    allowed ones. Pinning goes through taskset rather than preexec_fn, which
    is not safe once the caller runs several measurements from threads."""
    cpus = list(cpus) if cpus else _cpus_for(threads)
    log = open(log_path, "wb") if log_path else subprocess.DEVNULL
    if TASKSET:
        argv = [TASKSET, "-c", ",".join(map(str, cpus))] + list(argv)
    t0 = time.perf_counter()
    popen = subprocess.Popen(argv, cwd=cwd, env=child_env(threads), stdout=log,
                             stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             start_new_session=True)
    if not TASKSET:
        os.sched_setaffinity(popen.pid, cpus)
    sampler = _Sampler(popen.pid, t0, timeout_s, mem_cap_mb)
    sampler.start()
    # blocking wait: wall time is exact, not rounded up to the sampling period
    _, wstatus, ru = os.wait4(popen.pid, 0)
    wall = time.perf_counter() - t0
    sampler.stop.set()
    sampler.join()
    if log_path:
        log.close()
    popen.returncode = os.waitstatus_to_exitcode(wstatus)
    # stray workers that outlived their parent must not keep running into
    # the next measurement
    _kill_group(popen.pid)

    status = sampler.status
    if status is None:
        if popen.returncode == 0:
            status = "ok"
        elif popen.returncode == -signal.SIGKILL:
            status = "oom"  # nobody here sent it: the kernel OOM killer did
        else:
            status = "crash"

    samples = sampler.cpu_samples
    return {
        "wall_s": round(wall, 4),
        "cpu_user_s": round(ru.ru_utime, 4),
        "cpu_sys_s": round(ru.ru_stime, 4),
        "max_rss_mb": round(max(sampler.peak_rss / 1048576.0, ru.ru_maxrss / 1024.0), 1),
        "peak_cpu_pct": round(max(samples), 1) if samples else "",
        "mean_cpu_pct": round(sum(samples) / len(samples), 1) if samples else "",
        "read_bytes": sampler.io_read, "write_bytes": sampler.io_write,
        "exit_code": popen.returncode,
        "exit_status": status,
        "cpus": ",".join(map(str, cpus)),
    }

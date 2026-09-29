"""Host and process diagnostics for alert context (who + partial why)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psutil


@dataclass
class ProcessInfo:
    pid: int
    user: str
    cpu_percent: float
    memory_percent: float
    cmdline: str


@dataclass
class HostContext:
    collected_at: datetime
    load_avg: tuple[float, float, float] | None
    memory_total_gb: float
    memory_available_gb: float
    memory_percent: float
    swap_percent: float
    cpu_user: float
    cpu_system: float
    cpu_iowait: float | None
    cpu_idle: float


def _safe_username(proc: psutil.Process) -> str:
    try:
        return proc.username()
    except (psutil.Error, KeyError):
        return "?"


def _safe_cmdline(proc: psutil.Process, limit: int = 120) -> str:
    try:
        parts = proc.cmdline()
        if parts:
            text = " ".join(parts)
        else:
            text = proc.name() or f"[pid {proc.pid}]"
    except (psutil.Error, OSError):
        try:
            text = proc.name()
        except (psutil.Error, OSError):
            text = f"[pid {proc.pid}]"
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def snapshot_top_processes(
    *,
    sort_by: str = "cpu",
    limit: int = 8,
) -> list[ProcessInfo]:
    """
    Return top processes by CPU or memory.

    Does a short cpu_percent priming pass so values are meaningful.
    """
    procs: list[psutil.Process] = []
    for proc in psutil.process_iter(["pid"]):
        try:
            proc.cpu_percent(interval=None)
            procs.append(proc)
        except (psutil.Error, OSError):
            continue

    # Brief interval so cpu_percent is non-zero where applicable.
    psutil.cpu_percent(interval=0.15)

    rows: list[ProcessInfo] = []
    for proc in procs:
        try:
            with proc.oneshot():
                cpu = float(proc.cpu_percent(interval=None) or 0.0)
                mem = float(proc.memory_percent() or 0.0)
                rows.append(
                    ProcessInfo(
                        pid=proc.pid,
                        user=_safe_username(proc),
                        cpu_percent=cpu,
                        memory_percent=mem,
                        cmdline=_safe_cmdline(proc),
                    )
                )
        except (psutil.Error, OSError):
            continue

    key = (
        (lambda p: p.memory_percent)
        if sort_by == "memory"
        else (lambda p: p.cpu_percent)
    )
    rows.sort(key=key, reverse=True)
    return rows[:limit]


def snapshot_host_context() -> HostContext:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    times = psutil.cpu_times_percent(interval=0.1)
    load: tuple[float, float, float] | None
    try:
        load = tuple(psutil.getloadavg())  # type: ignore[assignment]
    except (AttributeError, OSError):
        load = None

    iowait = float(getattr(times, "iowait", 0.0)) if hasattr(times, "iowait") else None

    return HostContext(
        collected_at=datetime.now(timezone.utc),
        load_avg=load,
        memory_total_gb=vm.total / (1024**3),
        memory_available_gb=vm.available / (1024**3),
        memory_percent=float(vm.percent),
        swap_percent=float(swap.percent),
        cpu_user=float(getattr(times, "user", 0.0)),
        cpu_system=float(getattr(times, "system", 0.0)),
        cpu_iowait=iowait,
        cpu_idle=float(getattr(times, "idle", 0.0)),
    )


def format_diagnostics_for_email(metric_key: str) -> str:
    """Build who + partial-why text for an alert email body."""
    if metric_key == "memory_percent":
        sort_by = "memory"
        who_title = "Why (top processes by memory):"
    elif metric_key == "cpu_percent":
        sort_by = "cpu"
        who_title = "Why (top processes by CPU):"
    else:
        # Disk alerts: still show CPU top + host context as general pressure clues.
        sort_by = "cpu"
        who_title = "Why (top processes by CPU — host context):"

    processes = snapshot_top_processes(sort_by=sort_by, limit=8)
    host = snapshot_host_context()

    lines: list[str] = ["", who_title]
    if not processes:
        lines.append("  (no process data available)")
    else:
        lines.append(
            f"  {'PID':<8} {'CPU%':>6} {'MEM%':>6}  {'USER':<12} PROCESS"
        )
        for p in processes:
            lines.append(
                f"  {p.pid:<8} {p.cpu_percent:6.1f} {p.memory_percent:6.1f}  "
                f"{p.user:<12} {p.cmdline}"
            )

    lines.append("")
    lines.append("Host context (partial why — system clues, not app root cause):")
    if host.load_avg is not None:
        lines.append(
            f"  Load avg: {host.load_avg[0]:.2f}, {host.load_avg[1]:.2f}, {host.load_avg[2]:.2f}"
        )
    else:
        lines.append("  Load avg: n/a")
    lines.append(
        f"  Memory: {host.memory_percent:.1f}% used "
        f"({host.memory_available_gb:.2f} GiB available / {host.memory_total_gb:.2f} GiB total)"
    )
    lines.append(f"  Swap: {host.swap_percent:.1f}% used")
    iowait_txt = (
        f", iowait={host.cpu_iowait:.1f}%"
        if host.cpu_iowait is not None
        else ""
    )
    lines.append(
        f"  CPU breakdown: user={host.cpu_user:.1f}%, system={host.cpu_system:.1f}%, "
        f"idle={host.cpu_idle:.1f}%{iowait_txt}"
    )
    lines.append(f"  Snapshot at: {host.collected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    return "\n".join(lines)

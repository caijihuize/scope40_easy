"""Environment checks, Foldseek download, and soft-links to upstream data."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
from pathlib import Path

from .config import (
    AA_FASTA,
    CONDA_ENV,
    DATA_DIR,
    FOLDSEEK_BIN,
    FOLDSEEK_DIR,
    FOLDSEEK_GT_DIR,
    FOLDSEEK_TARBALL,
    FOLDSEEK_URL,
    GITHUB_RUNTIME_URL,
    GT_DI_FASTA,
    HF_RUNTIME_SRC,
    METHODS,
    MMSEQS_GT_DIR,
    PRED_FASTA_DIR,
    PRED_FASTA_SRC,
    PROJECT_ROOT,
    RUNTIME_DIR,
    RUNTIME_TARBALL,
    SCOP_LOOKUP,
    ensure_work_dirs,
    scop_cla_path,
)


def _symlink(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        if dst.resolve() == src.resolve():
            print(f"⏭️  已链接: {dst} → {src}")
            return
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.symlink_to(src.resolve())
    print(f"✅ {dst} → {src}")


def download_foldseek(skip_existing: bool = True, force: bool = False) -> Path:
    """Download Linux AVX2 Foldseek into the project and extract.

    Source (release 10-941cd33):
      https://github.com/steineggerlab/foldseek/releases/download/10-941cd33/foldseek-linux-avx2.tar.gz

    Requires CPU with AVX2 (check: grep -m1 avx2 /proc/cpuinfo).
    """
    ensure_work_dirs()

    if not force and skip_existing and FOLDSEEK_BIN.is_file() and os.access(FOLDSEEK_BIN, os.X_OK):
        print(f"⏭️  foldseek 已存在: {FOLDSEEK_BIN}")
        return FOLDSEEK_BIN

    try:
        cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="ignore")
        if "avx2" not in cpuinfo.lower():
            print("⚠️  /proc/cpuinfo 未看到 avx2；当前包为 linux-avx2，可能无法运行")
    except OSError:
        pass

    print(f"下载 Foldseek:\n  {FOLDSEEK_URL}")
    if shutil.which("wget"):
        cmd = ["wget", "-O", str(FOLDSEEK_TARBALL), FOLDSEEK_URL]
    elif shutil.which("curl"):
        cmd = ["curl", "-L", "-o", str(FOLDSEEK_TARBALL), FOLDSEEK_URL]
    else:
        raise RuntimeError("需要 wget 或 curl 以下载 foldseek")

    print("[CMD]", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
    if not FOLDSEEK_TARBALL.is_file() or FOLDSEEK_TARBALL.stat().st_size == 0:
        raise FileNotFoundError(f"下载失败或文件为空: {FOLDSEEK_TARBALL}")

    if FOLDSEEK_DIR.exists():
        if FOLDSEEK_DIR.is_symlink() or FOLDSEEK_DIR.is_file():
            FOLDSEEK_DIR.unlink()
        else:
            shutil.rmtree(FOLDSEEK_DIR)

    print(f"解压 → {PROJECT_ROOT}")
    with tarfile.open(FOLDSEEK_TARBALL, "r:gz") as tf:
        tf.extractall(path=PROJECT_ROOT)

    if not FOLDSEEK_BIN.is_file():
        raise FileNotFoundError(
            f"解压后未找到可执行文件: {FOLDSEEK_BIN}\n"
            f"请检查 tarball 内容是否含 foldseek/bin/foldseek"
        )
    FOLDSEEK_BIN.chmod(FOLDSEEK_BIN.stat().st_mode | 0o111)
    print(f"✅ foldseek: {FOLDSEEK_BIN}")
    return FOLDSEEK_BIN


def link_scope40_runtime(force: bool = False) -> Path:
    """Use local scope40_hf_dataset output, or download tarball from GitHub."""
    ensure_work_dirs()

    def _runtime_ready(root: Path) -> bool:
        return (
            (root / "FoldseekDB" / "DB").is_file()
            and (root / "fasta" / "DB_aa.fasta").is_file()
            and (root / "metadata" / "scop_lookup.tsv").is_file()
        )

    def _install_lookup(root: Path) -> None:
        packaged_lookup = root / "metadata" / "scop_lookup.tsv"
        SCOP_LOOKUP.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(packaged_lookup, SCOP_LOOKUP)
        print(f"✅ SCOP lookup → {SCOP_LOOKUP}")

    # 1) Prefer local Git checkout of scope40_hf_dataset
    if _runtime_ready(HF_RUNTIME_SRC):
        if force and RUNTIME_DIR.exists():
            if RUNTIME_DIR.is_symlink() or RUNTIME_DIR.is_file():
                RUNTIME_DIR.unlink()
            else:
                shutil.rmtree(RUNTIME_DIR)
        _symlink(HF_RUNTIME_SRC, RUNTIME_DIR)
        _install_lookup(HF_RUNTIME_SRC)
        print(f"✅ SCOPe40 runtime (local): {RUNTIME_DIR}")
        return RUNTIME_DIR

    # 2) Already extracted / linked under data/
    if not force and _runtime_ready(RUNTIME_DIR):
        _install_lookup(RUNTIME_DIR)
        print(f"⏭️  SCOPe40 runtime 已存在: {RUNTIME_DIR}")
        return RUNTIME_DIR

    # 3) Backup: download output/scope40_runtime.tar.gz from GitHub
    print(f"本地未找到 {HF_RUNTIME_SRC}")
    print(f"改为从 GitHub 下载:\n  {GITHUB_RUNTIME_URL}")
    if shutil.which("wget"):
        cmd = ["wget", "-O", str(RUNTIME_TARBALL), GITHUB_RUNTIME_URL]
    elif shutil.which("curl"):
        cmd = ["curl", "-L", "-o", str(RUNTIME_TARBALL), GITHUB_RUNTIME_URL]
    else:
        raise RuntimeError("需要 wget 或 curl 以下载 runtime 包")
    print("[CMD]", " ".join(cmd))
    subprocess.run(cmd, check=True)
    if not RUNTIME_TARBALL.is_file() or RUNTIME_TARBALL.stat().st_size == 0:
        raise FileNotFoundError(f"下载失败或文件为空: {RUNTIME_TARBALL}")

    if RUNTIME_DIR.exists():
        if RUNTIME_DIR.is_symlink() or RUNTIME_DIR.is_file():
            RUNTIME_DIR.unlink()
        else:
            shutil.rmtree(RUNTIME_DIR)

    print(f"解压 → {DATA_DIR}")
    with tarfile.open(RUNTIME_TARBALL, "r:gz") as tf:
        root = DATA_DIR.resolve()
        for member in tf.getmembers():
            destination = (DATA_DIR / member.name).resolve()
            if root not in destination.parents and destination != root:
                raise RuntimeError(f"不安全的归档路径: {member.name}")
        tf.extractall(DATA_DIR)

    if not _runtime_ready(RUNTIME_DIR):
        raise FileNotFoundError(
            f"GitHub 运行包解压后不完整: {RUNTIME_DIR}\n"
            f"请检查 {GITHUB_RUNTIME_URL}"
        )
    _install_lookup(RUNTIME_DIR)
    print(f"✅ SCOPe40 runtime (GitHub): {RUNTIME_DIR}")
    return RUNTIME_DIR


def link_prediction_fastas() -> None:
    """Link model-predicted 3Di FASTA (AA→3Di on DB_aa.fasta) into data/pred_fasta/."""
    ensure_work_dirs()
    source_dir = PRED_FASTA_SRC
    if not source_dir.is_dir():
        raise FileNotFoundError(
            f"缺少模型预测目录: {source_dir}\n"
            "请将各模型对 DB_aa.fasta 预测得到的 *aa2di.fasta 放到该目录，"
            "或设置环境变量 PRED_FASTA_DIR。"
        )
    for _label, _key, filename in METHODS:
        if filename is None:
            continue
        source = source_dir / filename
        if not source.is_file():
            raise FileNotFoundError(f"缺少模型预测 FASTA: {source}")
        _symlink(source, PRED_FASTA_DIR / filename)


def check_environment() -> dict[str, bool]:
    """Print dependency status; return ok flags."""
    status: dict[str, bool] = {}

    print(f"PROJECT_ROOT = {PROJECT_ROOT}")
    print(f"CONDA_DEFAULT_ENV = {os.environ.get('CONDA_DEFAULT_ENV', '(unset)')}")
    print(f"期望 conda env   = {CONDA_ENV}")
    print(f"runtime src      = {HF_RUNTIME_SRC}")
    print(f"GitHub backup   = {GITHUB_RUNTIME_URL}")
    print(f"pred fasta src   = {PRED_FASTA_SRC}")

    try:
        import Bio  # noqa: F401

        status["biopython"] = True
        print("✅ biopython")
    except ImportError:
        status["biopython"] = False
        print("❌ biopython 缺失")

    try:
        import pandas  # noqa: F401
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401

        status["pandas_mpl"] = True
        print("✅ pandas / matplotlib / numpy")
    except ImportError as e:
        status["pandas_mpl"] = False
        print(f"❌ {e}")

    status["foldseek"] = FOLDSEEK_BIN.is_file() and os.access(FOLDSEEK_BIN, os.X_OK)
    print(("✅" if status["foldseek"] else "❌") + f" foldseek: {FOLDSEEK_BIN}")

    status["scop_lookup"] = SCOP_LOOKUP.is_file()
    print(
        ("✅" if status["scop_lookup"] else "❌")
        + f" SCOP lookup: {SCOP_LOOKUP}"
    )

    cla = scop_cla_path()
    status["scop_cla"] = cla.is_file()
    print(("✅" if status["scop_cla"] else "❌") + f" SCOP cla: {cla}")

    status["aa_fasta"] = AA_FASTA.is_file()
    print(("✅" if status["aa_fasta"] else "❌") + f" AA FASTA: {AA_FASTA}")

    status["gt_di_fasta"] = GT_DI_FASTA.is_file()
    print(("✅" if status["gt_di_fasta"] else "❌") + f" GT 3Di FASTA: {GT_DI_FASTA}")

    mmseqs_ok = (MMSEQS_GT_DIR / "DB").is_file()
    print(
        ("✅" if mmseqs_ok else "⚠️ ")
        + f" MMseqsDB (optional): {MMSEQS_GT_DIR / 'DB'}"
    )

    for label, key, di_name in METHODS:
        if di_name is None:
            ok = (FOLDSEEK_GT_DIR / "DB").is_file()
            print(("✅" if ok else "❌") + f" {label}: FoldseekDB/DB")
            status[f"input_{key}"] = ok
        else:
            path = PRED_FASTA_DIR / di_name
            ok = path.is_file()
            print(("✅" if ok else "❌") + f" {label}: {path}")
            status[f"input_{key}"] = ok

    if status["foldseek"]:
        try:
            r = subprocess.run(
                [str(FOLDSEEK_BIN), "version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            ver = (r.stdout or r.stderr or "").strip().splitlines()[:1]
            if ver:
                print(f"   foldseek version: {ver[0]}")
        except Exception as e:
            print(f"   foldseek version 检查失败: {e}")

    return status

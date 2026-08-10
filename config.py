"""Shared paths, methods, and defaults for scope40_easy notebooks."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
HOME = PROJECT_ROOT.parent

TEMP = PROJECT_ROOT / "tmp"
WORK_DIR = PROJECT_ROOT / "work"
BIN_DIR = PROJECT_ROOT / "bin"
WORK_TMP_DIR = WORK_DIR / "tmp"

# Ground-truth sequences (from 0.prepare) — user model inputs
GT_FASTA_DIR = WORK_DIR / "GT_fasta"
AA_FASTA = GT_FASTA_DIR / "DB_aa.fasta"
GT_DI_FASTA = GT_FASTA_DIR / "DB_di.fasta"

# User translation outputs
AA2DI_FASTA_DIR = WORK_DIR / "aa2di_fasta"  # AA → 3Di (used by current benchmark)
DI2AA_FASTA_DIR = WORK_DIR / "di2aa_fasta"  # 3Di → AA (reserved; not in eval yet)

# Comparison databases
DBS_DIR = WORK_DIR / "DB"
FOLDSEEK_GT_DIR = DBS_DIR / "foldseek_DB"
MMSEQS_GT_DIR = DBS_DIR / "mmseqs_DB"

# SCOPe id → class (only label file kept from prepare)
LABEL_DIR = WORK_DIR / "lable"
SCOP_LOOKUP = LABEL_DIR / "scop_lookup.tsv"

ALN_DIR = WORK_DIR / "aln"
METRICS_DIR = WORK_DIR / "metrics"
FIGURES_DIR = WORK_DIR / "figures"
TRANSLATION_METRICS_DIR = METRICS_DIR / "translation"

# Optional portable bundle written by 0.prepare
WORK_BUNDLE = WORK_DIR / "scope40_work_bundle.tar.gz"

# Project-wide binaries
FOLDSEEK_BIN = BIN_DIR / "foldseek"
MMSEQS_BIN = BIN_DIR / "mmseqs"

FOLDSEEK_URL = (
    "https://github.com/steineggerlab/foldseek/releases/download/"
    "10-941cd33/foldseek-linux-avx2.tar.gz"
)
MMSEQS_URL = (
    "https://github.com/soedinglab/MMseqs2/releases/download/"
    "18-8cc5c/mmseqs-linux-avx2.tar.gz"
)

FOLDSEEK_TMP_DIR = TEMP / "foldseek"
MMSEQS_TMP_DIR = TEMP / "mmseqs"
FOLDSEEK_TARBALL = TEMP / "foldseek-linux-avx2.tar.gz"
MMSEQS_TARBALL = TEMP / "mmseqs-linux-avx2.tar.gz"

SCOP_CLA_NAME = "dir.cla.scope.2.08-stable.txt"
SCOP_CLA_FALLBACK = HOME / "SCOPE" / SCOP_CLA_NAME

# Legacy GitHub runtime (old layout); 1.init can migrate into work/
GITHUB_RUNTIME_URL = os.environ.get(
    "SCOPE40_RUNTIME_URL",
    "https://github.com/caijihuize/scope40_hf_dataset/raw/master/output/scope40_runtime.tar.gz",
)
LEGACY_RUNTIME_TARBALL = TEMP / "scope40_runtime.tar.gz"

HF_BASE = "https://huggingface.co/datasets/caijihuize/scope40_pdbstyle/resolve/main"

# (display_name, method_key, engine, di_fasta under aa2di_fasta/, or None for GT)
# engine: "foldseek" | "mmseqs"
METHODS: list[tuple[str, str, str, str | None]] = [
    ("Foldseek (AA+3Di)", "foldseek", "foldseek", None),
    ("MMseqs2", "mmseqs", "mmseqs", None),
    ("ESM3-3Di", "ESM3", "foldseek", "DB_ESM3_aa2di.fasta"),
    ("ESM3-LoRA", "ESM3_LoRA", "foldseek", "DB_ESM3_LoRA_aa2di.fasta"),
    ("ProstT5 (translate)", "ProstT5", "foldseek", "DB_ProstT5_translate_aa2di.fasta"),
    ("SaProt", "SaProt", "foldseek", "DB_SaProt_aa2di.fasta"),
]

# Translation accuracy eval (aa2di / di2aa vs GT_fasta)
# (display_name, method_key, aa2di_fasta under aa2di_fasta/, di2aa_fasta under di2aa_fasta/)
TRANSLATION_METHODS: list[tuple[str, str, str, str]] = [
    ("ESM3-3Di", "ESM3", "DB_ESM3_aa2di.fasta", "DB_ESM3_di2aa.fasta"),
    ("ESM3-LoRA", "ESM3_LoRA", "DB_ESM3_LoRA_aa2di.fasta", "DB_ESM3_LoRA_di2aa.fasta"),
    (
        "ProstT5 (translate)",
        "ProstT5",
        "DB_ProstT5_translate_aa2di.fasta",
        "DB_ProstT5_translate_di2aa.fasta",
    ),
    ("SaProt", "SaProt", "DB_SaProt_aa2di.fasta", "DB_SaProt_di2aa.fasta"),
]

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")

PALETTE = {
    "Foldseek (AA+3Di)": "#2b5c8f",
    "MMseqs2": "#666666",
    "ESM3-3Di": "#d95f02",
    "ESM3-LoRA": "#1b9e77",
    "ProstT5 (translate)": "#7570b3",
    "SaProt": "#e7298a",
}

EASY_SEARCH_PARAMS = {
    "sensitivity": 9.5,
    "max_seqs": 2000,
    "evalue": 10.0,
    "threads": 64,
}

CONDA_ENV = "ESM3_3Di_5090"
PREPARE_THREADS = 16


def require_project_root(marker: str) -> Path:
    """Ensure the notebook is launched from the project root."""
    cwd = Path.cwd()
    if (cwd / marker).is_file():
        if cwd.resolve() != PROJECT_ROOT:
            print(f"⚠️  cwd={cwd} 与 config.PROJECT_ROOT={PROJECT_ROOT} 不一致，使用 PROJECT_ROOT")
        return PROJECT_ROOT
    if (PROJECT_ROOT / marker).is_file():
        print(f"⚠️  cwd 不是项目根目录 ({cwd})，改用 {PROJECT_ROOT}")
        return PROJECT_ROOT
    raise SystemExit(
        f"请在项目根目录启动 notebook（需存在 {marker}），当前 cwd: {cwd}"
    )


def db_prefix(method_key: str) -> Path:
    return DBS_DIR / f"{method_key}_DB" / "DB"


def aln_tsv(method_key: str) -> Path:
    return ALN_DIR / f"{method_key}_easy.tsv"


def aln_tmp_dir(method_key: str) -> Path:
    return WORK_TMP_DIR / f"easy_{method_key}"


def metric_prefix(method_key: str) -> Path:
    return METRICS_DIR / f"{method_key}_easy"


def translation_per_seq_path(task: str, method_key: str) -> Path:
    return TRANSLATION_METRICS_DIR / f"{task}_{method_key}_per_seq.tsv"


def translation_summary_path(task: str) -> Path:
    return TRANSLATION_METRICS_DIR / f"{task}_summary.csv"


def method_by_key(method_key: str) -> tuple[str, str, str, str | None]:
    for row in METHODS:
        if row[1] == method_key:
            return row
    raise KeyError(f"未知 method_key: {method_key}")


def method_engine(method_key: str) -> str:
    return method_by_key(method_key)[2]


def predicted_fasta_names() -> list[str]:
    return [name for *_rest, name in METHODS if name is not None]


def scop_cla_path() -> Path:
    for path in (
        TEMP / SCOP_CLA_NAME,
        SCOP_CLA_FALLBACK,
    ):
        if path.is_file():
            return path
    return TEMP / SCOP_CLA_NAME


def work_ready() -> bool:
    """True if 0.prepare (or migrated runtime) has installed GT assets."""
    return (
        (FOLDSEEK_GT_DIR / "DB").is_file()
        and (MMSEQS_GT_DIR / "DB").is_file()
        and AA_FASTA.is_file()
        and GT_DI_FASTA.is_file()
        and SCOP_LOOKUP.is_file()
    )


def ensure_work_dirs() -> None:
    for d in (
        TEMP,
        BIN_DIR,
        GT_FASTA_DIR,
        AA2DI_FASTA_DIR,
        DI2AA_FASTA_DIR,
        DBS_DIR,
        LABEL_DIR,
        ALN_DIR,
        METRICS_DIR,
        TRANSLATION_METRICS_DIR,
        FIGURES_DIR,
        WORK_TMP_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


def cleanup_tmp(*, also_work_tmp: bool = True) -> None:
    """Remove download/build temp dirs at the end of a notebook run."""
    import shutil

    targets = [TEMP]
    if also_work_tmp:
        targets.append(WORK_TMP_DIR)
    for path in targets:
        if path.exists():
            shutil.rmtree(path)
            print(f"🧹 已清理: {path}")
        else:
            print(f"⏭️  无需清理: {path}")

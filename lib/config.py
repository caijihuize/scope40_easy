"""Paths, methods, and easy-search defaults for scope40_easy."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HOME = PROJECT_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"

# Upstream: prepared runtime from scope40_hf_dataset (local clone preferred)
SCOPE40_HF = HOME / "scope40_hf_dataset"
HF_RUNTIME_SRC = SCOPE40_HF / "output" / "scope40_runtime"

# Backup: download runtime tarball from GitHub if local clone is absent
GITHUB_REPO = os.environ.get(
    "SCOPE40_HF_GITHUB", "https://github.com/caijihuize/scope40_hf_dataset"
)
GITHUB_REF = os.environ.get("SCOPE40_HF_REF", "master")
GITHUB_RUNTIME_URL = os.environ.get(
    "SCOPE40_RUNTIME_URL",
    f"{GITHUB_REPO}/raw/{GITHUB_REF}/output/scope40_runtime.tar.gz",
)
RUNTIME_TARBALL = DATA_DIR / "scope40_runtime.tar.gz"

# Model AA→3Di predictions (input was DB_aa.fasta)
NEW_SCOPE40 = HOME / "new_scope40"
PRED_FASTA_SRC = Path(os.environ.get("PRED_FASTA_DIR", str(NEW_SCOPE40 / "fasta")))

RUNTIME_DIR = DATA_DIR / "scope40_runtime"  # local link or extracted copy
FASTA_DIR = RUNTIME_DIR / "fasta"
FOLDSEEK_GT_DIR = RUNTIME_DIR / "FoldseekDB"
MMSEQS_GT_DIR = RUNTIME_DIR / "MMseqsDB"
PRED_FASTA_DIR = DATA_DIR / "pred_fasta"  # symlinks to model di.fasta

# Foldseek binary (downloaded in 1.init; Linux AVX2 build)
FOLDSEEK_DIR = PROJECT_ROOT / "foldseek"
FOLDSEEK_BIN = FOLDSEEK_DIR / "bin" / "foldseek"
FOLDSEEK_TARBALL = PROJECT_ROOT / "foldseek-linux-avx2.tar.gz"
FOLDSEEK_URL = (
    "https://github.com/steineggerlab/foldseek/releases/download/"
    "10-941cd33/foldseek-linux-avx2.tar.gz"
)

WORK_DIR = PROJECT_ROOT / "work"
DBS_DIR = WORK_DIR / "dbs"
ALN_DIR = WORK_DIR / "aln"
METRICS_DIR = WORK_DIR / "metrics"
FIGURES_DIR = WORK_DIR / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"

AA_FASTA = FASTA_DIR / "DB_aa.fasta"
GT_DI_FASTA = FASTA_DIR / "DB_di.fasta"
SCOP_LOOKUP = METRICS_DIR / "scop_lookup.tsv"
SCOP_CLA_NAME = "dir.cla.scope.2.08-stable.txt"
SCOP_CLA_FALLBACK = HOME / "SCOPE" / SCOP_CLA_NAME

# (display_name, method_key, predicted 3Di fasta under pred_fasta/, or None for GT)
METHODS: list[tuple[str, str, str | None]] = [
    ("Foldseek (AA+3Di)", "foldseek", None),
    ("ESM3-3Di", "ESM3", "DB_ESM3_aa2di.fasta"),
    ("ESM3-LoRA", "ESM3_LoRA", "DB_ESM3_LoRA_aa2di.fasta"),
    ("ProstT5 (translate)", "ProstT5", "DB_ProstT5_translate_aa2di.fasta"),
    ("SaProt", "SaProt", "DB_SaProt_aa2di.fasta"),
]

PALETTE = {
    "Foldseek (AA+3Di)": "#2b5c8f",
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


def db_prefix(method_key: str) -> Path:
    return DBS_DIR / f"{method_key}_DB" / "DB"


def aln_tsv(method_key: str) -> Path:
    return ALN_DIR / f"{method_key}_easy.tsv"


def aln_tmp_dir(method_key: str) -> Path:
    return WORK_DIR / "tmp" / f"easy_{method_key}"


def metric_prefix(method_key: str) -> Path:
    return METRICS_DIR / f"{method_key}_easy"


def scop_cla_path() -> Path:
    for path in (
        RUNTIME_DIR / "metadata" / SCOP_CLA_NAME,
        HF_RUNTIME_SRC / "metadata" / SCOP_CLA_NAME,
        SCOP_CLA_FALLBACK,
    ):
        if path.is_file():
            return path
    return SCOP_CLA_FALLBACK


def ensure_work_dirs() -> None:
    for d in (
        DATA_DIR,
        PRED_FASTA_DIR,
        DBS_DIR,
        ALN_DIR,
        METRICS_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        WORK_DIR / "tmp",
    ):
        d.mkdir(parents=True, exist_ok=True)

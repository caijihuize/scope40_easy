"""Build Foldseek databases from AA + 3Di FASTA (tsv2db)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .config import (
    AA_FASTA,
    DBS_DIR,
    FOLDSEEK_BIN,
    FOLDSEEK_GT_DIR,
    METHODS,
    PRED_FASTA_DIR,
    db_prefix,
    ensure_work_dirs,
)

def _seqio():
    try:
        from Bio import SeqIO
    except ImportError as e:
        raise SystemExit("需要 Biopython: pip install biopython") from e
    return SeqIO


def _read_fasta_dict(path: Path) -> dict[str, str]:
    SeqIO = _seqio()
    out: dict[str, str] = {}
    for record in SeqIO.parse(path, "fasta"):
        out[record.id] = str(record.seq)
    return out


def build_tsvs(aa_fasta: Path, di_fasta: Path, tmp_dir: Path) -> None:
    SeqIO = _seqio()
    sequences_aa = _read_fasta_dict(aa_fasta)
    sequences_3di: dict[str, str] = {}
    for record in SeqIO.parse(di_fasta, "fasta"):
        if record.id not in sequences_aa:
            print(
                f"Warning: ignoring 3Di entry {record.id}, "
                "since it is not in the amino-acid FASTA file"
            )
        else:
            sequences_3di[record.id] = str(record.seq).upper()

    for seq_id in sequences_aa:
        if seq_id not in sequences_3di:
            raise SystemExit(
                f"Error: entry {seq_id} in amino-acid FASTA has no corresponding 3Di string"
            )

    aa_tsv = tmp_dir / "aa.tsv"
    di_tsv = tmp_dir / "3di.tsv"
    header_tsv = tmp_dir / "header.tsv"
    with aa_tsv.open("w", encoding="utf-8") as faa, di_tsv.open(
        "w", encoding="utf-8"
    ) as fdi, header_tsv.open("w", encoding="utf-8") as fh:
        for i, seq_id in enumerate(sequences_aa.keys(), start=1):
            idx = str(i)
            faa.write(f"{idx}\t{sequences_aa[seq_id]}\n")
            fdi.write(f"{idx}\t{sequences_3di[seq_id]}\n")
            fh.write(f"{idx}\t{seq_id}\n")


def run_tsv2db(foldseek_bin: Path, db_out: Path, tmp_dir: Path) -> None:
    cmds = [
        [str(foldseek_bin), "tsv2db", str(tmp_dir / "aa.tsv"), str(db_out), "--output-dbtype", "0"],
        [
            str(foldseek_bin),
            "tsv2db",
            str(tmp_dir / "3di.tsv"),
            f"{db_out}_ss",
            "--output-dbtype",
            "0",
        ],
        [
            str(foldseek_bin),
            "tsv2db",
            str(tmp_dir / "header.tsv"),
            f"{db_out}_h",
            "--output-dbtype",
            "12",
        ],
    ]
    for cmd in cmds:
        print("[CMD]", " ".join(cmd))
        subprocess.run(cmd, check=True)


def build_one(
    aa_fasta: Path,
    di_fasta: Path,
    db_out: Path,
    foldseek_bin: Path | None = None,
    skip_existing: bool = True,
) -> Path:
    foldseek_bin = Path(foldseek_bin or FOLDSEEK_BIN)
    if skip_existing and db_out.is_file():
        print(f"⏭️  DB 已存在，跳过: {db_out}")
        return db_out
    if not foldseek_bin.is_file():
        raise FileNotFoundError(f"foldseek 不存在: {foldseek_bin}")
    if not aa_fasta.is_file():
        raise FileNotFoundError(f"AA FASTA 不存在: {aa_fasta}")
    if not di_fasta.is_file():
        raise FileNotFoundError(f"3Di FASTA 不存在: {di_fasta}")

    db_out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scope40_easy_db_") as tmp:
        tmp_dir = Path(tmp)
        build_tsvs(aa_fasta, di_fasta, tmp_dir)
        run_tsv2db(foldseek_bin, db_out, tmp_dir)
    print(f"✅ Foldseek DB: {db_out}")
    return db_out


def link_foldseek_gt(skip_existing: bool = True) -> Path:
    """Soft-link structural Foldseek DB into work/dbs/foldseek_DB."""
    ensure_work_dirs()
    dest = DBS_DIR / "foldseek_DB"
    src = FOLDSEEK_GT_DIR
    marker = dest / "DB"
    if skip_existing and marker.is_file():
        print(f"⏭️  foldseek GT DB 已就绪: {marker}")
        return marker
    if not (src / "DB").is_file():
        raise FileNotFoundError(f"结构真值 FoldseekDB 不存在: {src / 'DB'}")
    if dest.is_symlink() or dest.exists():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            # replace incomplete dir with symlink
            import shutil

            shutil.rmtree(dest)
    dest.symlink_to(src.resolve())
    if not marker.is_file():
        raise FileNotFoundError(f"软链后仍找不到: {marker}")
    print(f"✅ 软链 FoldseekDB → {dest}")
    return marker


def build_all(skip_existing: bool = True) -> dict[str, Path]:
    """Build / link all method DBs. Returns method_key → DB path."""
    ensure_work_dirs()
    out: dict[str, Path] = {}
    out["foldseek"] = link_foldseek_gt(skip_existing=skip_existing)

    for _label, key, di_name in METHODS:
        if di_name is None:
            continue
        di_fasta = PRED_FASTA_DIR / di_name
        path = build_one(
            AA_FASTA,
            di_fasta,
            db_prefix(key),
            skip_existing=skip_existing,
        )
        out[key] = path
    return out

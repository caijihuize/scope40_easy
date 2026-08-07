"""Foldseek easy-search wrapper (SCOPe40 remote homology)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config import (
    EASY_SEARCH_PARAMS,
    FOLDSEEK_BIN,
    METHODS,
    aln_tmp_dir,
    aln_tsv,
    db_prefix,
    ensure_work_dirs,
)


def easy_search(
    query_db: Path,
    output_tsv: Path,
    tmp_dir: Path,
    target_db: Path | None = None,
    foldseek_bin: Path | None = None,
    threads: int | None = None,
    skip_existing: bool = True,
) -> Path:
    """Run foldseek easy-search; query == target by default."""
    foldseek_bin = Path(foldseek_bin or FOLDSEEK_BIN)
    target_db = Path(target_db or query_db)
    threads = int(threads if threads is not None else EASY_SEARCH_PARAMS["threads"])

    if skip_existing and output_tsv.is_file() and output_tsv.stat().st_size > 0:
        print(f"⏭️  比对已存在，跳过: {output_tsv} ({output_tsv.stat().st_size} bytes)")
        return output_tsv

    if not foldseek_bin.is_file():
        raise FileNotFoundError(f"foldseek 不存在: {foldseek_bin}")
    if not query_db.is_file():
        raise FileNotFoundError(f"query DB 不存在: {query_db}")
    if not target_db.is_file():
        raise FileNotFoundError(f"target DB 不存在: {target_db}")

    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(foldseek_bin),
        "easy-search",
        str(query_db),
        str(target_db),
        str(output_tsv),
        str(tmp_dir),
        "--threads",
        str(threads),
        "-s",
        str(EASY_SEARCH_PARAMS["sensitivity"]),
        "--max-seqs",
        str(EASY_SEARCH_PARAMS["max_seqs"]),
        "-e",
        str(EASY_SEARCH_PARAMS["evalue"]),
    ]
    print("[CMD]", " ".join(cmd))
    subprocess.run(cmd, check=True)

    if not output_tsv.is_file():
        raise FileNotFoundError(f"结果未生成: {output_tsv}")
    print(f"✅ {output_tsv}  行数≈检查 wc -l")
    return output_tsv


def search_one(method_key: str, skip_existing: bool = True, threads: int | None = None) -> Path:
    ensure_work_dirs()
    return easy_search(
        query_db=db_prefix(method_key),
        output_tsv=aln_tsv(method_key),
        tmp_dir=aln_tmp_dir(method_key),
        skip_existing=skip_existing,
        threads=threads,
    )


def search_all(skip_existing: bool = True, threads: int | None = None) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for _label, key, _di in METHODS:
        print(f"\n══ easy-search: {key} ══")
        out[key] = search_one(key, skip_existing=skip_existing, threads=threads)
    return out

"""scope_family-style remote homology evaluation (easy-search only)."""

from __future__ import annotations

import gc
import re
import traceback
from pathlib import Path

import pandas as pd

from .config import (
    AA_FASTA,
    METHODS,
    METRICS_DIR,
    SCOP_LOOKUP,
    aln_tsv,
    ensure_work_dirs,
    metric_prefix,
    scop_cla_path,
)


def remove_family_number(scop_class: str) -> str:
    return re.sub(r"\.[0-9]+$", "", scop_class)


def resolve_scop_class(qid: str, id2cls: dict[str, str]) -> str | None:
    """Exact match → strip _MODEL_* → multi-chain fallback dXXXX.N_X → dXXXX.N."""
    candidates: list[str] = [qid]
    base_model = re.sub(r"_MODEL_.*", "", qid)
    if base_model != qid:
        candidates.append(base_model)

    for cand in list(candidates):
        if "." in cand:
            base_chain = re.sub(r"_[A-Za-z0-9]+$", "", cand)
            if base_chain != cand:
                candidates.append(base_chain)

    for cand in candidates:
        if cand in id2cls:
            return id2cls[cand]
    return None


def build_scop_lookup(
    scop_cla: Path | None = None,
    fasta_file: Path | None = None,
    scop_lookup: Path | None = None,
    skip_existing: bool = True,
) -> Path:
    scop_cla = Path(scop_cla or scop_cla_path())
    fasta_file = Path(fasta_file or AA_FASTA)
    scop_lookup = Path(scop_lookup or SCOP_LOOKUP)
    ensure_work_dirs()

    if skip_existing and scop_lookup.is_file() and scop_lookup.stat().st_size > 0:
        print(f"⏭️  SCOP lookup 已存在: {scop_lookup}")
        return scop_lookup

    id2cls: dict[str, str] = {}
    with scop_cla.open() as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 4:
                id2cls[parts[0].strip()] = parts[3].strip()
    print(f"从 dir.cla 读取了 {len(id2cls)} 个 domain")

    all_ids: set[str] = set()
    with fasta_file.open() as f:
        for line in f:
            if line.startswith(">"):
                qid = line[1:].strip().split()[0]
                if qid:
                    all_ids.add(qid)
    print(f"FASTA 中共有 {len(all_ids)} 个唯一 ID")

    missed = 0
    with scop_lookup.open("w") as out:
        for qid in sorted(all_ids):
            cls = resolve_scop_class(qid, id2cls)
            if cls is None:
                missed += 1
                continue
            out.write(f"{qid}\t{cls}\n")
    print(f"✅ {scop_lookup}  匹配={len(all_ids) - missed} 未匹配={missed}")
    return scop_lookup


def load_scop_levels(scop_lookup: Path | None = None) -> pd.DataFrame:
    scop_lookup = Path(scop_lookup or SCOP_LOOKUP)
    rows = []
    with scop_lookup.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            fam = parts[1].strip()
            sf = remove_family_number(fam)
            fo = remove_family_number(sf)
            rows.append({"id": parts[0].strip(), "fa": fam, "sf": sf, "fo": fo})
    return pd.DataFrame(rows)


def calc_fp_rates(aln_tsv_path: Path, cla: pd.DataFrame, out_prefix: Path) -> dict[str, Path]:
    """Sensitivity up to first wrong-fold FP; exclude self-hits."""
    print(f"  读取比对: {aln_tsv_path}", flush=True)
    aln = pd.read_csv(
        aln_tsv_path,
        sep="\t",
        header=None,
        usecols=[0, 1],
        names=["qid", "tid"],
        dtype=str,
    )
    print(f"  原始行数: {len(aln):,}", flush=True)
    aln = aln[aln["qid"] != aln["tid"]].copy()
    print(f"  去 self-hit 后: {len(aln):,}", flush=True)

    work = aln.merge(cla, left_on="qid", right_on="id", how="inner")
    work = work.rename(columns={"fo": "qfo", "sf": "qsf", "fa": "qfa"}).drop(columns=["id"])
    work = work.merge(cla, left_on="tid", right_on="id", how="left")
    work = work.rename(columns={"fo": "tfo", "sf": "tsf", "fa": "tfa"}).drop(columns=["id"])

    is_wrong_fold = (work["qfo"] != work["tfo"]).fillna(True)
    work["seen_fp"] = (
        is_wrong_fold.groupby(work["qid"], sort=False).cumsum().gt(0).astype("int8")
    )

    same_fo = work["qfo"] == work["tfo"]
    same_sf = work["qsf"] == work["tsf"]
    same_fa = work["qfa"] == work["tfa"]

    count_fold = (same_fo & ~same_sf).astype("int32")
    count_super = (same_fo & same_sf & ~same_fa).astype("int32")
    count_family = (same_fo & same_sf & same_fa).astype("int32")

    before_fp = 1 - work["seen_fp"]
    work["fold_tp"] = count_fold * before_fp
    work["super_tp"] = count_super * before_fp
    work["family_tp"] = count_family * before_fp
    work["count_fold"] = count_fold
    work["count_super"] = count_super
    work["count_family"] = count_family

    agg = (
        work.groupby("qid", sort=False)
        .agg(
            focnt=("fold_tp", "sum"),
            fotot=("count_fold", "sum"),
            sfcnt=("super_tp", "sum"),
            sftot=("count_super", "sum"),
            facnt=("family_tp", "sum"),
            fatot=("count_family", "sum"),
        )
        .reset_index()
    )

    for tot in ("fotot", "sftot", "fatot"):
        agg[tot] = agg[tot].replace(0, 1)

    agg["fofrac"] = agg["focnt"] / agg["fotot"]
    agg["sfrac"] = agg["sfcnt"] / agg["sftot"]
    agg["fafrac"] = agg["facnt"] / agg["fatot"]

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "fol": Path(str(out_prefix) + "_fol.tsv"),
        "sup": Path(str(out_prefix) + "_sup.tsv"),
        "fam": Path(str(out_prefix) + "_fam.tsv"),
    }
    agg[["qid", "focnt", "fotot", "fofrac"]].to_csv(
        paths["fol"], sep="\t", header=False, index=False
    )
    agg[["qid", "sfcnt", "sftot", "sfrac"]].to_csv(
        paths["sup"], sep="\t", header=False, index=False
    )
    agg[["qid", "facnt", "fatot", "fafrac"]].to_csv(
        paths["fam"], sep="\t", header=False, index=False
    )
    return paths


def mean_sensitivity(level_tsv: Path) -> float:
    vals = []
    with level_tsv.open() as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 4:
                vals.append(float(parts[3]))
    return sum(vals) / len(vals) if vals else 0.0


def evaluate_all(skip_existing: bool = True) -> pd.DataFrame:
    """Compute fam/sup/fol tables and write auc_easy.csv."""
    ensure_work_dirs()
    build_scop_lookup(skip_existing=skip_existing)
    cla = load_scop_levels()
    print(f"SCOP levels: {len(cla)}")

    auc_rows: list[dict] = []
    for level_name, level_key in (("Family", "fam"), ("Superfamily", "sup"), ("Fold", "fol")):
        row: dict[str, float | str] = {"search_mode": "easy", "level": level_name}
        for label, key, _di in METHODS:
            tsv_path = aln_tsv(key)
            out_prefix = metric_prefix(key)
            fam_path = Path(str(out_prefix) + "_fam.tsv")
            level_path = Path(str(out_prefix) + f"_{level_key}.tsv")

            print(f"\n[easy] {label}")
            if not tsv_path.is_file():
                print(f"  ❌ 缺少比对: {tsv_path}")
                continue

            if not (skip_existing and fam_path.is_file() and fam_path.stat().st_size > 0):
                if level_name == "Family":
                    try:
                        calc_fp_rates(tsv_path, cla, out_prefix)
                        print("  ✅ 写入 fam/sup/fol")
                    except Exception as e:
                        print(f"  ❌ {e}")
                        traceback.print_exc()
                        continue
                    finally:
                        gc.collect()
            else:
                if level_name == "Family":
                    print("  ⏭️  评估已存在")

            if level_path.is_file():
                row[label] = mean_sensitivity(level_path)
                print(f"  {level_name} AUC={row[label]:.4f}")
        auc_rows.append(row)

    df = pd.DataFrame(auc_rows)
    csv_path = METRICS_DIR / "auc_easy.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ AUC CSV: {csv_path}")
    return df

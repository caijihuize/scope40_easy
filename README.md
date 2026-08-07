# scope40_easy

SCOPe40（SCOPe 2.08，序列同一性 ≤ 40%）上，用 **Foldseek easy-search** 评估不同 **AA→3Di** 编码的远程同源检测表现。

本仓库是 [`new_scope40`](../new_scope40) 的精简重实现：**只做 easy-search**；入口为三个 notebook。

## 输入

对比实验需要两类输入：

| 来源 | 内容 |
|------|------|
| SCOPe40 runtime | FoldseekDB、`DB_aa.fasta` / `DB_di.fasta`、`scop_lookup.tsv`、可选 MMseqsDB |
| 各模型预测目录（默认 [`new_scope40/fasta`](../new_scope40/fasta)） | 以 `DB_aa.fasta` 为输入预测得到的 `*aa2di.fasta` |

**Runtime 获取顺序：**

1. 本地仓库 [`../scope40_hf_dataset/output/scope40_runtime`](../scope40_hf_dataset/output/scope40_runtime)（优先软链）
2. 若本地不存在，则从 GitHub 下载备用包：

```text
https://github.com/caijihuize/scope40_hf_dataset/raw/master/output/scope40_runtime.tar.gz
```

可用环境变量覆盖：

- `SCOPE40_RUNTIME_URL`：完整 tarball URL
- `SCOPE40_HF_GITHUB` / `SCOPE40_HF_REF`：默认仓库与分支（`master`）
- `PRED_FASTA_DIR`：模型预测 FASTA 目录


## 目录

```text
scope40_easy/
├── README.md
├── 1.init.ipynb          # Foldseek + 链接数据 + 建库
├── 2.benchmark.ipynb     # easy-search → 灵敏度表 → AUC CSV
├── 3.plot.ipynb          # AUROC1 图
├── lib/
├── foldseek/             # 1.init 下载解压
├── data/
│   ├── scope40_runtime → ../scope40_hf_dataset/output/scope40_runtime
│   └── pred_fasta/       # 各模型 *aa2di.fasta 软链
├── work/                 # db / aln / metrics / figures
└── logs/
```

## 流程

```text
scope40_hf_dataset/output ──┐
                            ├─→ 1.init（链接 + 建 DB）→ 2.benchmark → 3.plot
模型预测 *aa2di.fasta ──────┘
```

1. `1.init`：下载 Foldseek；链接 runtime 与预测 FASTA；构建各方法 Foldseek DB  
2. `2.benchmark`：easy-search（同库自比）→ scope_family 评估 → `auc_easy.csv`  
3. `3.plot`：AUROC1（Family / Superfamily / Fold）

### 对比方法

| 名称 | 3Di 来源 |
|------|----------|
| Foldseek (AA+3Di) | 结构真值 `FoldseekDB` |
| ESM3-3Di | `DB_ESM3_aa2di.fasta` |
| ESM3-LoRA | `DB_ESM3_LoRA_aa2di.fasta` |
| ProstT5 (translate) | `DB_ProstT5_translate_aa2di.fasta` |
| SaProt | `DB_SaProt_aa2di.fasta` |

搜索参数（对齐 `new_scope40`）：`-s 9.5 --max-seqs 2000 -e 10`，query = target。

### 评估协议（scope_family）

1. 跳过 self-hit  
2. 第一个 **wrong fold** 视为 FP，其后不再计 TP  
3. Family / Superfamily / Fold 灵敏度；AUC = 各 query 灵敏度均值  

## 快速开始

先完成 [`scope40_hf_dataset`](../scope40_hf_dataset) 的构建并 push，或直接使用 GitHub 上的
`output/scope40_runtime.tar.gz`。

```bash
cd /hpcfs/fhome/caihuize/scope40_easy
conda activate ESM3_3Di_5090
# 可选：export PRED_FASTA_DIR=/path/to/predicted_aa2di_fastas
# 可选：export SCOPE40_RUNTIME_URL=https://github.com/caijihuize/scope40_hf_dataset/raw/master/output/scope40_runtime.tar.gz
jupyter lab
```

按顺序运行：

1. [`1.init.ipynb`](1.init.ipynb)  
2. [`2.benchmark.ipynb`](2.benchmark.ipynb)  
3. [`3.plot.ipynb`](3.plot.ipynb)  

产物：

| 路径 | 说明 |
|------|------|
| `work/dbs/{method}_DB/` | Foldseek 库 |
| `work/aln/{method}_easy.tsv` | easy-search 比对 |
| `work/metrics/*_{fam,sup,fol}.tsv` | 各层级灵敏度 |
| `work/metrics/auc_easy.csv` | AUC 汇总 |
| `work/figures/auroc1_easy.png` | AUROC1 图 |

已有产物默认跳过；强制重跑时设 `SKIP_EXISTING = False`。

## 依赖

| 依赖 | 说明 |
|------|------|
| Conda | `ESM3_3Di_5090` |
| Python | biopython、pandas、numpy、matplotlib |
| Foldseek | `1.init` 下载 Linux AVX2 到 `./foldseek/` |
| SCOPe40 runtime | 本地 `../scope40_hf_dataset/output/scope40_runtime`，或 GitHub tarball 备用下载 |
| 模型预测 | 默认 `../new_scope40/fasta`（`*aa2di.fasta`） |

## 参考结果（easy，来自 new_scope40）

| Method | Family | Superfamily | Fold |
|--------|--------|-------------|------|
| Foldseek (AA+3Di) | 0.735 | 0.631 | 0.081 |
| ProstT5 (translate) | 0.708 | 0.589 | 0.055 |
| ESM3-LoRA | 0.698 | 0.582 | 0.051 |
| ESM3-3Di | 0.698 | 0.582 | 0.055 |
| SaProt | 0.458 | 0.343 | 0.024 |

## 相关

- 运行包构建：[`scope40_hf_dataset`](../scope40_hf_dataset)  
- 完整版（含 exhaustive）：[`new_scope40`](../new_scope40)  

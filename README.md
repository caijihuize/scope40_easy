# scope40_easy

在 **SCOPe40**（SCOPe 2.08，序列同一性 ≤ 40%）上，用 **easy-search** 评估远程同源检测表现：

- 结构真值：Foldseek (AA+3Di)、MMseqs2
- 预测 3Di：ESM3-3Di、ESM3-LoRA、ProstT5、SaProt

入口为五个 notebook；路径 / 方法表 / 搜索参数见 [`config.py`](config.py)。

## 流程

```text
0.prepare → work/{GT_fasta, DB, lable} + bin/
                ↓
用户读 GT_fasta，跑模型 → work/aa2di_fasta/ 、work/di2aa_fasta/（可选）
                ↓
      1.init → 2.a.benchmark / 2.b.translation_eval（只写 metrics）
                ↓
                    3.plot（AUROC + translation 图）
```

各 notebook 结尾会清理 `tmp/` 与 `work/tmp/`；正式产物保留在 `work/` 与 `bin/`。

## 目录

```text
scope40_easy/
├── README.md
├── config.py                 # 共享配置
├── environment.yml
├── requirements.txt
├── 0.prepare.ipynb           # 下载 / 建 GT 库 / 写标签
├── 1.init.ipynb              # 检查预测 FASTA、建预测库
├── 2.a.benchmark.ipynb       # easy-search + 评估（写出 metrics）
├── 2.b.translation_eval.ipynb # AA↔3Di 预测 vs GT 准确度
├── 3.plot.ipynb              # AUROC1 + translation 图
├── bin/                      # foldseek, mmseqs（gitignore）
├── tmp/                      # 中间产物，notebook 结尾清理（gitignore）
└── work/
    ├── GT_fasta/             # DB_aa.fasta, DB_di.fasta
    ├── lable/                # 仅 scop_lookup.tsv
    ├── DB/                   # foldseek_DB / mmseqs_DB / 各预测库
    ├── aa2di_fasta/          # 【用户】AA→3Di（见该目录 README）
    ├── di2aa_fasta/          # 【用户】3Di→AA（见该目录 README）
    ├── aln/                  # easy-search 结果
    ├── metrics/              # 灵敏度表、auc_easy.csv；translation/ 序列表
    └── figures/              # AUROC1 图；translation_accuracy.png
```

## 各 notebook 输入 / 输出

### `0.prepare.ipynb`

| | 内容 |
|--|------|
| 输入 | 无本地业务文件；下载 Foldseek / MMseqs / SCOPe40 结构与分类 |
| 输出 | `bin/foldseek`、`bin/mmseqs` |
| | `work/GT_fasta/DB_aa.fasta`、`DB_di.fasta` |
| | `work/DB/foldseek_DB/`、`work/DB/mmseqs_DB/` |
| | `work/lable/scop_lookup.tsv` |
| | 可选：`work/scope40_work_bundle.tar.gz` |

### `1.init.ipynb`

| | 内容 |
|--|------|
| 输入 | 上一步的 `work/GT_*`、`work/DB/{foldseek,mmseqs}_DB`、`work/lable/`、`bin/` |
| | 用户：`work/aa2di_fasta/*aa2di.fasta` |
| 输出 | `work/DB/{ESM3,ESM3_LoRA,ProstT5,SaProt}_DB/` |

若本地尚无 `0.prepare` 产物，可设 `SCOPE40_RUNTIME_URL` 下载旧 runtime 并自动迁移到当前 `work/` 布局（`bin/mmseqs` 仍建议由 `0.prepare` 安装）。

### `2.a.benchmark.ipynb`

| | 内容 |
|--|------|
| 输入 | `work/DB/*`、`bin/{foldseek,mmseqs}`、`work/lable/scop_lookup.tsv` |
| 输出 | `work/aln/{method}_easy.tsv` |
| | `work/metrics/{method}_easy_{fam,sup,fol}.tsv` |
| | `work/metrics/auc_easy.csv`（汇总；`3.plot` 会按曲线重算并刷新） |

### `2.b.translation_eval.ipynb`

| | 内容 |
|--|------|
| 输入 | `work/GT_fasta/DB_aa.fasta`、`DB_di.fasta` |
| | 用户：`work/aa2di_fasta/*aa2di.fasta`、`work/di2aa_fasta/*di2aa.fasta`（成对方法见 `config.TRANSLATION_METHODS`） |
| 输出 | `work/metrics/translation/{task}_{method}_per_seq.tsv` |
| | `work/metrics/translation/{aa2di,di2aa}_summary.csv`、`translation_summary.csv` |

默认 `SKIP_LENGTH_MISMATCH = True`：预测与 GT 长度不一致的序列不计入 micro/macro accuracy（仍统计 length mismatch 数量）。**图在 `3.plot.ipynb`。**

### `3.plot.ipynb`

| | 内容 |
|--|------|
| 输入 | `work/metrics/*_{fam,sup,fol}.tsv`（来自 2.a） |
| | `work/metrics/translation/translation_summary.csv`（来自 2.b，可选） |
| 输出 | `work/figures/auroc1_easy.png`（并刷新 `auc_easy.csv`） |
| | `work/figures/translation_accuracy.png`（有 translation 汇总时） |

## 用户预测输入

以 `work/GT_fasta/DB_aa.fasta` 为输入跑模型后，将结果复制到 `work/aa2di_fasta/`：

| 方法 | 文件名 |
|------|--------|
| ESM3-3Di | `DB_ESM3_aa2di.fasta` |
| ESM3-LoRA | `DB_ESM3_LoRA_aa2di.fasta` |
| ProstT5 (translate) | `DB_ProstT5_translate_aa2di.fasta` |
| SaProt | `DB_SaProt_aa2di.fasta` |

详见 [`work/aa2di_fasta/README.md`](work/aa2di_fasta/README.md)。  
3Di→AA 对称命名与评估见 [`work/di2aa_fasta/README.md`](work/di2aa_fasta/README.md)。  
新增方法：改 [`config.py`](config.py) 的 `METHODS` / `PALETTE`（及 `TRANSLATION_METHODS`），并放入对应 fasta。

## 对比方法与搜索

| 名称 | 引擎 | 库 / 输入 |
|------|------|-----------|
| Foldseek (AA+3Di) | Foldseek | `work/DB/foldseek_DB` |
| MMseqs2 | MMseqs2 | `work/DB/mmseqs_DB` + `bin/mmseqs` |
| ESM3-3Di | Foldseek | `work/aa2di_fasta/DB_ESM3_aa2di.fasta` → 建库 |
| ESM3-LoRA | Foldseek | `work/aa2di_fasta/DB_ESM3_LoRA_aa2di.fasta` → 建库 |
| ProstT5 (translate) | Foldseek | `work/aa2di_fasta/DB_ProstT5_translate_aa2di.fasta` → 建库 |
| SaProt | Foldseek | `work/aa2di_fasta/DB_SaProt_aa2di.fasta` → 建库 |

参数（对齐 `new_scope40` easy）：`-s 9.5 --max-seqs 2000 -e 10`，query = target。

### 评估协议（scope_family）

1. 跳过 self-hit  
2. 第一个 **wrong fold** 视为 FP，其后不再计 TP  
3. Family / Superfamily / Fold 灵敏度；AUC = 各 query 灵敏度均值  

## 快速开始

```bash
cd /path/to/scope40_easy
conda env create -f environment.yml   # 或已有环境：conda activate ESM3_3Di_5090
conda activate ESM3_3Di_5090

# 1) 运行 0.prepare.ipynb
# 2) 放入预测 FASTA
cp /path/to/DB_ESM3_aa2di.fasta work/aa2di_fasta/
cp /path/to/DB_ESM3_LoRA_aa2di.fasta work/aa2di_fasta/
cp /path/to/DB_ProstT5_translate_aa2di.fasta work/aa2di_fasta/
cp /path/to/DB_SaProt_aa2di.fasta work/aa2di_fasta/
# 可选：di2aa 预测（用于 2.b.translation_eval）
cp /path/to/DB_ESM3_di2aa.fasta work/di2aa_fasta/
# … 其余方法见 work/di2aa_fasta/README.md

# 3) 1.init → 2.a.benchmark → 2.b.translation_eval（后者可选，顺序可互换）
# 4) 3.plot.ipynb 统一作图
jupyter lab
```

Kernel 名：`ESM3_3Di_5090`。已有产物默认跳过；强制重跑设 `SKIP_EXISTING = False`。

## 依赖

| 依赖 | 说明 |
|------|------|
| Conda | `ESM3_3Di_5090`（`environment.yml`） |
| Python | biopython、pandas、numpy、matplotlib（`requirements.txt`） |
| Foldseek / MMseqs2 | `0.prepare` 安装到 `bin/`（Linux AVX2） |
| 模型预测 | 用户复制到 `work/aa2di_fasta/`、`work/di2aa_fasta/` |

## 参考结果（easy，来自 new_scope40；MMseqs2 为本项目新增）

| Method | Family | Superfamily | Fold |
|--------|--------|-------------|------|
| Foldseek (AA+3Di) | 0.735 | 0.631 | 0.081 |
| MMseqs2 | — | — | — |
| ProstT5 (translate) | 0.708 | 0.589 | 0.055 |
| ESM3-LoRA | 0.698 | 0.582 | 0.051 |
| ESM3-3Di | 0.698 | 0.582 | 0.055 |
| SaProt | 0.458 | 0.343 | 0.024 |

## 相关

- 完整版（含 exhaustive）：[`new_scope40`](../new_scope40)

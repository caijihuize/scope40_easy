# scope40_easy

在 **SCOPe40**（SCOPe 2.08，序列同一性 ≤ 40%）上评估远程同源检测：

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
├── 2.a.benchmark.ipynb       # Foldseek easy-search / MMseqs search + 评估
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
    ├── aln/                  # 全库自比对 TSV
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
| 搜索 | Foldseek / 预测方法：`foldseek easy-search`（可直接吃库） |
| | MMseqs2：`mmseqs search` + `convertalis`（`easy-search` 只接受 FASTA，不能传 DB） |

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

参数（query = target，默认 64 线程）。2.a 请在计算节点跑。

| 方法 | 搜索 | 灵敏度协议 |
|------|------|------------|
| Foldseek / 预测 3Di | `easy-search -s 9.5 --max-seqs 2000 -e 10`（对齐 `new_scope40` easy） | **hitlist**：分母 = 比对 TSV 里出现的同类 hit |
| MMseqs2 | `search -a -s 7.5 --max-seqs 2000 -e 10000`（对齐 `foldseek-analysis` `runMMseqs.sh`） | **catalog**：`bench.noselfhit.awk`，分母 = 库内该层级全部同源 |

### 评估协议

两边都：跳过 self-hit；第一个 **wrong fold** 视为 FP，其后不再计 TP；Family / Superfamily / Fold 互斥计数；AUC = 各 query 灵敏度均值。

MMseqs2 额外对齐 foldseek-analysis：

1. 分母是库内全部同源（漏检算 FN），不是 TSV 内 hit 数  
2. 只平均同时具有 family、远程 superfamily、远程 fold 成员的 query  
3. 零命中的有效 query 记灵敏度为 0  

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
# 4) 3.plot.ipynb 统一作图（需 matplotlib；或用下面命令出图）
jupyter lab --no-browser --ip=0.0.0.0
```

**Kernel 必须是 `ESM3_3Di_5090` 的 Python**（`~/.conda/envs/ESM3_3Di_5090/bin/python`，3.10）。第一格打印 `sys.executable` 确认。集群自带的 `miniforge3/.../python3.12` 没有 biopython / matplotlib，不要在那上面 pip。

已有 Foldseek / 预测方法产物默认跳过；强制重跑设 `SKIP_EXISTING = False`。  
MMseqs2 在改用 foldseek-analysis 参数后，`2.a` 里 `MMSEQS_SKIP_EXISTING = False`（会重搜）；跑完一次后可改回 `True`。图写入 `work/figures/`。

## 依赖

| 依赖 | 说明 |
|------|------|
| Conda | `ESM3_3Di_5090`（`environment.yml`） |
| Python | biopython、pandas、numpy、matplotlib（`requirements.txt`） |
| Foldseek / MMseqs2 | `0.prepare` 安装到 `bin/`（Linux AVX2） |
| 模型预测 | 用户复制到 `work/aa2di_fasta/`、`work/di2aa_fasta/` |

## 结果（本仓库 easy，SCOPe40 13,920 domains）

来源：`work/metrics/auc_easy.csv`（2026-08-18）。图：[`work/figures/auroc1_easy.png`](work/figures/auroc1_easy.png)。AUC = 各 query 灵敏度均值。

| Method | Family | Superfamily | Fold |
|--------|--------|-------------|------|
| Foldseek (AA+3Di) | 0.735 | 0.631 | 0.080 |
| ProstT5 (translate) | 0.708 | 0.589 | 0.055 |
| ESM3-LoRA | 0.699 | 0.582 | 0.051 |
| ESM3-3Di | 0.695 | 0.582 | 0.054 |
| MMseqs2 | （待重跑） | （待重跑） | （待重跑） |
| SaProt | 0.458 | 0.344 | 0.024 |

Foldseek / 预测 3Di 与 `new_scope40` easy 参考值一致。  
MMseqs2 已改为 foldseek-analysis 的搜索参数与 catalog 灵敏度协议，需重跑 `2.a.benchmark.ipynb` 后更新本表。

### Translation accuracy（预测 vs GT）

来源：`work/metrics/translation/translation_summary.csv`。图：[`work/figures/translation_accuracy.png`](work/figures/translation_accuracy.png)。micro accuracy；长度不一致已跳过（ESM3 aa2di 13 条，ProstT5 双向各 3 条）。

| Method | AA→3Di | 3Di→AA |
|--------|--------|--------|
| ProstT5 (translate) | 0.670 | 0.372 |
| ESM3-LoRA | 0.656 | 0.393 |
| ESM3-3Di | 0.604 | 0.234 |
| SaProt | 0.409 | 0.413 |

## 相关

- 完整版（含 exhaustive）：[`new_scope40`](../new_scope40)

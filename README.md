# scope40_easy

在 **SCOPe40**（SCOPe 2.08，序列同一性 ≤ 40%，**13,920** domains）上复现远程同源检测与 AA↔3Di 翻译准确度。检索为全库自比对（`query = target`）。

实验代码就是 **五本 notebook**。没有 `config.py`。打开任意一本都能看到同一套超参。

## 软件与硬件

| 项目 | 钉死版本 |
|------|----------|
| Conda | `ESM3_3Di_5090`（`environment.yml`） |
| Python | 3.10，`~/.conda/envs/ESM3_3Di_5090/bin/python` |
| Foldseek | `10-941cd33` Linux AVX2 → `bin/foldseek` |
| MMseqs2 | `18-8cc5c` Linux AVX2 → `bin/mmseqs` |
| GPU | 不需要 |
| `0_prepare` / `1_build` / `2b` / `3_figures` | 登录节点即可 |
| `2a_remote_homology` | **CPU 计算节点**，默认 64 线程；串行，墙钟数小时 |

Kernel **必须**是 `ESM3_3Di_5090`。集群自带的 `miniforge3` Python 3.12 没有依赖，不要在上面 pip。解释器路径不含该环境名时，notebook 会立刻退出。

```bash
cd /path/to/scope40_easy
conda env create -f environment.yml   # 或已有环境：conda activate ESM3_3Di_5090
conda activate ESM3_3Di_5090
jupyter lab --no-browser --ip=0.0.0.0
```

## 两条灵敏度协议（不要混成同一个 AUC）

| 方法 | 搜索 | 协议 |
|------|------|------|
| Foldseek / 预测 3Di | `easy-search -s 9.5 --max-seqs 2000 -e 10` | **hitlist**：分母 = 比对 TSV 里的同类 hit（对齐 `new_scope40`） |
| MMseqs2 | `search -a -s 7.5 --max-seqs 2000 -e 10000` 再 `convertalis` | **catalog**：`bench.noselfhit.awk`；分母 = 库内全部同源；只平均同时有 family、远程 sfam、远程 fold 成员的 query；零命中记 0 |

共用规则：跳过 self-hit；第一个 wrong-fold 为 FP；Family / Superfamily / Fold 互斥计数；AUC = 各 query 灵敏度均值。

`3_figures.ipynb` 里 MMseqs2 用**虚线**，图例带 `[catalog]`。

## 五本 notebook（按此顺序）

骨架统一：Title → Environment → **Configuration** → Run flags → Helpers → Steps → Verify → Cleanup。

**Configuration 在五本中字节级相同。** 改方法表或搜索参数：只改 `0_prepare_scope40.ipynb` 这一格，再整格复制到另外四本。

| 文件 | 对应论文 | 节点 | 墙钟 |
|------|----------|------|------|
| `0_prepare_scope40.ipynb` | Dataset construction | 登录，16 线程 | 约 30–60 min |
| `1_build_predicted_dbs.ipynb` | Predicted 3Di libraries | 登录 | 约 10 min |
| `2a_remote_homology.ipynb` | SCOPe remote homology | **计算节点**，64 线程 | 数小时，串行 |
| `2b_translation_accuracy.ipynb` | AA↔3Di accuracy | 登录 | 数分钟 |
| `3_figures.ipynb` | Figures / tables | 登录 | 数秒 |

`0_prepare` 之后，`2a` 与 `2b` 可互换（2b 不依赖预测库）。Cleanup 只删 `tmp/` 与 `work/tmp/`。

同源检索只用 **AA→3Di**；翻译评估是 **双向**。

## 放置预测 FASTA

跑完 `0_prepare` 后，以 `work/GT_fasta/DB_aa.fasta`（di2aa 用 `DB_di.fasta`）为输入跑模型，再复制：

```bash
cp /path/to/DB_ESM3_aa2di.fasta              work/aa2di_fasta/
cp /path/to/DB_ESM3_LoRA_aa2di.fasta         work/aa2di_fasta/
cp /path/to/DB_ProstT5_translate_aa2di.fasta work/aa2di_fasta/
cp /path/to/DB_SaProt_aa2di.fasta            work/aa2di_fasta/

cp /path/to/DB_ESM3_di2aa.fasta              work/di2aa_fasta/
cp /path/to/DB_ESM3_LoRA_di2aa.fasta         work/di2aa_fasta/
cp /path/to/DB_ProstT5_translate_di2aa.fasta work/di2aa_fasta/
cp /path/to/DB_SaProt_di2aa.fasta            work/di2aa_fasta/
```

FASTA header 必须与 `DB_aa.fasta` 一致。然后跑 `1_build_predicted_dbs.ipynb`。

新增方法：改 `0_prepare_scope40.ipynb` Configuration 里的 `METHODS` / `TRANSLATION_METHODS` / `PALETTE`，复制到另外四本，并放入对应 FASTA。

## 目录

```text
scope40_easy/
├── README.md
├── environment.yml
├── requirements.txt
├── 0_prepare_scope40.ipynb
├── 1_build_predicted_dbs.ipynb
├── 2a_remote_homology.ipynb
├── 2b_translation_accuracy.ipynb
├── 3_figures.ipynb
├── bin/                      # foldseek, mmseqs（gitignore）
├── tmp/                      # 各 notebook 结尾清理
└── work/
    ├── GT_fasta/             # DB_aa.fasta, DB_di.fasta
    ├── labels/               # scop_lookup.tsv
    ├── DB/                   # foldseek_DB / mmseqs_DB / 预测库
    ├── aa2di_fasta/          # 【用户】AA→3Di
    ├── di2aa_fasta/          # 【用户】3Di→AA
    ├── aln/                  # {method}_easy.tsv + .meta.json
    ├── metrics/              # 灵敏度表、auc_easy.csv、translation/
    └── figures/              # auroc1_easy.png/.pdf、translation_accuracy.png/.pdf
```

## 与论文图表对应

| 文中内容 | 文件 |
|----------|------|
| Family / Superfamily / Fold AUC 表 | `work/metrics/auc_easy.csv`（`3_figures` 会按曲线刷新） |
| AUROC1 图 | `work/figures/auroc1_easy.png`（及 `.pdf`） |
| 翻译准确度表 | `work/metrics/translation/translation_summary.csv` |
| 翻译准确度图 | `work/figures/translation_accuracy.png`（及 `.pdf`） |

`SKIP_EXISTING = True` 会跳过已有产物。检索参数写在 `{aln}.meta.json`：参数变了会自动重搜。没有指纹的 MMseqs TSV 视为过期（catalog 协议）。全部重跑设 `SKIP_EXISTING = False`。

## 常见失败

| 现象 | 原因 |
|------|------|
| Environment 格直接退出 | Kernel 不是 `ESM3_3Di_5090` |
| `Missing ... Run 0_prepare_scope40.ipynb` | 没跑 prepare |
| 1_build 缺 `DB_*_aa2di.fasta` | 预测 FASTA 未复制或文件名不对 |
| 2a 极慢或被杀 | 在登录节点跑；改到计算节点，或把 `THREADS` 调小 |
| MMseqs AUC 看起来像 Foldseek | 把 hitlist 与 catalog 混成同一指标 |
| Foldseek 二进制无法运行 | CPU 无 AVX2 |

## 结果（本仓库快照）

来源：`work/metrics/auc_easy.csv`（2026-08-18）。AUC = 各 query 灵敏度均值。

| Method | Protocol | Family | Superfamily | Fold |
|--------|----------|--------|-------------|------|
| Foldseek (AA+3Di) | hitlist | 0.735 | 0.631 | 0.080 |
| ProstT5 (translate) | hitlist | 0.708 | 0.589 | 0.055 |
| ESM3-LoRA | hitlist | 0.699 | 0.582 | 0.051 |
| ESM3-3Di | hitlist | 0.695 | 0.582 | 0.054 |
| SaProt | hitlist | 0.458 | 0.344 | 0.024 |
| MMseqs2 | catalog | （待重跑 2a） | （待重跑 2a） | （待重跑 2a） |

Foldseek / 预测 3Di 与 `new_scope40` easy 参考值一致。MMseqs2 改为 foldseek-analysis 的 `-s 7.5 -e 10000` 与 catalog 协议后需重搜；没有 `mmseqs_easy.tsv.meta.json` 时，`2a` 会自动重跑 MMseqs。

### Translation accuracy（micro；长度不一致已跳过）

| Method | AA→3Di | 3Di→AA |
|--------|--------|--------|
| ProstT5 (translate) | 0.670 | 0.372 |
| ESM3-LoRA | 0.656 | 0.393 |
| ESM3-3Di | 0.604 | 0.234 |
| SaProt | 0.409 | 0.413 |

长度不一致已跳过：ESM3 aa2di 13 条，ProstT5 双向各 3 条。

## 相关

含 exhaustive 的完整流程：[`new_scope40`](../new_scope40)。

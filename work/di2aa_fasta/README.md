# 3Di → AA 预测结果

以 `work/GT_fasta/DB_di.fasta` 为输入跑模型后，将预测的 AA FASTA **复制到本目录**。

## 文件名（与 aa2di 对称）

| 方法 | 文件名 |
|------|--------|
| ESM3-3Di | `DB_ESM3_di2aa.fasta` |
| ESM3-LoRA | `DB_ESM3_LoRA_di2aa.fasta` |
| ProstT5 (translate) | `DB_ProstT5_translate_di2aa.fasta` |
| SaProt | `DB_SaProt_di2aa.fasta` |

评估：运行 [`2.b.translation_eval.ipynb`](../2.b.translation_eval.ipynb)，与 `GT_fasta/DB_aa.fasta` 比较 micro/macro accuracy；图见 [`3.plot.ipynb`](../3.plot.ipynb)。

**easy-search 基准当前不使用 di2aa 建库**；本目录用于序列准确度评估。

# AA → 3Di 预测结果

请先运行 `0.prepare.ipynb`，再以 `work/GT_fasta/DB_aa.fasta` 为输入跑你的模型，把预测的 3Di FASTA **复制到本目录**。

## 当前基准需要的文件

| 对比方法 | 文件名 |
|----------|--------|
| ESM3-3Di | `DB_ESM3_aa2di.fasta` |
| ESM3-LoRA | `DB_ESM3_LoRA_aa2di.fasta` |
| ProstT5 (translate) | `DB_ProstT5_translate_aa2di.fasta` |
| SaProt | `DB_SaProt_aa2di.fasta` |

```bash
cp /path/to/DB_ESM3_aa2di.fasta work/aa2di_fasta/
# ...
```

然后运行 `1.init.ipynb` 建库；序列准确度见 [`2.b.translation_eval.ipynb`](../2.b.translation_eval.ipynb)，作图见 [`3.plot.ipynb`](../3.plot.ipynb)。

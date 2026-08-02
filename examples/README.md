# Examples

| File | What it is |
|---|---|
| `wave1_ask.txt` | Sample `ragmod ask` answer + citations |
| `savings_table.md` | Latest A/B bench table (regenerate with `ragmod bench`) |
| `savings_table.json` | Machine-readable bench rows |

Regenerate the table (proxy must be running):

```bash
ragmod bench --repo . --out examples/savings_table.md
```

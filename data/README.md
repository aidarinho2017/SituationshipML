# Generated training data

Training CSV files are intentionally not distributed with this repository because the upstream dataset does not declare redistribution terms.

To recreate the public English splits and machine-translated Russian/Kazakh splits:

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python download_data.py
.venv/bin/python translate_data.py
```

Source: [ieuniversity/flirty_or_not](https://huggingface.co/datasets/ieuniversity/flirty_or_not). Review its current terms before downloading or redistributing the data.

`data/private/` is reserved for local review CSVs and is ignored by Git.

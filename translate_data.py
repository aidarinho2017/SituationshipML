import csv
import hashlib
import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


MODEL_NAME = "facebook/nllb-200-distilled-600M"
DATA_DIR = Path(__file__).parent / "data"
SOURCE_DIR = DATA_DIR / "english"
CACHE_DIR = DATA_DIR / ".translation_cache"
SPLITS = ("train", "validation", "test")
TARGETS = {"ru": "rus_Cyrl", "kk": "kaz_Cyrl"}
BATCH_SIZE = 32


def translate(texts, tokenizer, model, target_language, device):
    translations = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        inputs = tokenizer(
            batch, return_tensors="pt", padding=True, truncation=True, max_length=512
        ).to(device)
        with torch.inference_mode():
            tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_language),
                max_new_tokens=128,
                num_beams=4,
                no_repeat_ngram_size=3,
                repetition_penalty=1.15,
            )
        decoded = tokenizer.batch_decode(tokens, skip_special_tokens=True)
        translations.extend(
            translated if translated.strip() else source
            for source, translated in zip(batch, decoded)
        )
        print(f"  {target_language}: {min(start + BATCH_SIZE, len(texts))}/{len(texts)}")
    return translations


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["id", "label", "texts"]:
            raise ValueError(f"Unexpected columns in {path}: {reader.fieldnames}")
        return list(reader)


def write_multilingual(path, source_rows, translations):
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "label", "texts", "language"])
        writer.writeheader()
        for index, source in enumerate(source_rows):
            writer.writerow({**source, "language": "en"})
            for language in TARGETS:
                writer.writerow(
                    {**source, "texts": translations[language][index], "language": language}
                )
    os.replace(temporary, path)


def cached_translation(split, language, code, texts, tokenizer, model, device):
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{split}.{language}.json"
    digest = hashlib.sha256(json.dumps(texts, ensure_ascii=False).encode()).hexdigest()
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached["model"] == MODEL_NAME and cached["source"] == digest:
            print(f"  {code}: loaded from cache")
            return cached["translations"]

    translations = translate(texts, tokenizer, model, code, device)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {"model": MODEL_NAME, "source": digest, "translations": translations},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return translations


def main():
    missing = [split for split in SPLITS if not (SOURCE_DIR / f"{split}.csv").is_file()]
    if missing:
        raise FileNotFoundError(
            f"Missing English splits: {', '.join(missing)}. Run download_data.py first."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.float16 if device.type == "cuda" else torch.float32
    print(f"Loading {MODEL_NAME} on {device}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang="eng_Latn")
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, dtype=dtype).to(device)
    model.eval()

    for split in SPLITS:
        rows = read_rows(SOURCE_DIR / f"{split}.csv")
        texts = [row["texts"] for row in rows]
        print(f"{split}: {len(rows)} English rows")
        translated = {
            language: cached_translation(
                split, language, code, texts, tokenizer, model, device
            )
            for language, code in TARGETS.items()
        }
        assert all(len(values) == len(rows) for values in translated.values())
        output = DATA_DIR / f"{split}.csv"
        write_multilingual(output, rows, translated)
        print(f"  saved {len(rows) * 3} rows to {output}")


if __name__ == "__main__":
    main()

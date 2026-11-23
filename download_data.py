from pathlib import Path

from datasets import load_dataset


DATASET_NAME = "ieuniversity/flirty_or_not"
SPLITS = ("train", "validation", "test")
DATA_DIR = Path(__file__).parent / "data" / "english"


def main() -> None:
    dataset = load_dataset(DATASET_NAME)
    missing = set(SPLITS) - set(dataset)
    if missing:
        raise RuntimeError(f"Dataset is missing splits: {', '.join(sorted(missing))}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        frame = dataset[split].to_pandas()
        output = DATA_DIR / f"{split}.csv"
        frame.to_csv(output, index=False)

        print(f"{split}: shape={frame.shape}")
        print(f"  columns={frame.columns.tolist()}")
        label_columns = [column for column in frame.columns if "label" in column.lower()]
        if not label_columns:
            raise RuntimeError(f"No label column found in {split} split")
        for column in label_columns:
            print(f"  {column} distribution={frame[column].value_counts(dropna=False).to_dict()}")
        print(f"  saved={output}")


if __name__ == "__main__":
    main()

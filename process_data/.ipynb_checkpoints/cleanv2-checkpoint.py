import re

import mwparserfromhell
import pandas as pd
from tqdm import tqdm  # 1. Import tqdm

# 2. Initialize tqdm for Pandas
tqdm.pandas(desc="Cleaning Wiki Text")


def clean(text):
    if not isinstance(text, str):
        return ""

    try:
        wikicode = mwparserfromhell.parse(text)
        text = wikicode.strip_code()
        text = re.sub(r"\s+", " ", text).strip()
        return text

    except Exception as e:
        # We probably don't want to print every error if there are thousands,
        # but leaving it here as requested.
        print(f"\nWarning: Failed to parse a row. Error: {e}")
        return ""


def process_csv(file_path):
    df = pd.read_csv(file_path)

    print("Initial:", len(df))

    df["title"] = df["title"].fillna("")
    df["text"] = df["text"].fillna("")

    df = df[~df["title"].str.contains("định hướng", na=False)]
    df = df[
        ~df["title"].str.startswith(("Wikipedia:", "Tập tin:", "Bản mẫu:", "Thể loại:"))
    ]
    df = df[df["title"] != "Trang Chính"]

    print("Starting the cleaning process...")

    # 3. Swap .apply() for .progress_apply()
    df["text"] = df["text"].progress_apply(clean)

    df = df[df["text"].str.len() > 800]

    df.to_csv("cleaned.csv", index=False, encoding="utf-8")
    print("Done:", len(df))


process_csv(r"E:\ProjectAI\Agent\data\clean\viwiki.csv")

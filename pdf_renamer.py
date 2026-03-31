from __future__ import annotations

import os
import re
import string
from collections import Counter
from pathlib import Path

from langdetect import detect
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
from tqdm import tqdm

import nltk

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")

custom_stopwords_tr = set(
    [
        "için",
        "olarak",
        "veya",
        "ve",
        "ile",
        "ama",
        "fakat",
        "ancak",
        "gibi",
        "daha",
        "çok",
        "az",
        "her",
        "bir",
        "bu",
        "şu",
        "o",
        "da",
        "de",
        "ki",
        "mı",
        "mi",
        "mu",
        "mü",
        "ya",
        "ise",
        "en",
        "sonra",
        "önce",
        "kadar",
        "göre",
        "üzere",
        "içinde",
        "üzerine",
        "arasında",
        "tarafından",
        "hakkında",
        "karşı",
        "iç",
        "dış",
        "altında",
        "üstünde",
        "yanında",
    ]
)
custom_stopwords_en = set(
    [
        "fig",
        "figure",
        "table",
        "page",
        "pages",
        "chapter",
        "etc",
        "ie",
        "eg",
        "also",
        "one",
        "two",
        "three",
        "may",
        "can",
        "must",
        "should",
        "could",
        "would",
        "however",
        "thus",
        "therefore",
        "et",
        "al",
        "use",
        "used",
        "using",
        "based",
        "within",
        "among",
        "per",
        "via",
        "see",
        "shown",
        "solution",
        "solutions",
    ]
)


def extract_text_from_pdf(pdf_path: str | Path, max_pages: int = 3) -> str:
    """Extract raw text from a given number of starting pages.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to extract text from.

    Returns:
        Concatenated text from the first max_pages pages.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        num_pages = min(len(reader.pages), max_pages)
        for i in range(num_pages):
            text += reader.pages[i].extract_text() or ""
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def extract_title_candidate(pdf_path: str | Path, max_pages: int = 3) -> str | None:
    """
    Try to extract a probable title from the first max_pages pages.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to search for a title.

    Returns:
        Title string if successful, otherwise None.
    """
    title = None
    try:
        reader = PdfReader(pdf_path)
        num_pages = min(len(reader.pages), max_pages)
        lines = []
        for i in range(num_pages):
            page_text = reader.pages[i].extract_text()
            if not page_text:
                continue
            page_lines = page_text.split("\n")
            # Filter out completely empty lines and short lines
            page_lines = [line.strip() for line in page_lines if len(line.strip()) >= 6]
            lines.extend(page_lines)
        # Heuristic: The first non-stopword, non-all-uppercase line (or the line with the most words) is often the title
        if lines:
            # Option 1: Prefer the first long line
            probable_titles = [
                l for l in lines if (8 < len(l) < 140) and not l.isupper()
            ]
            if probable_titles:
                # Option 2: Prefer the line with the most "significant" words
                return probable_titles[0]
            # Option 3: Fallback to the longest line
            return max(lines, key=len)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return title


def clean_and_tokenize(text: str, lang: str) -> list[str]:
    """Tokenize text and remove stopwords based on language.

    Args:
        text: Raw text to tokenize.
        lang: ISO 639-1 language code (e.g., 'en', 'tr').

    Returns:
        List of filtered tokens.
    """
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    words = word_tokenize(text)
    if lang == "tr":
        stop_words = set(stopwords.words("turkish")).union(custom_stopwords_tr)
    else:
        stop_words = set(stopwords.words("english")).union(custom_stopwords_en)
    words = [w for w in words if w.isalpha() and w not in stop_words and len(w) > 3]
    return words


def get_top_nouns_en(words: list[str], n: int = 4) -> list[str]:
    """Extract top N nouns from English text using POS tagging.

    Args:
        words: List of tokenized words.
        n: Number of top nouns to return.

    Returns:
        List of top N nouns by frequency.
    """
    tagged = pos_tag(words)
    nouns = [word for word, pos in tagged if pos.startswith("NN")]
    counter = Counter(nouns)
    most_common = [word for word, _ in counter.most_common(n)]
    return most_common


def get_top_words_tr(words: list[str], n: int = 4) -> list[str]:
    """Extract top N words from Turkish text by frequency.

    Args:
        words: List of tokenized words.
        n: Number of top words to return.

    Returns:
        List of top N words by frequency.
    """
    counter = Counter(words)
    most_common = [word for word, _ in counter.most_common(n)]
    return most_common


def slugify(text: str, lang: str) -> str:
    """Make a string safe for filenames, keep Turkish special chars if needed.

    Args:
        text: Text to slugify.
        lang: ISO 639-1 language code (e.g., 'en', 'tr').

    Returns:
        Filename-safe string.
    """
    text = text.strip().replace(" ", "_")
    # Remove unwanted chars that can't be in filenames
    text = re.sub(r'[<>:"/\\|?*]', "", text)
    # Optionally, transliterate Turkish chars (uncomment if you want Latin only)
    # if lang == 'tr':
    #     replacements = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u'}
    #     for src, tgt in replacements.items():
    #         text = text.replace(src, tgt)
    return text


def rename_pdf(pdf_path: str | Path, new_name: str, directory: str | Path) -> None:
    """Rename a PDF file with collision-safe suffixing.

    Args:
        pdf_path: Path to the original PDF file.
        new_name: Desired filename without extension.
        directory: Target directory for the renamed file.
    """
    ext = ".pdf"
    new_filename = f"{new_name}{ext}"
    new_filepath = os.path.join(directory, new_filename)
    i = 1
    while os.path.exists(new_filepath):
        new_filename = f"{new_name}_{i}{ext}"
        new_filepath = os.path.join(directory, new_filename)
        i += 1
    os.rename(pdf_path, new_filepath)
    print(f"Renamed to: {new_filename}")


def main(directory: str | Path, max_pages: int = 3) -> None:
    """Process all PDFs in a directory and rename based on content.

    Args:
        directory: Path to the directory containing PDFs.
        max_pages: Maximum number of pages to extract text from.
    """
    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(directory, pdf_file)
        first_text = extract_text_from_pdf(pdf_path, max_pages)
        if not first_text.strip():
            print(f"No text found in {pdf_file}, skipping.")
            continue
        try:
            lang = detect(first_text)
        except Exception:
            lang = "en"
        # Try to extract title from the first pages
        title_candidate = extract_title_candidate(pdf_path, max_pages)
        if title_candidate:
            slug_title = slugify(title_candidate, lang)
            rename_pdf(pdf_path, slug_title, directory)
            continue
        # If no title, fallback to keywords
        words = clean_and_tokenize(first_text, lang)
        if not words:
            print(f"No valid words found in {pdf_file}, skipping.")
            continue
        if lang == "tr":
            top_words = get_top_words_tr(words, n=4)
        else:
            top_words = get_top_nouns_en(words, n=4)
        if top_words:
            # Use the longest (likely the most distinctive) word for the filename
            top_words = sorted(top_words, key=lambda w: (-len(w), w))
            new_name = top_words[0]
            rename_pdf(pdf_path, new_name, directory)
        else:
            print(f"No significant words found in {pdf_file}, skipping.")


if __name__ == "__main__":
    directory = "./pdfs"
    main(directory, max_pages=3)

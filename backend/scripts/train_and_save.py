"""Обучение модели на emails.csv и сохранение артефактов.

Вариант 1 (быстрый, если есть словари из Spark-пайплайна домашки):
    передайте пути к parquet-таблицам через --word-table / --bigram-table.

Вариант 2 (локальный):
    python scripts/train_and_save.py --csv ../emails.csv

Результат: backend/data/vocab.json.gz и backend/data/bigrams.json.gz
"""
import argparse
import gzip
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.cleaner import clean_and_tokenize  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
MIN_WORD_FREQ = 3
MIN_NGRAM_FREQ = 3


def save_json_gz(path: str, obj) -> None:
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    print(f'  -> {path} ({os.path.getsize(path) / 1e6:.1f} MB)')


def load_json_gz(path: str):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def train_from_csv(csv_path: str) -> None:
    import pandas as pd

    print(f'Читаю {csv_path} ...')
    t0 = time.time()
    emails = pd.read_csv(csv_path, usecols=['message'])
    print(f'  писем: {len(emails)} за {time.time() - t0:.1f}s')

    print('Токенизация ...')
    t0 = time.time()
    corpus = [clean_and_tokenize(t) for t in emails['message'].fillna('')]
    corpus = [t for t in corpus if t]
    print(f'  {len(corpus)} непустых писем за {time.time() - t0:.1f}s')
    del emails

    word_counts = Counter()
    for text in corpus:
        word_counts.update(text)
    word_counts = {w: c for w, c in word_counts.items() if c >= MIN_WORD_FREQ}
    print(f'Словарь: {len(word_counts)} слов (частота >= {MIN_WORD_FREQ})')

    bigrams = Counter()
    for text in corpus:
        bigrams.update(zip(text, text[1:]))
    # группируем в {prev: {next: count}}, отбрасывая редкие биграммы
    bigram_map: dict = {}
    for (prev, nxt), c in bigrams.items():
        if c >= MIN_NGRAM_FREQ:
            bigram_map.setdefault(prev, {})[nxt] = c
    n_contexts = len(bigram_map)
    print(f'Биграмм: {n_contexts} контекстов (частота >= {MIN_NGRAM_FREQ})')
    del corpus, bigrams

    os.makedirs(DATA_DIR, exist_ok=True)
    save_json_gz(os.path.join(DATA_DIR, 'vocab.json.gz'), word_counts)
    save_json_gz(os.path.join(DATA_DIR, 'bigrams.json.gz'), bigram_map)


def train_from_parquet(word_table: str, bigram_table: str) -> None:
    """Читает таблицы, сохранённые Spark-пайплайном домашки."""
    import pandas as pd

    print(f'Читаю частоты слов из {word_table} ...')
    wc = pd.read_parquet(word_table)
    word_counts = dict(zip(wc['word'], wc['cnt'].astype(int)))
    print(f'  {len(word_counts)} слов')

    print(f'Читаю биграммы из {bigram_table} ...')
    bg = pd.read_parquet(bigram_table)
    bigram_map: dict = {}
    for gram, cnt in zip(bg['gram'], bg['cnt'].astype(int)):
        if cnt < MIN_NGRAM_FREQ:
            continue
        prev, nxt = gram.rsplit(' ', 1)
        bigram_map.setdefault(prev, {})[nxt] = cnt
    print(f'  {len(bigram_map)} контекстов')

    os.makedirs(DATA_DIR, exist_ok=True)
    save_json_gz(os.path.join(DATA_DIR, 'vocab.json.gz'), word_counts)
    save_json_gz(os.path.join(DATA_DIR, 'bigrams.json.gz'), bigram_map)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', help='путь к emails.csv (локальное обучение)')
    parser.add_argument('--word-table', help='путь к parquet с колонками word, cnt')
    parser.add_argument('--bigram-table', help='путь к parquet с колонками gram, cnt')
    args = parser.parse_args()

    if args.word_table and args.bigram_table:
        train_from_parquet(args.word_table, args.bigram_table)
    elif args.csv:
        train_from_csv(args.csv)
    else:
        parser.error('укажите --csv или --word-table + --bigram-table')

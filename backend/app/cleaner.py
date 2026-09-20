"""Очистка и токенизация текста писем (задание 1 домашки).

Логика та же, что использовалась при подготовке корпуса в Spark,
поэтому статистика, собранная на кластере, совместима с этой функцией.
"""
import re

URL_RE = re.compile(r'https?://\S+|www\.\S+')
EMAIL_ADDR_RE = re.compile(r'\S+@\S+')
HTML_RE = re.compile(r'<[^>]+>')
NON_ALPHA = re.compile(r"[^a-z\s']+")
WS = re.compile(r'\s+')


def clean_and_tokenize(text: str) -> list[str]:
    """Очистка + токенизация: нижний регистр, только буквы и апострофы."""
    if not text:
        return []
    text = text.lower()
    text = HTML_RE.sub(' ', text)
    text = URL_RE.sub(' ', text)
    text = EMAIL_ADDR_RE.sub(' ', text)
    text = NON_ALPHA.sub(' ', text)
    return WS.sub(' ', text).strip().split()

"""FastAPI: подсказки продолжения текста в реальном времени."""
import gzip
import json
import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .model import NGramLanguageModel, TextSuggestion, WordCompletor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def load_json_gz(path: str):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


# --- загрузка артефактов, обученных на корпусе emails (см. scripts/train_and_save.py) ---
word_counts = load_json_gz(os.path.join(DATA_DIR, 'vocab.json.gz'))
bigrams = load_json_gz(os.path.join(DATA_DIR, 'bigrams.json.gz'))

word_completor = WordCompletor(word_counts=word_counts)

# основная модель: контекст из 2 слов (семантика n-грамм из задания 4 домашки)
ctx_model = NGramLanguageModel(n=2)
ctx2_path = os.path.join(DATA_DIR, 'contexts2.json.gz')
if os.path.exists(ctx2_path):
    contexts2 = load_json_gz(ctx2_path)
    for ctx, dist in contexts2.items():
        ctx_model.next_words[tuple(ctx.split(' '))] = dist
else:
    # фолбэк: 1-словные контексты из биграмм
    for prev, dist in bigrams.items():
        ctx_model.next_words[(prev,)] = dist

# фолбэк-модель: контекст из 1 слова — срабатывает, когда 2-словного нет
fallback_model = NGramLanguageModel(n=1)
for prev, dist in bigrams.items():
    fallback_model.next_words[(prev,)] = dist


def next_words_for(context: list) -> list:
    """2-словный контекст -> фолбэк на последнее слово."""
    nxt, _ = ctx_model.get_next_words_and_probs(context)
    if nxt:
        return nxt
    nxt, _ = fallback_model.get_next_words_and_probs(context)
    return nxt

app = FastAPI(
    title='N-grammer API',
    description='Автодополнение текста n-граммной моделью (HW1, ФКН ВШЭ)',
    version='1.0.0',
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # dev; в проде заменить на адрес фронтенда
    allow_methods=['*'],
    allow_headers=['*'],
)


class SuggestRequest(BaseModel):
    text: str = Field(..., description='Текст, набранный пользователем')
    n_words: int = Field(3, ge=1, le=10, description='Сколько слов в продолжении')
    k: int = Field(3, ge=1, le=10, description='Сколько вариантов показывать')


class Suggestion(BaseModel):
    completion: str = Field(..., description='Строка, которую дописать к тексту (с ведущим пробелом)')
    words: List[str] = Field(..., description='Слова продолжения по отдельности')
    type: str = Field(..., description='complete — дополняет недописанное слово; next — следующие слова')


class SuggestResponse(BaseModel):
    suggestions: List[Suggestion]


@app.get('/health')
def health() -> dict:
    return {
        'status': 'ok',
        'vocab_size': len(word_counts),
        'n_contexts_2w': len(ctx_model.next_words),
        'n_contexts_1w': len(fallback_model.next_words),
    }


@app.post('/suggest', response_model=SuggestResponse)
def suggest(req: SuggestRequest) -> SuggestResponse:
    """Подсказки для текущего текста.

    Логика (задание 5):
      - текст кончается недописанным словом -> дополняем его через WordCompletor
        (тип `complete`) и добавляем вариант продолжения лучшего дополнения;
      - текст кончается пробелом (слово закончено) -> n-граммная модель
        предлагает следующие слова (тип `next`).
    """
    text = req.text
    if not text.strip():
        # пустой ввод: самые частые слова корпуса
        top = sorted(word_counts.items(), key=lambda kv: -kv[1])[:req.k]
        return SuggestResponse(suggestions=[
            Suggestion(completion=w, words=[w], type='next') for w, _ in top
        ])

    ends_with_space = text.endswith((' ', '\t', '\n'))
    words = text.strip().split()
    out: List[Suggestion] = []

    # контекст для биграммной модели — последнее слово; для триграммной — два
    continuation = next_words_for

    if not ends_with_space:
        # 1) дополняем недописанное слово — топ-k по вероятности
        cw, _ = word_completor.get_words_and_probs(words[-1])
        for w in cw[:req.k]:
            out.append(Suggestion(completion=f' {w}', words=[w], type='complete'))
        # 2) продолжение для лучшего дополнения
        if cw:
            nxt = continuation(words[:-1] + [cw[0]])
            if nxt:
                chain = [cw[0]] + nxt[:max(req.n_words - 1, 1)]
                out.append(Suggestion(
                    completion=' ' + ' '.join(chain),
                    words=chain,
                    type='next',
                ))
        return SuggestResponse(suggestions=out[:req.k + 1])

    # 3) слово закончено — продолжаем n-граммами, для каждого варианта докатываем цепочку
    nxt = continuation(words)
    for w in nxt[:req.k]:
        chain = [w]
        ctx = words + [w]
        for _ in range(max(req.n_words - 1, 0)):
            nn = continuation(ctx)
            if not nn:
                break
            ctx = ctx + [nn[0]]
            chain.append(nn[0])
        out.append(Suggestion(completion=' ' + ' '.join(chain), words=chain, type='next'))
    return SuggestResponse(suggestions=out[:req.k])

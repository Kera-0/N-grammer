# N-grammer

**Text Suggestion** — система автодополнения текста n-граммной моделью (домашнее задание 1, «Глубинное обучение для текстовых данных», ФКН ВШЭ). Бонусная часть: полноценный UI — страница написания письма, где подсказки появляются в реальном времени.

- **Бекенд:** FastAPI + классы из основной части домашки (`PrefixTree`, `WordCompletor`, `NGramLanguageModel`, `TextSuggestion`), обученные на 517k писем Enron.
- **Фронтенд:** Vue 3 + Vite. Призрачный текст (ghost text) показывает лучшее продолжение прямо в поле ввода, чипы — альтернативы, `Tab` применяет подсказку, `↑↓` — переключение.

## Структура

```
N-grammer/
├── backend/
│   ├── app/
│   │   ├── cleaner.py        # очистка + токенизация (задание 1)
│   │   ├── model.py          # PrefixTree, WordCompletor, NGramLanguageModel, TextSuggestion (задания 2–5)
│   │   └── main.py           # FastAPI: /suggest, /health
│   ├── scripts/
│   │   └── train_and_save.py # обучение на emails.csv → data/*.json.gz
│   ├── data/                 # артефакты (vocab.json.gz, bigrams.json.gz)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.vue
    │   ├── components/Composer.vue   # редактор письма с подсказками
    │   └── styles.css
    ├── index.html
    └── package.json
```

## Запуск

### 1. Обучить модель

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# локально из emails.csv (~5–10 минут):
python scripts/train_and_save.py --csv ../emails.csv

# или из Spark-таблиц домашки (быстро):
python scripts/train_and_save.py \
  --word-table  /path/to/priv_DB_dengalimovr/hw1_word_counts \
  --bigram-table /path/to/priv_DB_dengalimovr/hw1_bigram_counts
```

### 2. Поднять API

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Swagger: http://localhost:8000/docs

### 3. Поднять фронтенд

```bash
cd frontend
npm install
npm run dev
```

Открыть http://localhost:5173

## API

`POST /suggest`

```json
{ "text": "dear team, i would like ", "n_words": 3, "k": 3 }
```

Ответ:

```json
{
  "suggestions": [
    { "completion": " to invite you", "words": ["to", "invite", "you"], "type": "next" }
  ]
}
```

Логика подсказки (задание 5):

- текст кончается **недописанным словом** → `WordCompletor` дополняет его (тип `complete`) + лучший вариант продолжения;
- текст кончается **пробелом/знаком** → n-граммная модель предлагает следующие слова (тип `next`).

## Горячие клавиши в UI

| Клавиша | Действие |
|---|---|
| `Tab` / `→` | принять активную подсказку |
| `↑` / `↓` | выбрать другую подсказку |
| `Esc` | скрыть призрачный текст |

"""Классы системы Text Suggestion — решение заданий 2-5 домашки."""
from collections import Counter, defaultdict
from typing import List, Tuple


class PrefixTreeNode:
    __slots__ = ('children', 'is_end_of_word')

    def __init__(self):
        self.children: dict[str, PrefixTreeNode] = {}
        self.is_end_of_word = False


class PrefixTree:
    """Префиксное дерево: поиск всех слов по префиксу за O(n + mk)."""

    def __init__(self, vocabulary: List[str]):
        self.root = PrefixTreeNode()
        for word in vocabulary:
            node = self.root
            for ch in word:
                node = node.children.setdefault(ch, PrefixTreeNode())
            node.is_end_of_word = True

    def search_prefix(self, prefix: str) -> List[str]:
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return []
        words, stack = [], [(node, prefix)]
        while stack:
            cur, pref = stack.pop()
            if cur.is_end_of_word:
                words.append(pref)
            for ch, child in cur.children.items():
                stack.append((child, pref + ch))
        return words


class WordCompletor:
    """Дополняет недописанное слово до целого по частоте встречаемости."""

    def __init__(self, corpus=None, word_counts: dict = None):
        if word_counts is not None:
            self.word_counts = word_counts
        else:
            counts = Counter()
            total = 0
            for text in (corpus or []):
                counts.update(text)
                total += len(text)
            self.word_counts = dict(counts)
        self.total = sum(self.word_counts.values()) or 1
        self.prefix_tree = PrefixTree(self.word_counts)

    def get_words_and_probs(self, prefix: str) -> Tuple[List[str], List[float]]:
        words = self.prefix_tree.search_prefix(prefix)
        # топ по вероятности, чтобы не отдавать тысячи продолжений
        words.sort(key=lambda w: -self.word_counts[w])
        probs = [self.word_counts[w] / self.total for w in words]
        return words, probs


class NGramLanguageModel:
    """N-граммная модель: распределение следующего слова по контексту.

    Семантика домашки: P(w_i | w_{i-1}, ..., w_{i-n}) по частоте n-граммы,
    то есть контекст — n последних слов префикса, а предсказываем (n+1)-е.
    Внутреннее хранение: {tuple(context): {next_word: count}}.
    """

    def __init__(self, corpus=None, n: int = 2, ngram_counts: dict = None,
                 contexts_size: int = None):
        self.n = n
        if ngram_counts is not None:
            self.next_words = {tuple(k) if not isinstance(k, tuple) else k: dict(v)
                               for k, v in ngram_counts.items()}
        else:
            # {context (n слов): {next_word: count}} — считаем из корпуса
            nxt = defaultdict(lambda: defaultdict(int))
            for text in (corpus or []):
                padded = ['<PAD>'] * n + list(text)
                for i in range(len(padded) - n):
                    nxt[tuple(padded[i:i + n])][padded[i + n]] += 1
            self.next_words = {k: dict(v) for k, v in nxt.items()}

    def get_next_words_and_probs(self, prefix: list) -> Tuple[List[str], List[float]]:
        context = tuple(prefix[-self.n:]) if len(prefix) >= self.n else tuple(prefix)
        dist = self.next_words.get(context)
        if not dist:
            return [], []
        total = sum(dist.values())
        items = sorted(dist.items(), key=lambda kv: -kv[1])
        return [w for w, _ in items], [c / total for _, c in items]


class TextSuggestion:
    """Объединяет WordCompletor и NGramLanguageModel (задание 5)."""

    def __init__(self, word_completor: WordCompletor, n_gram_model: NGramLanguageModel):
        self.word_completor = word_completor
        self.n_gram_model = n_gram_model

    def suggest_text(self, text, n_words: int = 3, n_texts: int = 1) -> List[List[str]]:
        """[дополненное последнее слово] + n_words слов продолжения."""
        if isinstance(text, str):
            text = text.split()
        text = list(text)
        if not text:
            return [[] for _ in range(n_texts)]

        last = text[-1]
        words, probs = self.word_completor.get_words_and_probs(last)
        completed = last
        if words and last not in words:
            completed = words[0]  # слова уже отсортированы по вероятности
        context = text[:-1] + [completed]

        for _ in range(n_words):
            nxt, pr = self.n_gram_model.get_next_words_and_probs(context)
            if not nxt:
                break
            context.append(nxt[0])
        return [context[-(n_words + 1):]] * n_texts

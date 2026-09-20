"""Быстрые проверки классов (dummy-тесты из домашки)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model import PrefixTree, WordCompletor, NGramLanguageModel, TextSuggestion

# задание 2
pt = PrefixTree(['aa', 'aaa', 'abb', 'bba', 'bbb', 'bcd'])
assert set(pt.search_prefix('a')) == {'aa', 'aaa', 'abb'}
assert set(pt.search_prefix('bb')) == {'bba', 'bbb'}

# задание 3
dummy = [["aa", "ab"], ["aaa", "abab"], ["abb", "aa", "ab", "bba", "bbb", "bcd"]]
wc = WordCompletor(corpus=dummy)
words, probs = wc.get_words_and_probs('a')
assert set(zip(words, probs)) == {('aa', 0.2), ('ab', 0.2), ('aaa', 0.1), ('abab', 0.1), ('abb', 0.1)}

# задание 4 (корпус из условия задания 4)
dummy_corpus = [['aa', 'aa', 'aa', 'aa', 'ab'], ['aaa', 'abab'], ['abb', 'aa', 'ab', 'bba', 'bbb', 'bcd']]
ng = NGramLanguageModel(corpus=dummy_corpus, n=2)
nw, np_ = ng.get_next_words_and_probs(['aa', 'aa'])
assert set(zip(nw, np_)) == {('aa', 2/3), ('ab', 1/3)}

# задание 5 (WordCompletor на том же корпусе, что и в условии)
wc2 = WordCompletor(corpus=dummy_corpus)
ts = TextSuggestion(wc2, ng)
assert ts.suggest_text(['aa', 'aa'], n_words=3, n_texts=1) == [['aa', 'aa', 'aa', 'aa']]
assert ts.suggest_text(['abb', 'aa', 'ab'], n_words=2, n_texts=1) == [['ab', 'bba', 'bbb']]

print('Все dummy-тесты проходят ✓')

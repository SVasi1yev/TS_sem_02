#!/usr/bin/env python
# -*- coding: utf8 -*-

from LanguageModel import LanguageModel
from ErrorModel import ErrorModel
from Bor import Bor
import utils
import sys


class Spellchecker:
    def __init__(self):
        self.lang_model = LanguageModel()
        self.lang_model.load()
        self.err_model = ErrorModel()
        self.err_model.load()
        self.bor = Bor(self.lang_model, self.err_model)
        self.bor.fit()
        self.switcher = utils.LayoutSwitcher()

    def fix_query(self, query):
        if len(utils.split(query)) == 0:
            return query
        old_query = None
        new_query = query
        while old_query != new_query:
            old_query = new_query
            new_query = self.fix_all(query)
        return new_query

    def fix_all(self, query):
        q0, w0 = query, self.lang_model.get_query_prob(query)
        q, w = self.fix_dict(query)
        if w < w0:
            q0, w0 = q, w
        q, w = self.fix_layout(query)
        if w < w0:
            q0, w0 = q, w
        q, w = self.fix_join(query)
        if w < w0:
            q0, w0 = q, w
        q, w = self.fix_split(query)
        if w < w0:
            q0, w0 = q, w
        if w0 > 3000:
            return query
        return q0

    def fix_dict(self, query):
        matches = utils.split(query)
        for idx, word in enumerate(matches):
            matches[idx] = self.bor.best_match(word=word, alpha=1, beta=1, max_weight=6, match_num=8, max_diff=3)
        q0, w0 = self.word_chain(matches)
        return q0, w0

    def word_chain(self, matches):
        q0 = ''
        w0 = 1e6
        for query in self.gen_chain(matches):
            q = ' '.join(query) + '\n'
            w = self.lang_model.get_query_prob(q)
            if w < w0:
                q0, w0 = q, w
        return q0, w0

    def gen_chain(self, matches):
        if len(matches) == 1:
            for word in matches[0]:
                yield [word]
        else:
            for word in matches[0]:
                for query in self.gen_chain(matches[1:]):
                    yield [word] + query

    def fix_layout(self, query):
        words = utils.split(query)
        q0, w0 = query, self.lang_model.get_query_prob(query)
        for idx, word in enumerate(words):
            ru_word = self.switcher.switch_en_to_ru(word)
            en_word = self.switcher.switch_ru_to_en(word)
            ru_query = ' '.join(words[:idx] + [ru_word] + words[idx+1:])
            en_query = ' '.join(words[:idx] + [en_word] + words[idx+1:])
            ru_w = self.lang_model.get_query_prob(ru_query)
            en_w = self.lang_model.get_query_prob(en_query)
            if ru_w < w0:
                q0, w0 = ru_query, ru_w
            if en_w < w0:
                q0, w0 = en_query, en_w
        return q0, w0

    def fix_join(self, query):
        q0 = query
        w0 = self.lang_model.get_query_prob(query)
        for idx, ch in enumerate(query):
            if ch != ' ':
                continue
            q = query[:idx] + query[idx+1:]
            w = self.lang_model.get_query_prob(q)
            if w < w0:
                q0 = q
                w0 = w
        return q0, w0

    def fix_split(self, query):
        q0 = query
        w0 = self.lang_model.get_query_prob(query)
        for i in range(1, len(query) - 1):
            q = query[:i] + ' ' + query[i:]
            w = self.lang_model.get_query_prob(q)
            if w < w0:
                q0 = q
                w0 = w
        return q0, w0


if __name__ == '__main__':
    spellchecker = Spellchecker()
    for line in sys.stdin:
        sys.stdout.write(spellchecker.fix_query(line.decode('utf8')).encode('utf8'))
    # with open('queries_all.txt', 'r') as f:
    #     for idx, line in enumerate(f):
    #         line = line.decode('utf8')
    #         line = line.split('\t')[0]
    #         print idx + 1, spellchecker.fix_query(line).encode('utf8')
    #         if idx == 1000:
    #             break

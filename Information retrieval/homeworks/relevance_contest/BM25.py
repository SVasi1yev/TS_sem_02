from _collections import defaultdict
import re
import numpy as np
import pymorphy2
from tqdm import tqdm
from pymystem3 import Mystem
from rank_bm25 import BM25Okapi

sample_sub_file = 'sample.technosphere.ir1.textrelevance.submission.txt'
parsed_docs_dir = 'my_doc_mystem/'
query_file = 'queries.numerate.txt'

SPLIT_RGX = re.compile(r'[A-Za-zА-Яа-я0-9]+')

def split(string):
    words = re.findall(SPLIT_RGX, string)
    return words

query_id_2_docs_id = defaultdict(list)
with open(sample_sub_file, 'r') as f:
    f.readline()
    for line in f:
        query_id, doc_id = tuple(map(int, line.split(',')))
        query_id_2_docs_id[query_id].append(doc_id)

query_id_2_query = {}
with open(query_file, 'r') as f:
    for line in f:
        query_id, query = tuple(line.split('\t')[:2])
        query_id = int(query_id)
        query_id_2_query[query_id] = query

mystem = Mystem()


class GlobalStats:
    def __init__(self):
        self.collection_len = 0
        self.title_avg_len = 0
        self.headers_avg_len = 0
        self.body_avg_len = 0
        self.title_word_2_idf = defaultdict(float)
        self.headers_word_2_idf = defaultdict(float)
        self.body_word_2_idf = defaultdict(float)
        for query_id in tqdm(query_id_2_docs_id):
            for doc_id in query_id_2_docs_id[query_id]:
                with open(f'{parsed_docs_dir}{doc_id}.txt', errors='ignore') as f:
                    self.collection_len += 1
                    title = split(f.readline().lower())
                    self.title_avg_len += len(title)
                    proc_words = set()
                    for word in title:
                        if word not in proc_words:
                            self.title_word_2_idf[word] += 1
                            proc_words.add(word)
                    headers = split(f.readline().lower())
                    self.headers_avg_len += len(headers)
                    proc_words = set()
                    for word in headers:
                        if word not in proc_words:
                            self.headers_word_2_idf[word] += 1
                            proc_words.add(word)
                    body = split(f.read().lower())
                    self.body_avg_len += len(body)
                    proc_words = set()
                    for word in body:
                        if word not in proc_words:
                            self.body_word_2_idf[word] += 1
                            proc_words.add(word)
        title_idf_sum = 0
        title_neg_idf = []
        for word in self.title_word_2_idf:
            idf = np.log(self.collection_len - self.title_word_2_idf[word] + 0.5) - np.log(self.title_word_2_idf[word] + 0.5)
            self.title_word_2_idf[word] = idf
            title_idf_sum += idf
            if idf < 0:
                title_neg_idf.append(word)
        aver_idf = title_idf_sum / len(self.title_word_2_idf)
        eps = 0.25 * aver_idf
        for word in title_neg_idf:
            self.title_word_2_idf[word] = eps
        self.title_avg_len /= self.collection_len

        headers_idf_sum = 0
        headers_neg_idf = []
        for word in self.headers_word_2_idf:
            idf = np.log(self.collection_len - self.headers_word_2_idf[word] + 0.5) - np.log(self.headers_word_2_idf[word] + 0.5)
            self.headers_word_2_idf[word] = idf
            headers_idf_sum += idf
            if idf < 0:
                headers_neg_idf.append(word)
        aver_idf = headers_idf_sum / len(self.headers_word_2_idf)
        eps = 0.25 * aver_idf
        for word in headers_neg_idf:
            self.headers_word_2_idf[word] = eps
        self.headers_avg_len /= self.collection_len

        body_idf_sum = 0
        body_neg_idf = []
        for word in self.body_word_2_idf:
            idf = np.log(self.collection_len - self.body_word_2_idf[word] + 0.5) - np.log(self.body_word_2_idf[word] + 0.5)
            self.body_word_2_idf[word] = idf
            body_idf_sum += idf
            if idf < 0:
                body_neg_idf.append(word)
        aver_idf = body_idf_sum / len(self.body_word_2_idf)
        eps = 0.25 * aver_idf
        for word in body_neg_idf:
            self.body_word_2_idf[word] = eps
        self.body_avg_len /= self.collection_len


class QueryStats:
    def __init__(self, query_id):
        docs_list = query_id_2_docs_id[query_id]
        self.query_id = query_id
        self.query_words = split(' '.join(mystem.lemmatize(query_id_2_query[query_id].lower())))
        self.collection_len = len(docs_list)
        self.title_avg_len = 0
        self.headers_avg_len = 0
        self.body_avg_len = 0
        self.title_word_2_idf = defaultdict(float)
        self.headers_word_2_idf = defaultdict(float)
        self.body_word_2_idf = defaultdict(float)
        for doc_id in docs_list:
            with open(f'{parsed_docs_dir}{doc_id}.txt', errors='ignore') as f:
                title = split(f.readline().lower())
                self.title_avg_len += len(title)
                proc_words = set()
                for word in title:
                    if word not in proc_words:
                        self.title_word_2_idf[word] += 1
                        proc_words.add(word)
                headers = split(f.readline().lower())
                self.headers_avg_len += len(headers)
                proc_words = set()
                for word in headers:
                    if word not in proc_words:
                        self.headers_word_2_idf[word] += 1
                        proc_words.add(word)
                body = split(f.read().lower())
                self.body_avg_len += len(body)
                proc_words = set()
                for word in body:
                    if word not in proc_words:
                        self.body_word_2_idf[word] += 1
                        proc_words.add(word)

        title_idf_sum = 0
        title_neg_idf = []
        for word in self.title_word_2_idf:
            idf = np.log(self.collection_len - self.title_word_2_idf[word] + 0.5) - np.log(self.title_word_2_idf[word] + 0.5)
            self.title_word_2_idf[word] = idf
            title_idf_sum += idf
            if idf < 0:
                title_neg_idf.append(word)
        aver_idf = title_idf_sum / len(self.title_word_2_idf)
        eps = 0.25 * aver_idf
        for word in title_neg_idf:
            self.title_word_2_idf[word] = eps
        self.title_avg_len /= self.collection_len

        headers_idf_sum = 0
        headers_neg_idf = []
        for word in self.headers_word_2_idf:
            idf = np.log(self.collection_len - self.headers_word_2_idf[word] + 0.5) - np.log(self.headers_word_2_idf[word] + 0.5)
            self.headers_word_2_idf[word] = idf
            headers_idf_sum += idf
            if idf < 0:
                headers_neg_idf.append(word)
        aver_idf = headers_idf_sum / len(self.headers_word_2_idf)
        eps = 0.25 * aver_idf
        for word in headers_neg_idf:
            self.headers_word_2_idf[word] = eps
        self.headers_avg_len /= self.collection_len

        body_idf_sum = 0
        body_neg_idf = []
        for word in self.body_word_2_idf:
            idf = np.log(self.collection_len - self.body_word_2_idf[word] + 0.5) - np.log(self.body_word_2_idf[word] + 0.5)
            self.body_word_2_idf[word] = idf
            body_idf_sum += idf
            if idf < 0:
                body_neg_idf.append(word)
        aver_idf = body_idf_sum / len(self.body_word_2_idf)
        eps = 0.25 * aver_idf
        for word in body_neg_idf:
            self.body_word_2_idf[word] = eps
        self.body_avg_len /= self.collection_len


class BM25:
    def __init__(self, k=3.44, b=0.75, pos_disc=0.999, title_bonus=0, headers_bonus=0):
        self.k = k
        self.b = b
        self.pos_disc = pos_disc
        self.title_bonus = title_bonus
        self.headers_bonus = headers_bonus
        self.query_stats = {}
        self.global_stats = None

    def count_global_stats(self):
        self.global_stats = GlobalStats()

    def count_stats_for_query(self, query_id):
        # if query_id in self.query_stats:
        #     return
        self.query_stats[query_id] = QueryStats(query_id)

    def count_query_score_list(self, query_id):
        if query_id not in self.query_stats:
            raise ValueError(f'First you need count stats for this query. Query: {query_id_2_query[query_id]}')
        doc_2_score = {}
        for doc_id in query_id_2_docs_id[query_id]:
            doc_2_score[doc_id] = self.count_doc_score(query_id, doc_id) # TODO
        return doc_2_score

    def count_doc_score(self, query_id, doc_id):
        query = self.query_stats[query_id]
        title_word_2_tf = defaultdict(float)
        headers_word_2_tf = defaultdict(float)
        body_word_2_tf = defaultdict(float)
        with open(f'{parsed_docs_dir}{doc_id}.txt', errors='ignore') as f:
            title = split(f.readline().lower())
            headers = split(f.readline().lower())
            body = split(f.read().lower())
            title_len = len(title)
            headers_len = len(headers)
            body_len = len(body)
            k = 1
            for word in title:
                title_word_2_tf[word] += k
                k *= self.pos_disc
            k = 1
            for word in headers:
                headers_word_2_tf[word] += k
                k *= self.pos_disc
            k = 1
            for word in body:
                body_word_2_tf[word] += k
                k *= self.pos_disc
        for word in title:
            body_word_2_tf[word] += self.title_bonus
        for word in headers:
            body_word_2_tf[word] += self.headers_bonus
        # for word in word_2_tf:
        #     word_2_tf[word] /= doc_len

        title_score = 0
        headers_score = 0
        body_score = 0

        for word in query.query_words:
            title_score += self.global_stats.title_word_2_idf[word] * (title_word_2_tf[word] * (self.k + 1)) / \
                    (title_word_2_tf[word] + self.k * (1 - self.b + self.b * title_len / self.global_stats.title_avg_len))
            headers_score += self.global_stats.headers_word_2_idf[word] * (headers_word_2_tf[word] * (self.k + 1)) / \
                    (headers_word_2_tf[word] + self.k * (1 - self.b + self.b * headers_len / self.global_stats.headers_avg_len))
            body_score += self.global_stats.body_word_2_idf[word] * (body_word_2_tf[word] * (self.k + 1)) / \
                    (body_word_2_tf[word] + self.k * (1 - self.b + self.b * body_len / self.global_stats.body_avg_len))
        return 2.7 * title_score + 1.0 * headers_score + 1.5 * body_score

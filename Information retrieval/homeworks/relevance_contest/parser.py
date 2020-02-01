from bs4 import BeautifulSoup
import re
import pymorphy2
from tqdm import tqdm
from pymystem3 import Mystem

morph = pymorphy2.MorphAnalyzer()
mystem = Mystem()
SPLIT_RGX = re.compile(r'[A-Za-zА-Яа-я0-9]+')


def split(string):
    words = re.findall(SPLIT_RGX, string)
    return words


class Parser:
    def __init__(self):
        self.dir_mystem = 'my_doc_mystem/'
        self.dict_mystem = {}
        self.urls = {}
        urls_id = []
        with open('sample.technosphere.ir1.textrelevance.submission.txt', 'r') as f:
            f.readline()
            for line in f:
                urls_id.append(int(line.split(',')[1].strip()))
        with open('urls.numerate.txt', 'r') as f:
            for line in f:
                url_id, url = tuple(line.strip().split('\t'))
                self.urls[url] = int(url_id)

    def parse(self, first_dir=0, first_doc=0):
        dirs_with_docs = [
            'content/20170702/',
            'content/20170704/',
            'content/20170707/',
            'content/20170708/',
            'content/20170710/',
            'content/20170711/',
            'content/20170717/',
            'content/20170726/'
        ]

        docs_num = [
            4532,
            4616,
            4609,
            4666,
            4803,
            4877,
            4954,
            5049
        ]

        for dir_num in range(first_dir, len(dirs_with_docs)):
            print(f'DIR: {dir_num}')
            start = first_doc if dir_num == first_dir else 0
            for doc_num in tqdm(range(start, docs_num[dir_num] + 1)):
                s = str(doc_num)
                s = '0' * (4 - len(s)) + s
                with open(f'{dirs_with_docs[dir_num]}doc.{s}.dat', errors='ignore') as f:
                    url = f.readline().strip()
                    if url not in self.urls:
                        continue
                    html = f.read()
                    soup = BeautifulSoup(html)
                    [s.extract() for s in soup(['script', 'style', 'title', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
                    body_text = soup.get_text('\n', True).lower()
                    body_words = split(body_text)
                    soup = BeautifulSoup(html)
                    title_text = ' '.join(e.get_text() for e in soup.find_all('title')).lower()
                    title_words = split(title_text)
                    headers_text = ' '.join([e.get_text() for e in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]).lower()
                    headers_words = split(headers_text)

                    title_mystem = []
                    for word in title_words:
                        if word in self.dict_mystem:
                            title_mystem.append(self.dict_mystem[word])
                        else:
                            a = mystem.lemmatize(word)[0]
                            title_mystem.append(a)
                            self.dict_mystem[word] = a
                    title_mystem = ' '.join(title_mystem)

                    headers_mystem = []
                    for word in headers_words:
                        if word in self.dict_mystem:
                            headers_mystem.append(self.dict_mystem[word])
                        else:
                            a = mystem.lemmatize(word)[0]
                            headers_mystem.append(a)
                            self.dict_mystem[word] = a
                    headers_mystem = ' '.join(headers_mystem)

                    body_mystem = []
                    for word in body_words:
                        if word in self.dict_mystem:
                            body_mystem.append(self.dict_mystem[word])
                        else:
                            a = mystem.lemmatize(word)[0]
                            body_mystem.append(a)
                            self.dict_mystem[word] = a
                    body_mystem = ' '.join(body_mystem)

                    doc_id = self.urls[url]
                    with open(f'{self.dir_mystem}{doc_id}.txt', 'w') as f:
                        f.write(title_mystem + '\n')
                        f.write(headers_mystem + '\n')
                        f.write(body_mystem)

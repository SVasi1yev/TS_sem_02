from collections import defaultdict
from utils import split
import numpy as np
import json


class LanguageModel:
    def __init__(self):
        self.un_prob = defaultdict(float)  # {word : prob}
        self.bin_prob = defaultdict(lambda: defaultdict(float))  # {first_word : {second_word : prob}}

        self.un_count = 0
        self.bin_count = defaultdict(int)

    def store(self, file_name='lm_dump.json'):
        with open(file_name, 'w') as file:
            file.write(json.dumps((self.un_prob, self.bin_prob, self.un_count, self.bin_count)))

    def load(self, file_name='lm_dump.json'):
        with open(file_name, 'r') as file:
            dump = json.loads(file.read().decode('utf8'))
            self.un_prob = dump[0]
            self.bin_prob = dump[1]
            self.un_count = dump[2]
            self.bin_count = dump[3]

    def fit(self, file_name='queries_all.txt'):
        with open(file_name, 'r') as file:
            for line in file:
                line = line.decode('utf8')
                line = line.split('\t')[-1].lower().strip()
                words = split(line)

                if len(words) == 0:
                    continue

                self.un_prob[words[0]] += 1
                self.un_count += 1
                for i in range(1, len(words)):
                    self.un_prob[words[i]] += 1
                    self.un_count += 1
                    self.bin_prob[words[i - 1]][words[i]] += 1
                    self.bin_count[words[i - 1]] += 1
            for word in self.un_prob:
                self.un_prob[word] = -(np.log(self.un_prob[word]) - np.log(self.un_count))
            for first_word in self.bin_prob:
                for second_word in self.bin_prob[first_word]:
                    self.bin_prob[first_word][second_word] = -(
                        np.log(self.bin_prob[first_word][second_word])
                        - np.log(self.bin_count[first_word])
                    )

    def get_un_prob(self, word):
        word = word.lower()
        if word in self.un_prob:
            return self.un_prob[word]
        else:
            return 100  # TODO

    def get_bin_prop(self, first_word, second_word):
        first_word = first_word.lower()
        second_word = second_word.lower()
        if first_word in self.bin_prob:
            if second_word in self.bin_prob[first_word]:
                return self.bin_prob[first_word][second_word]
            else:
                return 100  # TODO
        else:
            return 100  # TODO

    def get_query_prob(self, query):
        words = split(query.lower())
        if len(words) == 0:
            return 0
        prob = self.get_un_prob(words[0])
        for i in range(1, len(words)):
            prob += self.get_bin_prop(words[i - 1], words[i])
        return prob

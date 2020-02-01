# import Levenshtein
from collections import defaultdict
import utils
import numpy as np
import json


class ErrorModel:
    def __init__(self):
        self.un_prob = defaultdict(lambda: defaultdict(float))
        self.bin_prob = defaultdict(lambda: defaultdict(float))

        self.un_count = defaultdict(float)
        self.bin_count = defaultdict(float)

    def store(self, file_name='em_dump.json'):
        with open(file_name, 'w') as file:
            file.write(json.dumps((self.un_prob, self.bin_prob, self.un_count, self.bin_count)))

    def load(self, file_name='em_dump.json'):
        with open(file_name, 'r') as file:
            dump = json.loads(file.read().decode('utf8'))
            self.un_prob = dump[0]
            self.bin_prob = dump[1]
            self.un_count = dump[2]
            self.bin_count = dump[3]

    # def fit(self, file_name='queries_all.txt'):
    #     with open(file_name, 'r') as file:
    #         for line in file:
    #             line = line.decode('utf8')
    #             parts = line.split('\t')
    #             if len(parts) == 1:
    #                 continue
    #
    #             sep_sym = '='
    #
    #             fix = parts[0].lower()
    #             fix = sep_sym.join(utils.split(fix))
    #             orig = parts[1].lower()
    #             orig = sep_sym.join(utils.split(orig))
    #
    #             fix = fix + '^'
    #             orig = orig + '^'
    #             idx_fix = 0
    #             idx_orig = 0
    #
    #             eds = Levenshtein.editops(fix, orig)
    #             for ed in eds:
    #                 if ed[0] == 'insert':
    #                     fix = utils.insert_in_str(fix, ed[1] + idx_fix, '_')
    #                     idx_fix += 1
    #                 if ed[0] == 'delete':
    #                     orig = utils.insert_in_str(orig, ed[2] + idx_orig, '_')
    #                     idx_orig += 1
    #
    #             for i in range(1, len(fix)):
    #                 self.un_prob[fix[i]][orig[i]] += 1
    #                 self.un_count[fix[i]] += 1
    #                 if fix[i-1] == sep_sym or fix[i] == sep_sym \
    #                    or orig[i-1] == sep_sym or orig[i] == sep_sym:
    #                     continue
    #                 self.bin_prob[fix[i-1: i+1]][orig[i-1: i+1]] += 1
    #                 self.bin_count[fix[i-1: i+1]] += 1
    #
    #         for k1 in self.un_prob:
    #             for k2 in self.un_prob[k1]:
    #                 self.un_prob[k1][k2] = -(np.log(self.un_prob[k1][k2]) - np.log(self.un_count[k1]))
    #         for k1 in self.bin_prob:
    #             for k2 in self.bin_prob[k1]:
    #                 self.bin_prob[k1][k2] = -(np.log(self.bin_prob[k1][k2]) - np.log(self.bin_count[k1]))

    def get_un_prob(self, orig, fix):
        if not(len(orig) == 1 and len(fix) == 1):
            raise ValueError
        if fix in self.un_prob:
            if orig in self.un_prob[fix]:
                return self.un_prob[fix][orig]
        return 100  # TODO

    def get_bin_prob(self, orig, fix):
        if not (len(orig) == 2 and len(fix) == 2):
            raise ValueError
        if fix in self.bin_prob:
            if orig in self.bin_prob[fix]:
                return self.bin_prob[fix][orig]
        return 100  # TODO

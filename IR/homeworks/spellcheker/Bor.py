class Node:
    def __init__(self, word="", children=None, prob=None):
        if children is None:
            children = {}
        self.word = word
        self.children = children
        self.prob = prob


class Bor:
    def __init__(self, lang_model, err_model):
        self.root = Node()
        self.lang_model = lang_model
        self.err_model = err_model

    def fit(self):
        for word in self.lang_model.un_prob:
            cur_node = self.root
            for idx, ch in enumerate(word):
                if ch in cur_node.children:
                    cur_node = cur_node.children[ch]
                else:
                    cur_node.children[ch] = Node(word=word[: idx+1])
                    cur_node = cur_node.children[ch]
                if cur_node.word == word:
                    cur_node.prob = self.lang_model.un_prob[word]

    def _un_search(self, word, start_node=None, start_weight=0):
        if start_node is None:
            start_node = self.root
        if start_weight > self.max_weight:
            return []

        if word == "":
            if start_node.prob is not None:
                return [(start_node.word, start_node.prob, start_weight)]
            else:
                return []

        candidates = []

        # change
        for child in start_node.children:
            if child != word[0]:
                new_weight = start_weight + self.err_model.get_un_prob(child, word[0])
            else:
                new_weight = start_weight

            candidates += self._un_search(
                word=word[1:],
                start_node=start_node.children[child],
                start_weight=new_weight
            )

        # insert
        for child in start_node.children:
            candidates += self._un_search(
                word=word,
                start_node=start_node.children[child],
                start_weight=start_weight + self.err_model.get_un_prob(child, '_')
            )

        # delete
        candidates += self._un_search(
            word=word[1:],
            start_node=start_node,
            start_weight=start_weight + self.err_model.get_un_prob('_', word[0])
        )

        return candidates

    # def _bin_search(self, word, start_node=None, start_weight=0):
    #     if start_node is None:
    #         start_node = self.root
    #     if start_weight > self.max_weight:
    #         return []
    #
    #     if word == "^":
    #         if start_node.prob is not None:
    #             return [(start_node.word, start_node.prob, start_weight)]
    #         else:
    #             return []
    #
    #     candidates = []
    #
    #     # change
    #     for child in start_node.children:
    #         if child != word[0]:
    #             new_weight = start_weight + self.err_model.get_un_prob(child, word[0])
    #         else:
    #             new_weight = start_weight
    #
    #         candidates += self._un_search(
    #             word=word[1:],
    #             start_node=start_node.children[child],
    #             start_weight=new_weight
    #         )
    #
    #     return candidates

    def best_match(self, word, alpha, beta, max_weight, match_num=None, max_diff=None):
        self.max_weight = max_weight
        matches = self._un_search(word)
        matches.sort(key=lambda tup: alpha * tup[1] + beta * tup[2])
        if len(matches) == 0:
            return []
        best_weight = matches[0][2]
        res = []
        for e in matches:
            if max_diff is not None and e[2] - best_weight > max_diff:
                break
            if e[0] not in res:
                res.append(e[0])
                if match_num is not None and len(res) == match_num:
                    break

        return res

#!/usr/bin/env python
# -*- coding: utf8 -*-
import re

SPLIT_RGX = re.compile(ur'[A-Za-zА-Яа-я0-9]+', re.UNICODE)


def split(string):
    words = re.findall(SPLIT_RGX, string)
    return words


class LayoutSwitcher:
    def __init__(self):
        self.en_keyboard = u"qwertyuiop[]asdfghjkl;\'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?|@#$^&`~"
        self.ru_keyboard = u"йцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,/\"№;:?ёЁ"
        self.ru_to_en = {ord(c): ord(t) for c, t in zip(self.ru_keyboard, self.en_keyboard)}
        self.en_to_ru = {ord(c): ord(t) for c, t in zip(self.en_keyboard, self.ru_keyboard)}

    def switch_ru_to_en(self, string):
        return string.translate(self.ru_to_en)

    def switch_en_to_ru(self, string):
        return string.translate(self.en_to_ru)


def insert_in_str(string, index, sym):
    return string[:index] + sym + string[index:]

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from six import PY2, PY3
from six.moves import filter, map, range

import collections


class ParseError(Exception):
    pass


class ContentLine:

    def __eq__(self, other):
        ret = (self.name == other.name
            and self.params == other.params
            and self.value == other.value)
        return ret

    __ne__ = lambda self, other: not self.__eq__(other)

    def __init__(self, name, params={}, value=''):
        self.name = name
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';{}={}'.format(pname, ','.join(self.params[pname]))
        return "{}{}:{}".format(self.name, params_str, self.value)

    def __repr__(self):
        return "<ContentLine '{}' with {} parameters. Value='{}'>".format(self.name, len(self.params), self.value)

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(klass, line):
        if ':' not in line:
            raise ParseError("No ':' in line '{}'".format(line))

        # Separe key and value
        splitted = line.split(':')
        key, value = splitted[0], ':'.join(splitted[1:]).strip()

        # Separe name and params
        splitted = key.split(';')
        name, params_strings = splitted[0], splitted[1:]

        # Separe key and values for params
        params = {}
        for paramstr in params_strings:
            if '=' not in paramstr:
                raise ParseError("No '=' in line '{}'".format(line))
            splitted = paramstr.split('=')
            pname, pvals = splitted[0], '='.join(splitted[1:])
            params[pname] = pvals.split(',')
        return klass(name, params, value)


class Container(list):
    def __init__(self, name, *items):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        content_str = '\n'.join(map(str, self))
        if content_str:
            content_str = '\n' + content_str
        return 'BEGIN:{}{}\nEND:{}'.format(self.name, content_str, self.name)

    def __repr__(self):
        return "<Container '{}' with {} elements>".format(self.name, len(self))

    @classmethod
    def parse(klass, name, tokenized_lines):
        items = []
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(Container.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value != name:
                    raise ParseError("Expected END:{}, got END:{}".format(name, line.value))
                break
            else:
                items.append(line)
        return klass(name, *items)


def unfold_lines(physical_lines):
    if not isinstance(physical_lines, collections.Iterable):
        # TODO : better error
        raise ParseError('Not an iterable')
    current_line = ''
    for line in physical_lines:
        if len(line.strip()) == 0:
            continue
        elif not current_line:
            current_line = line
        elif line[0] == ' ':
            current_line += line[1:]
        else:
            yield(current_line)
            current_line = line
    if current_line:
        yield(current_line)


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        yield ContentLine.parse(line)


def parse(tokenized_lines, block_name=None):
    res = []
    for line in tokenized_lines:
        if line.name == 'BEGIN':
            res.append(Container.parse(line.value, tokenized_lines))
        else:
            res.append(line)
    return res


def lines_to_container(lines):
    return parse(tokenize_line(unfold_lines(lines)))


def string_to_container(txt):
    return lines_to_container(txt.split('\n'))

if __name__ == "__main__":
    from tests.fixture import cal1

    def printTree(elem, lvl=0):
        if isinstance(elem, list) or isinstance(elem, Container):
            if isinstance(elem, Container):
                print("{}{}".format('   ' * lvl, elem.name))
            for sub_elem in elem:
                printTree(sub_elem, lvl + 1)
        elif isinstance(elem, ContentLine):
            print("{}{}{}".format('   ' * lvl, elem.name, elem.params, elem.value))
        else:
            print("Wuuut ?")

    cal = string_to_container(cal1)
    printTree(cal)
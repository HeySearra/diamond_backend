from collections import defaultdict, deque
from typing import List, Tuple, Callable

from utils.algorithm import greedy_merge_lcs


class OuterXMLParser(object):

    def __init__(self, xml_content: str):
        self.s = xml_content

    def walk(self, without_tag=True):
        cur, n = 0, len(self.s)
        while cur < n:
            lhs_begin = self.s.find('<', cur)
            if lhs_begin == -1:
                break
            lhs_end = self.s.find('>', lhs_begin) + 1
            if lhs_end == 0:
                raise ValueError

            clz = self.s[lhs_begin + 1:lhs_end - 1].split()[0]
            rhs_str = f'</{clz}>'
            rhs_begin = self.s.find(rhs_str, lhs_end)
            if rhs_begin == -1:
                raise ValueError
            rhs_end = rhs_begin + len(rhs_str)

            yield self.s[lhs_begin:rhs_end] if without_tag else ((lhs_begin, lhs_end, rhs_begin, rhs_end), clz)
            cur = rhs_end


def filter_comment(xml: str):
    old_l = list(OuterXMLParser(xml).walk(False))
    i = 0
    l = []
    for (lhs_begin, lhs_end, rhs_begin, rhs_end), clz in old_l:
        if clz == 'comment-start' or clz == 'comment-end':
            l.append(xml[i:lhs_begin])
            i = rhs_end
    l.append(xml[i:])
    return ''.join(l)


def unordered_discretization(xml1: str, xml2: str):
    def _disc_apply(s: str) -> int:
        nonlocal disc_dct, disc_cnt
        if disc_dct[s] == 0:
            disc_dct[s], disc_cnt = disc_cnt, disc_cnt + 1
        return disc_dct[s]

    disc_dct, disc_cnt = defaultdict(int), 1

    return tuple(
        [_disc_apply(s) for s in OuterXMLParser(xx).walk()]
        for xx in (xml1, xml2)
    )


def xml_auto_merge(xml1, xml2):
    seq1: List[str] = list(OuterXMLParser(str(xml1)).walk())
    seq2: List[str] = list(OuterXMLParser(str(xml2)).walk())

    merged = greedy_merge_lcs(seq1, seq2)
    return merged


if __name__ == '__main__':
    print(xml_auto_merge(
        '<p>123</p><p>bcd</p>',
        '<p>123def</p>',
    )
    )
    # print(xml_auto_merge_available(
    #     '<p>我</p><p>你</p>',
    #     '<p>我</p><p>他</p><p>你是谁</p>')
    # )
    # print(xml_auto_merge_available(
    #     '<p>1</p><p>3</p><p>2</p>',
    #     '<p>1</p><p>3</p>')
    # )


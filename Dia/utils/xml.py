from collections import defaultdict, deque
from typing import List, Tuple, Callable

from utils.algorithm import greedy_merge_lcs


class OuterXMLParser(object):

    def __init__(self, xml_content: str):
        self.s = xml_content

    def walk(self):
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

            yield self.s[lhs_begin:rhs_end]
            cur = rhs_end
    
    def filter_comment(self):
        cur, n, l = 0, len(self.s), []
        while cur < n:
            lhs_begin = self.s.find('<comment-', cur)
            if lhs_begin == -1:
                break
            end_tag = '</comment-'
            rhs_end = self.s.find(end_tag, lhs_begin)
            if rhs_end == -1:
                break
            rhs_end = self.s.find('>', rhs_end) + 1
            l.append(self.s[cur:lhs_begin])
            cur = rhs_end
        l.append(self.s[cur:])
        return ''.join(l)


def filter_comment(xml: str):
    return OuterXMLParser(xml).filter_comment()


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
        '<p>123</p><p>bce</p>',
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
    print(filter_comment("""<p>&nbsp;</p><p>12<comment-start name="aaa:4e6bb"></comment-start>32<comment-end name="aaa:4e6bb"></comment-end>13</p><p>&nbsp;</p>"""))


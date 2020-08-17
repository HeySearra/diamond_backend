from collections import defaultdict, deque
from typing import List, Tuple, Callable

from xmldiff.utils import longest_common_subsequence


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
            
            yield self.s[lhs_end:rhs_begin]
            cur = rhs_end
    
def xml_auto_merge_available(xml1, xml2):
    disc_cnt, disc_dct = 1, defaultdict(int)
    
    def unordered_discretization(xml_content: str):
        nonlocal disc_cnt, disc_dct
        parser = OuterXMLParser(xml_content)
        for text in parser.walk():
            if disc_dct[text] == 0:
                disc_dct[text] = disc_cnt
                disc_cnt += 1

    unordered_discretization(xml1)
    unordered_discretization(xml2)
    
    lcs = longest_common_subsequence('1', '2')

if __name__ == '__main__':
    print(longest_common_subsequence([10, 20, 30], [20, 30]))

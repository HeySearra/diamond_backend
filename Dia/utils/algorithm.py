from collections import defaultdict


class TNode(object):
    def __init__(self, ch='', is_root=False):
        self.ch = ch
        self.is_root = is_root
        self.fail, self.fa = None, None
        self._next = {}
    
    def __call__(self):
        yield self._next
    
    def __iter__(self):
        return iter(self._next.keys())
    
    def __getitem__(self, item):
        return self._next[item]
    
    def __setitem__(self, key, value):
        self._next.setdefault(key, value).fa = self
    
    def __repr__(self):
        return f"<TNode object '{self.ch}' at {object.__repr__(self)[1:-1].split('at')[-1]}>"
    
    def __str__(self):
        return self.__repr__()


class AhoCorasick(object):
    def __init__(self, *words):
        self.w_set = set(words)
        self.w_li = sorted(list(self.w_set), key=lambda x: len(x))
        self._root = TNode(is_root=True)
        self._node_meta = defaultdict(set)
        self._node_all = [(0, self._root)]
        _ch_set = {}
        for word in self.w_li:
            for w in word:
                _ch_set.setdefault(w, set())
                _ch_set[w].add(word)
        
        def insert(s):
            if len(s) == 0:
                return
            cur = self._root
            for i, ch in enumerate(s):
                node = TNode(ch)
                if ch in cur:
                    pass
                else:
                    cur[ch] = node
                    self._node_all.append((i + 1, cur[ch]))
                if i >= 1:
                    for j in _ch_set[ch]:
                        if s[:i + 1].endswith(j):
                            self._node_meta[id(cur[ch])].add((j, len(j)))
                cur = cur[ch]
            else:
                if cur != self._root:
                    self._node_meta[id(cur)].add((s, len(s)))
        
        for word in self.w_li:
            insert(word)
        self._node_all.sort(key=lambda x: x[0])
        self._build()
    
    def _build(self):
        for _level, node in self._node_all:
            if node == self._root or _level <= 1:
                node.fail = self._root
            else:
                _node = node.fa.fail
                while True:
                    if node.ch in _node:
                        node.fail = _node[node.ch]
                        break
                    else:
                        if _node == self._root:
                            node.fail = self._root
                            break
                        else:
                            _node = _node.fail
    
    def match(self, content, with_index=False):
        result = set()
        node = self._root
        index = 0
        for i in content:
            while 1:
                if i not in node:
                    if node == self._root:
                        break
                    else:
                        node = node.fail
                else:
                    for keyword, keyword_len in self._node_meta.get(id(node[i]), set()):
                        if not with_index:
                            result.add(keyword)
                        else:
                            result.add((keyword, (index - keyword_len + 1, index + 1)))
                    node = node[i]
                    break
            index += 1
        return result


def LCS(leq, riq, eq_fn=lambda x, y: x == y):
    
    start = 0
    lend = lslen = len(leq)
    rend = rslen = len(riq)
    
    while start < lend and start < rend and eq_fn(leq[start], riq[start]):
        start += 1
    while start < lend and start < rend and eq_fn(leq[lend - 1], riq[rend - 1]):
        lend -= 1
        rend -= 1
    
    left = leq[start:lend]
    right = riq[start:rend]
    lmax, rmax = len(left), len(right)
    furthest = {1: (0, [])}
    
    if not lmax + rmax:
        r = range(lslen)
        return zip(r, r)
    for d in range(0, lmax + rmax + 1):
        for k in range(-d, d + 1, 2):
            if (k == -d or
                    (k != d and furthest[k - 1][0] < furthest[k + 1][0])):
                old_x, history = furthest[k + 1]
                x = old_x
            else:
                old_x, history = furthest[k - 1]
                x = old_x + 1
            
            history = history[:]
            y = x - k
            
            while x < lmax and y < rmax and eq_fn(left[x], right[y]):
                history.append((x + start, y + start))
                x += 1
                y += 1
            
            if x >= lmax and y >= rmax:
                # This is the best match
                return [(e, e) for e in range(start)] + history + \
                       list(zip(range(lend, lslen), range(rend, rslen)))
            else:
                furthest[k] = (x, history)


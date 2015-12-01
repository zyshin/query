from nltk.corpus import wordnet as WN


EXCEPT = {'her': 'she', 'him': 'he', 'his': 'he', 'its': 'its', 'me': 'I',
          'others': 'other', 'our': 'we', 'their': 'they', 'them': 'they', 'us': 'we',
          'your': 'you', 'yourselves': 'yourself'}


def lemmatize(s):
    # s: English word only
    # return: lower & retain '?'
    s = s.lower()
    q = ''
    if s.endswith('?'):
        s, q = s.strip('?'), '?'
    l = EXCEPT[s] if s in EXCEPT else WN.morphy(s)    # morphy may return None!
    if not l:
        l = s
    return l+q


def synonyms(w):
    r = set()
    ss = WN.synsets(w)
    for s in ss:
        for l in s.lemmas():
            if '_' not in l.name():
                r.add(l.name())
    if w in r:
        r.remove(w)
    r = list(r)
    r.insert(0, w)
    # w is the first in results
    return tuple(r)

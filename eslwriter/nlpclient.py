import requests
from django.conf import settings

from common.utils import timeit

@timeit
def lemmatize(s):
    # s: English word only
    # return: lower & retain '?'
    s, q = s.lower(), ''
    if s.endswith('?'):
        s, q = s[0:-1], '?'
    try:
        # TODO: add [requests-cache] (https://github.com/reclosedev/requests-cache)
        r = requests.post(settings.NLPSERVER_URL, params=settings.NLPSERVER_LEMMATIZE_PROPS, data=s)
        l = r.text.split('\t')[2]
    except Exception, e:
        print repr(e)
        print r.url, s
        l = s
    return l+q
    
# def synonyms(w):
#     r = set()
#     ss = WN.synsets(w)
#     for s in ss:
#         for l in s.lemmas():
#             if '_' not in l.name():
#                 r.add(l.name())
#     if w in r:
#         r.remove(w)
#     r = list(r)
#     r.insert(0, w)
#     # w is the first in results
#     return tuple(r)

import re, sys
from itertools import product
from collections import Iterable

from django.conf import settings

from common.models import *
from common.utils import mongo_get_object, mongo_get_object_or_404, timeit
from .wordnet import lemmatize, synonyms
from .translator import is_cn, translate


global dt2i, i2dt, pt2i, i2pt, t2i, i2t
dbc = settings.DBC
deps = list(dbc.common.deps.find())
dt2i = dict([(d['dt'], d['_id']) for d in deps])
i2dt = dict([(d['_id'], d['dt']) for d in deps])
poss = list(dbc.common.poss.find())
pt2i = dict([(p['pt'], p['_id']) for p in poss])
i2pt = dict([(p['_id'], p['pt']) for p in poss])
del deps, poss 

if True:
    class MongoDict:
        def __init__(self, get_func):
            self.get = get_func

    def t2i_get(t, default=None):
        o = dbc.common.tokens.find_one({'t': t}, {'_id': 1})
        if o:
            return o['_id']
        return default

    def i2t_get(i, default=None):
        o = dbc.common.tokens.find_one({'_id': i}, {'_id': 0, 't': 1})
        if o:
            return o['t']
        return default

    t2i = MongoDict(t2i_get)
    i2t = MongoDict(i2t_get)
else:
    print 'loading wordnet'
    lemmatize('')
    print 'loading tokens'
    tokens = list(dbc.common.tokens.find())
    t2i = dict([(t['t'], t['_id']) for t in tokens])
    i2t = dict([(t['_id'], t['t']) for t in tokens])
    del tokens


def tt2ii(tt, ignore=True):  # * -> 0
    if ignore:
        ii = [t2i.get(t, -1) if t != '*' else 0 for t in tt]
        return [i for i in ii if i != -1]
    return [t2i.get(t, t) if t != '*' else 0 for t in tt]


def ii2tt(ii):
    return [i2t.get(i, i) for i in ii]


# query processing

def elem_match(D, d):
    # check if d in D
    for k, v in d.iteritems():
        if k not in D or D[k] != v:
            return False
    return True


def find_elem_match(L, d):
    for i, D in enumerate(L):
        if elem_match(D, d):
            return i, D
    assert False, 'no match'


def find_all_tokens(T, l):
    return [i for i, t in enumerate(T) if t['l'] == l]


def find_best_match(S, ii, dd, ref):
    # ll = find_isolated_tokens(ii, dd)
    qlen = len(ii)
    positions = [None] * qlen  #candidate indices in sentences
    for d in dd:
        dt, i1, i2 = d
        qd = {'dt': dt, 'l1': ii[i1], 'l2': ii[i2]}
        di, dr = find_elem_match(S['d'], qd)
        positions[i1], positions[i2] = (dr['i1'],), (dr['i2'],)
    for i in xrange(qlen):
        if not positions[i]:
            positions[i] = find_all_tokens(S['t'], ii[i])
    best_m = []
    best_c = -1
    for m in product(*positions):
        # print 'm: ', m
        cost = match_cost(S['t'], m, ref)
        if best_c < 0 or cost < best_c:
            best_c = cost
            best_m = m
    return best_m, best_c


def match_cost(T, m, ref):
    #TODO: dependency award
    if len(m) != len(ref):
        return sys.maxint
    qlen = len(m)
    
    posCost = 0
    for i in xrange(qlen-1):
        delta = m[i+1] - m[i]
        if delta <= 0:
            posCost += 4-delta    #non-monotonicity penalty
        else:
            posCost += delta-1  #distance penalty
    
    queryCost = 0
    for i in xrange(qlen):
        if T[m[i]]['w'] != ref[i]: #case insensitive
            queryCost += 2  #query mismatch penalty
    
    formCost = 0
    for i in m:
        if T[i]['w'] != T[i]['l']:
            formCost += 1    # word != lemma penalty, 'writing' -> 'writing' > 'write' > 'writes' > ...
    
    return posCost + queryCost + formCost


def expanded_deps(iiii, dd, cids):
    r = iiii[:]
    for dt, i1, i2 in dd:
        k = None
        if 0 in r[i1]:
            k, k2 = 'l2', 'l1'
            ri, ri2 = i2, i1
        elif 0 in r[i2]:
            k, k2 = 'l1', 'l2'
            ri, ri2 = i1, i2
        if k:
            d = {}
            # disable '?' for efficiency
            pipeline = [{'$match': {'d': {'$elemMatch': {'dt': dt, k: {'$in': r[ri][:1]}}}}}]
            pipeline.append({'$project': {'_id': 0, 'd.l1': 1, 'd.l2': 1, 'd.dt': 1}})
            pipeline.append({'$unwind': '$d'})
            pipeline.append({'$match': {'d.dt': dt, 'd.'+k: {'$in': r[ri][:1]}}})
            pipeline.append({'$group': {'_id': '$d.'+k2, 'c': {'$sum': 1}}})
            # pipeline.append({'$sort': {'c': -1}})
            # pipeline.append({'$limit': settings.MAX_RESULT_LENGTH})
            for cid in cids:
                for o in dbc.sentences[str(cid)].aggregate(pipeline):
                    d[o['_id']] = d.get(o['_id'], 0) + o['c']
            r[ri2] = [i for i, c in sorted(d.iteritems(), key=lambda kv: kv[1], reverse=True)[:2*settings.MAX_GROUP_COUNT]]
    return r


def expanded_token(t):
    assert type(t) == type('') or type(t) == type(u''), 't is type of %s' % type('')
    # translate Chinese keywords & synonym expansion according to '?'
    if is_cn(t):
        return translate(t.strip('?'))
    elif t.endswith('?'):
        return synonyms(t.strip('?'))
    else:
        return (t,)

# TODO: use NLTK to split tokens
def split_query(q):
    tokens = q.split()
    lent = len(tokens)
    words, deps = [], []
    for i in xrange(lent):
        t_1 = tokens[i-1] if i > 0 else None
        t = tokens[i]
        t1 = tokens[i+1] if i < lent-1 else None
        if t in dt2i:
            if t_1 in dt2i or t1 in dt2i:
                return [], []
            # deps.append((dt2i[t], len(words)-1, len(words)))
            deps.append((dt2i[t], t_1, t1))
        else:
            if t_1 not in dt2i and t1 not in dt2i:
                if t == '*':
                    return [], []
                words.append(t)
    return words, deps


def check_query_str(q):
    assert type(q) == type('') or type(q) == type(u''), 'q is None'
    if len(q) > settings.MAX_QUERY_LENGTH:
        return 1
    return 0


# TODO: use NLTK to split tokens
# TODO: Chinese word split
def parse_query_str(q):
    token = q.split()
    # print "tokens = ", token
    lent = len(token)
    # print "lent = ", lent
    qtt, qdd = [], []
    for i in xrange(lent):
        # print "i = ", i
        t_1 = token[i - 1] if i > 0 else None
        t = token[i]
        t1 = token[i + 1] if i < lent - 1 else None
        if t in dt2i:
            if t_1 in dt2i or t1 in dt2i:
                return qtt, qdd
            qdd.append((dt2i[t], len(qtt)-1, len(qtt)))
        else:
            assert t, 't is empty'
            qtt.append(t)
    # qtt: unprocessed token string, include */?
    # qdd: relationship between qtt: (dt, i1 in qtt, i2 in qtt)
    return qtt, qdd


def find_isolated_tokens(ii, dd):
    # find tokens that not in a dep relationship
    dii = set()
    for dt, i1, i2 in dd:
        dii.add(i1)
        dii.add(i2)
    return [i for i in xrange(len(ii)) if i not in dii]


def strip_query(q): # split q, ignore '(dt)' and '?'
    q = re.sub(r'\(\w+\)', '', q, flags=re.UNICODE)
    rawq = q.split()
    tt = [t.replace('?', '') for t in rawq]
    tt = [translate(t)[0] if is_cn(t) else t for t in tt] #get first translation
    return rawq, tt


def is_list_or_tuple(o):
    return isinstance(o, list) or isinstance(o, tuple)


def format_query(ll, dd):
    # ll: [0*, l1, l2, ...], ISOLATED!
    # dd: [(dt, l1, l2), ...]
    # sorted max big -> max small
    q = {}
    if ll:
        q['t.l'] = {'$all': sorted(ll, reverse=True)}  #$all needs array but itemgetter return tuple.
    if dd:
        # qdd = [{'dt': dt, 'l1': l1, 'l2': l2} for dt, l1, l2 in dd]
        qdd = [{'dt': dt, 'l1': {'$in': l1} if is_list_or_tuple(l1) else l1, 'l2': {'$in': l2} if is_list_or_tuple(l2) else l2} for dt, l1, l2 in dd]
        q['d'] = {'$all': [{ '$elemMatch': d } for d in qdd]};
    return q


# generating views

global PUNCT_DICT
PUNCT_DICT = {"-LRB-":"(\b", "-RRB-":"\b)", "-LSB-":"[\b", "-RSB-":"\b]", "-LCB-":"{\b", "-RCB-":"\b}", "<":'<', ">":'>', "``":'"\b', "''":'\b"', "...":"\b...", ",":"\b,", ";":"\b;", ":":"\b:", "@":"\b@", "%":"\b%", "&":"&", ".":"\b.", "?":"\b?", "!":"\b!", "*":"\b*", "'":"\b'", "'m":"\b'm", "'M":"\b'M", "'d":"\b'd", "'D":"\b'D", "'s":"\b's", "'S":"\b'S", "'ll":"\b'll", "'re":"\b're", "'ve":"\b've", "n't":"\bn't", "'LL":"\b'LL", "'RE":"\b'RE", "'VE":"\b'VE", "N'T":"\bN'T", "`":"'\b"}
def cleaned_sentence(tokens, highlights):
    tt = [PUNCT_DICT.get(t, t) for t in tokens]
    for i in highlights:
        tt[i] = '<strong>%s</strong>' % tt[i]
    r = ' '.join(tt)
    r = r.replace(' \b', '')
    r = r.replace('\b ', '')
    r = r.replace(' <strong>\b', '<strong>')
    r = r.replace('\b</strong> ', '</strong>')
    return r


def paper_source_str(pid):
    s = {}
    p = mongo_get_object(DblpPaper, pk=pid)
    if not p:
        p = mongo_get_object_or_404(UploadRecord, pk=pid)
        s['source'] = 'Uploaded file: ' + p['title']
        return s
    # TODO: precompute source string and save to $common.uploads
    year = p['info'].get('year')
    title = p['info'].get('title', {}).get('text')
    authList = p['info'].get('authors', {}).get('author', [])

    source = ''
    v = mongo_get_object(DblpVenue, pk=p['venue'])
    if v:
        conference = v.get('shortName', v['fullName'])
        if year and len(year) == 4:
            conference += "'" + year[2:4]
        source += conference + '. '

        if authList:
            nameList = authList[0].split()  #split first author's name
            authorShort = nameList[0][0].upper() + '. ' +nameList[len(nameList)-1]
            if len(authList) > 1:
                authorShort += ' et. al.'
            else:
                authorShort += '.'
            source += authorShort
        source += title
    return {'source': source, 'url': p['url']}


def distribution_statistic(distribution, precision=0.001):
    keyword_total = len(distribution)
    sorted_distribution = [[[], []] for x in range(keyword_total)]
    for x in range(len(distribution)):
        for i in range(2):
            sorted_distribution[x][i] = sorted(distribution[x][i], key=lambda pos: pos[0])
    y_array = [[0 for i in range(int(1 / precision + 0.001))] for x in range(keyword_total)]
    for x in range(keyword_total):
        current = 0
        first_index = 0
        second_index = 0
        total = 0.0
        minus = 0.0
        length = len(sorted_distribution[x][0])
        while current * precision < 1.0 and first_index < length:
            if sorted_distribution[x][0][first_index][0] < current * precision:
                total += sorted_distribution[x][0][first_index][1]
                first_index += 1
            else:
                y_array[x][current] = total
                current += 1
        while current * precision < 1.0:
            y_array[x][current] = total
            current += 1
        current = 0
        while current * precision < 1.0 and second_index < length:
            if sorted_distribution[x][1][second_index][0] < current * precision:
                minus += sorted_distribution[x][1][second_index][1]
                second_index += 1
            else:
                y_array[x][current] -= minus
                current += 1
        while current * precision < 1.0:
            y_array[x][current] -= minus
            current += 1
    return y_array
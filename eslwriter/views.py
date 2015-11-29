# -*- coding: utf-8 -*-
import json
# import os
# import sys
# import commands
# import hashlib
# import math
# import urllib, urllib2
# from itertools import product, groupby
from operator import itemgetter

# from django.conf import settings
from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from django.core.cache import cache
# from django.core.urlresolvers import reverse
# from django.utils.decorators import method_decorator

from .utils import *
from common.models import Field
from common.utils import make_response, timeit


@timeit
def home_view(request):
    q = request.GET.get('q', '').strip()
    error = check_query_str(q)
    if not q or error != 0:
        return render(request, 'eslwriter/index.html', {'error': error})

    # print 'home_view:', q
    qtt, qdd = parse_query_str(q)
    ll = [t if is_cn(t) else lemmatize(t) for t in qtt]  # lemmatize with '?'
    llll = [expanded_token(l) for l in ll]  # translate Chinese keywords & synonym expansion
    iiii = [tt2ii(tt) for tt in llll]  # lemma id
    ref_wwii = tt2ii([t.strip('?').lower() for t in qtt])   #for sorting

    # query groups
    profile = {'field': settings.DEFAULT_FID, 'pub_corpora': settings.DEFAULT_CIDS}
    profile.update(mongo_get_object(UserProfile, pk=request.user.pk) or {})
    profile['field'] = mongo_get_object(Field, pk=profile['field'])['name']
    # cids = ['dac', 'date', 'icpp', 'icdcs', 'iccad', 'ipdps', 'isca', 'podc', 'iccd', 'ics', 'hpca', 'sc', 'spaa',
    # 'asplos', 'hpdc', 'acm_trans_embedded_comput_syst_tecs_', 'acm_trans_design_autom_electr_syst_todaes_', 'ppopp',]
    # print 'len(cids) =', len(cids)
    # pub_cids = cids
    pri_cids, pub_cids = _get_cids(profile)
    if pri_cids:
        l = UserCorpus.objects.filter(pk=pri_cids[0])
        if l.count():
            profile['pri_corpus'] = l[0]
    pub_gr = group_query(iiii, qdd, pub_cids, ref_wwii)
    pri_gr = group_query(iiii, qdd, pri_cids, ref_wwii) if pri_cids else []
    return render(request, 'eslwriter/result.html', {'profile': profile, 'q': q, 'pub_gr': pub_gr, 'pri_gr': pri_gr})


@timeit
def dep_query_view(request):
    q = request.GET.get('q', '').strip()
    error = check_query_str(q)
    if not q or error != 0:
        return render(request, 'eslwriter/index.html', {'error': error})

    qtt, qdd = parse_query_str(q)
    qlen = len(qtt)

    profile = mongo_get_object(UserProfile, pk=request.user.pk)
    pri_cids, pub_cids = _get_cids(profile)
    cids = pub_cids + pri_cids

    gr = []
    if (qlen == 1 or qlen == 2) and cids:
        tt = [t.strip('?') for t in qtt[:2]]
        tt = [translate(t)[0] if is_cn(t) else t for t in tt]
        tt = [lemmatize(t) for t in tt]
        llii = tt2ii(tt)

        l1 = llii[0]
        if qlen == 1:
            qtt.append('*')
            l2 = 0
        else:
            l2 = llii[1]
        gr = dep_query(l1, l2, cids)
        gr = [('%s %s %s' % (qtt[i1], i2dt[di], qtt[i2]), cleaned_sentence(ii2tt(wids), highlights)) for i1, i2, di, wids, highlights in gr]

    return make_response(content=json.dumps({ 'gr': gr }), content_type='application/json')


@timeit
def sentence_query_view(request):
    q = json.loads(request.POST.get('qs', '{}'))
    gc = q.get('gc', 0)
    ii = q.get('ii', [])
    dd = q.get('dd', [])
    ref = q.get('ref', [])
    cids = q.get('cids', [])
    # start = int(request.GET.get('s', '0'))  #sentence start index
    # count = int(request.GET.get('c', '100'))
    sr, vis_data = sentence_query(ii, dd, cids, ref)
    total_page_num = (len(sr) - 1) / 10 + 1
    if total_page_num > 10 :
        page_nums_list = [i for i in range(1, 11)]
    else:
        page_nums_list = [i for i in range(1, total_page_num + 1)]
    return render(request, 'eslwriter/sentence_result.html', {'gc': gc, 'sr': sr, 'page_nums_list': page_nums_list, 'vis_data': vis_data})

@timeit
def group_query(iiii, dd, cids, ref):
    # iiii: [(0,)*, (2, 3), (4, 5), ...]
    # dd: [((dt, i1, i2), ...]
    isolated = find_isolated_tokens(iiii, dd)
    gr = []
    for ii in product(*expanded_deps(iiii, dd, cids)):
        isolated_ll = [ii[i] for i in isolated]
        qdd = [(dt, ii[i1], ii[i2]) for dt, i1, i2 in dd]
        q = format_query(isolated_ll, qdd)
        c = group_count_query(q, cids)
        if c:
            gr.append((ii, dd, c))  #[... for ii, dd, c in gr]
    gr = sorted(gr, key=itemgetter(2), reverse=True)[:settings.MAX_GROUP_COUNT]	# TODO: tf-idf sorting
    gr = [{'s': ' ... '.join(ii2tt(ii)), 'c': c, 'qs': json.dumps({'gc': c, 'ii': ii, 'dd': dd, 'cids': cids, 'ref': ref})} for ii, dd, c in gr]
    # TODO: unified cids and ref for whole gr
    # TODO: switch the order of product and cids
    return gr


def group_count_query(q, cids):
    count = 0
    if not q:
        return count
    dbc = settings.DBC
    for cid in cids:
        count += dbc.sentences[str(cid)].count(q, limit=5000)	# limit=9973
    return count


@timeit
def sentence_query(ii, dd, cids, ref, start=0, count=100):
    # ref: query token ids in original form and order
    count = min(count, settings.MAX_SENTENCE_COUNT)
    isolated_ll = [ii[i] for i in find_isolated_tokens(ii, dd)]
    qdd = [(dt, ii[i1], ii[i2]) for dt, i1, i2 in dd]
    q = format_query(isolated_ll, qdd)
    sr, vis_data = [], []
    if not q:
        return sr, vis_data
    dbc = settings.DBC
    n = 0
    for cid in cids:
        _sr = list(dbc.sentences[str(cid)].find(q, {'_id': 0, 't.p': 0}, limit=settings.MAX_RESULT_LENGTH))
        for r in _sr:
            r['m'], r['c'] = find_best_match(r, ii, dd, ref)
            # TODO: ---- add r['m'] to vis_data ----
            sentence_length = len(r['t'])

        # _sr = [r for r in _sr if r['c'] < sys.maxint] #filter out critical unmatch results
        _sr.sort(key=itemgetter('c'))
        _sr = _sr[:count]
        sr += _sr
        n += sum(1 for r in _sr if r['c'] <= 2*len(ii))
        if n >= count:
            break
    sr.sort(key=itemgetter('c'))
    sr = [(paper_source_str(r['p']), cleaned_sentence(ii2tt([t['w'] for t in r['t']]), r['m'])) for r in sr[:count]]
    return sr, vis_data


def dep_query(l1, l2, cids):
    dbc = settings.DBC
    gr1, gr2 = [], []
    dq1, dq2 = {}, {}
    if l1:
        dq1['l1'] = dq2['l2'] = l1
    if l2:
        dq1['l2'] = dq2['l1'] = l2
    for dt in i2dt:
        dq1['dt'] = dq2['dt'] = dt
        for cid in cids:
            collection = dbc.sentences[str(cid)]
            r = collection.find_one({'d': {'$elemMatch': dq1}}, {'_id': 0, 't': 1, 'd.$': 1})
            if r:
                dr = r['d'][0]
                gr1.append((0, 1, dr['dt'], [t['w'] for t in r['t']], (dr['i1'], dr['i2'])))
                break
        for cid in cids:
            collection = dbc.sentences[str(cid)]
            r = collection.find_one({'d': {'$elemMatch': dq2}}, {'_id': 0, 't': 1, 'd.$': 1})
            if r:
                dr = r['d'][0]
                gr2.append((1, 0, dr['dt'], [t['w'] for t in r['t']], (dr['i1'], dr['i2'])))
                break
    return gr1 + gr2


def _get_cids(profile):
    pri_cids = [profile['pri_corpus']] if profile and profile.get('pri_corpus') else []
    pub_cids = profile and profile.get('pub_corpora') or settings.DEFAULT_CIDS
    # TODO: test permission
    # TODO: if pri_corpus.status == 0
    return pri_cids, pub_cids

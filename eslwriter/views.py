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
    # print "request = ",  request
    q = json.loads(request.POST.get('qs', '{}'))
    gc = q.get('gc', 0)
    ii = q.get('ii', [])
    dd = q.get('dd', [])
    ref = q.get('ref', [])
    cids = q.get('cids', [])
    # start = int(request.GET.get('s', '0'))  #sentence start index
    # count = int(request.GET.get('c', '100'))
    sr, vis_dict = sentence_query(ii, dd, cids, ref)
    total_page_num = (len(sr) - 1) / 10 + 1
    if total_page_num > 10 :
        page_nums_list = [i for i in range(1, 11)]
    else:
        page_nums_list = [i for i in range(1, total_page_num + 1)]
    return render(request, 'eslwriter/sentence_result.html',
                  {'gc': gc, 'sr': sr, 'page_nums_list': page_nums_list, 'vis_dict': vis_dict})

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


color_bank = [854151, 1050504, 1247113, 1443722, 1640076, 1771149, 1902222, 2098831, 2229904, 2360977, 2491793, 2622866,
              2753939, 2885012, 3016085, 3081622, 3212695, 3343767, 3474584, 3605657, 3671194, 3802266, 3933339, 4064412,
              4129948, 4261021, 4391838, 4457374, 4588447, 4719519, 4785056, 4916129, 4981409, 5112482, 5243554, 5309091,
              5440163, 5571236, 5636516, 5767588, 5833125, 5964197, 6029734, 6160806, 6291878, 6357159, 6488231, 6553767,
              6684839, 6750376, 6881448, 6946984, 7078056, 7209128, 7274664, 7405736, 7471528, 7602600, 7668136, 7799208,
              7864744, 7996072, 8061608, 8192936, 8258472, 8389800, 8455335, 8586663, 8652199, 8783526, 8849318, 8915110,
              9046437, 9112229, 9243557, 9309348, 9375140, 9506467, 9572259, 9703586, 9769377, 9835425, 9966752, 10032543,
              10098335, 10229662, 10295453, 10361245, 10492572, 10558363, 10624410, 10690202, 10821529, 10887320, 10953111,
              11018902, 11150229, 11216020, 11282068, 11347859, 11413650, 11544977, 11610768, 11676559, 11742350, 11808397,
              11874188, 11939979, 12005770, 12071561, 12202888, 12268680, 12334471, 12400518, 12466309, 12532100, 12597891,
              12663682, 12729473, 12795264, 12861055, 12927102, 12992893, 13058684, 13124475, 13190266, 13256058, 13321849,
              13387640, 13388151, 13453942, 13519733, 13585524, 13651315, 13717106, 13782897, 13848945, 13914736, 13980527,
              13980782, 14046573, 14112364, 14178155, 14243946, 14309994, 14310249, 14376040, 14441831, 14507622, 14573413,
              14573924, 14639715, 14705507, 14771298, 14837089, 14837344, 14903391, 14969182, 15034973, 15035229, 15101020,
              15167067, 15167322, 15233113, 15298904, 15299159, 15365207, 15430998, 15431253, 15497044, 15563091, 15563346,
              15629137, 15694929, 15695440, 15761231, 15761486, 15827277, 15827788, 15893579, 15959371, 15959882, 16025673,
              16025928, 16091975, 16092230, 16158021, 16158532, 16224324, 16224579, 16225090, 16290881, 16291136, 16357183,
              16357438, 16357950, 16423741, 16423996, 16424507, 16490298, 16490809, 16491064, 16556856, 16557367, 16557622,
              16558133, 16558388, 16624435, 16624691, 16625202, 16625457, 16625968, 16626223, 16626735, 16626990, 16693037,
              16693292, 16693804, 16694059, 16694570, 16694826, 16695337, 16630313, 16630568, 16631079, 16631335, 16631847,
              16632358, 16632614, 16567589, 16567845, 16568357, 16568869, 16503588, 16504100, 16504612, 16439332, 16439844,
              16374820, 16375077, 16310053, 16310565, 16245285, 16245797, 16180774, 16181286, 16116006, 16116519, 16051495,
              15986215, 15986727, 15921703, 15856678, 15856933, 15791908, 15792417]


@timeit
def sentence_query(ii, dd, cids, ref, start=0, count=100):
    # ref: query token ids in original form and order
    count = min(count, settings.MAX_SENTENCE_COUNT)
    isolated_ll = [ii[i] for i in find_isolated_tokens(ii, dd)]
    qdd = [(dt, ii[i1], ii[i2]) for dt, i1, i2 in dd]
    q = format_query(isolated_ll, qdd)
    sr = []
    keyword_total = len(ii)
    precision = 0.005
    color_step = 1.0 / 256
    vis_dict = dict()
    vis_data = [[] for x in range(keyword_total)]
    color_data = [[] for x in range(keyword_total)]
    y_range = 1
    vis_dict["vis_data"] = vis_data
    vis_dict["y_range"] = y_range
    vis_dict["color_data"] = color_data
    vis_dict["keywords"] = ii2tt(ii)
    if not q:
        return sr, vis_dict
    dbc = settings.DBC
    n = 0
    distribution = [[[], []] for x in range(keyword_total)]
    for cid in cids:
        _sr = list(dbc.sentences[str(cid)].find(q, {'_id': 0, 't.p': 0}, limit=settings.MAX_RESULT_LENGTH))
        for r in _sr:
            r['m'], r['c'] = find_best_match(r, ii, dd, ref)
            sentence_length = float(len(r['t']))
            position_tuple = r['m']
            position_delta = 1.0 / sentence_length
            # print "r['m'] = ", r['m']
            for x in range(keyword_total):
                distribution[x][0].append(position_tuple[x] / sentence_length)
                distribution[x][1].append(position_tuple[x] / sentence_length + position_delta)
        # _sr = [r for r in _sr if r['c'] < sys.maxint] #filter out critical unmatch results
        _sr.sort(key=itemgetter('c'))
        _sr = _sr[:count]
        sr += _sr
        n += sum(1 for r in _sr if r['c'] <= 2*len(ii))
        if n >= count:
            break
    sr.sort(key=itemgetter('c'))
    sr = [(paper_source_str(r['p']), cleaned_sentence(ii2tt([t['w'] for t in r['t']]), r['m'])) for r in sr[:count]]
    vis_data = distribution_statistic(distribution, precision)
    for data in vis_data:
        new_max = max(data)
        y_range = new_max if new_max > y_range else y_range
    y_range *= 1.1
    for array_index in range(len(vis_data)):
        for inside_index in range(len(vis_data[array_index])):
            color_data[array_index].append(color_bank[int(vis_data[array_index][inside_index] / float(y_range) / color_step)])
    vis_dict["vis_data"] = vis_data
    vis_dict["y_range"] = y_range
    vis_dict["color_data"] = color_data
    return sr, vis_dict


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

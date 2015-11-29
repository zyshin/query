# -*- coding: utf-8 -*-

import requests


def is_cn_char(c):
        return 0x4e00 <= ord(c) < 0x9fa6


def is_cn(s):
    return reduce(lambda x,y: x and y, [is_cn_char(c) for c in s], True)

# TODO: Bugs here, youdao returns not perfect English, for example: 搜索
def translate(cn):
    url = u'http://fanyi.youdao.com/openapi.do?keyfrom=ESLWriter&key=205873295&type=data&doctype=json&version=1.2&only=dict&q=' + cn
    l = ['no translation found!']
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            o = r.json()
            if o['errorCode'] == 0 and 'basic' in o and 'explains' in o['basic']:
                l = [s[s.find(']')+1:].strip() for s in o['basic']['explains']]
    except Exception as e:
        print e
    # l = [s for s in r if ' ' not in s]  #filter out phrases
    l.sort(key=lambda s: s.count(' '))
    return tuple(l)

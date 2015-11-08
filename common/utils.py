import os, hashlib
from time import clock

from django.conf import settings
from django.http import HttpResponse, Http404
from bson.objectid import ObjectId


def timeit(func):
    def __decorator(*args, **kwags):
        start = clock()
        result = func(*args, **kwags)  #recevie the native function call result
        finish = clock()
        span = int((finish - start) * 1000)
        if settings.DEBUG or span > 5000:
            print 'timeit: ', func.__name__, span, 'ms'
        return result        #return to caller
    return __decorator


def make_response(status=200, content_type='text/plain', content=None):
    """ Construct a response to an upload request.
    Success is indicated by a status of 200 and { "success": true }
    contained in the content.

    Also, content-type is text/plain by default since IE9 and below chokes
    on application/json. For CORS environments and IE9 and below, the
    content-type needs to be text/html.
    """
    response = HttpResponse()
    response.status_code = status
    response['Content-Type'] = content_type
    response.content = content
    return response


def mongo_get_object(type_object, projection=None, **kwargs):
    if 'pk' in kwargs:
        kwargs[type_object.Meta.pk] = kwargs['pk']
        del kwargs['pk']
    database_name, collection_name = type_object.Meta.db
    o = settings.DBC[database_name][collection_name].find_one(kwargs, projection)
    if o: o['pk'] = o[type_object.Meta.pk]
    return o


def mongo_get_object_or_404(type_object, projection=None, **kwargs):
    o = mongo_get_object(type_object, projection, **kwargs)
    if not o:
        database_name, collection_name = type_object.Meta.db
        raise Http404('No match found in %s.%s.' % (database_name, collection_name))
    return o


def mongo_get_objects(type_object, projection=None, **kwargs):
    if 'pk' in kwargs:
        kwargs[type_object.Meta.pk] = kwargs['pk']
        del kwargs['pk']
    database_name, collection_name = type_object.Meta.db
    return settings.DBC[database_name][collection_name].find(kwargs, projection)


def mongo_save(type_object, **kwargs):
    if 'pk' in kwargs and type_object.Meta.pk != 'pk':
        kwargs[type_object.Meta.pk] = kwargs['pk']
        del kwargs['pk']
    # else:
    #     i = ObjectId()
    #     kwargs['_id'] = kwargs[type_object.Meta.pk] = i
    database_name, collection_name = type_object.Meta.db
    return settings.DBC[database_name][collection_name].save(kwargs)    # or i


# paper path manager

def paper_path(i, check=False):
    path = os.path.join(settings.PAPERS_DIR, '%s.pdf' % str(i))
    if check and not os.path.isfile(path):
        return None
    return path


def extracted_path(i, check=False):
    path = os.path.join(settings.EXTRACTED_DIR, '%s.txt' % str(i))
    if check and not os.path.isfile(path):
        return None
    return path


def refined_path(i, check=False):
    path = os.path.join(settings.REFINED_DIR, '%s.txt' % str(i))
    if check and not os.path.isfile(path):
        return None
    return path


def parsed_path(i, check=False):
    path = os.path.join(settings.PARSED_DIR, '%s.conll' % str(i))
    if check and not os.path.isfile(path):
        return None
    return path


def corpus_path(i, create=True):
    path = os.path.join(settings.CORPORA_DIR, str(i))
    if create and not os.path.isdir(path):
       os.mkdir(path)
    return path


# for manually build corpora
dbc = None
def init_dbc(remote=False):
    from pymongo import MongoClient
    from getpass import getpass
    global dbc
    if remote:
        dbc = MongoClient('www.thuesl.org')
    else:
        dbc = MongoClient('166.111.139.170')
    print 'using', dbc
    try:
        dbc.database_names()
    except:
        user = raw_input('User: ')
        pwd = getpass()
        dbc.admin.authenticate(user, pwd)
    return True


def corpus_from_dblp(v):
    if not dbc:
        print 'call init_dbc(remote=True) first.'
        return
    i = v['dblp']
    fid = dbc.esl.fields.find_one({'name': v['field']})['_id']
    return {'_id': i, 'user': 1, 'name': v.get('shortName', v['fullName']), 'description': v['fullName'], 'db': i, 'field': fid, 'status': 0}


def corpora_from_dblp():
    if not dbc:
        print 'call init_dbc(remote=True) first.'
        return
    # bulk = dbc.common.corpora.initialize_unordered_bulk_op()
    venues = dbc.esl.venues.find({'c': {'$exists': True}, '$or': [{'ccf': 'B'}, {'ccf': 'A'}]})
    r = dbc.common.corpora.insert_many([corpus_from_dblp(v) for v in venues], ordered=False)
    return len(r.inserted_ids)
    # print bulk.execute()


def update_files(ids):
    if not dbc:
        print 'call init_dbc(remote=True) first.'
        return
    from datetime import datetime
    files = []
    uploads = []
    for i in ids:
        if dbc.common.files.count({'_id': i}) > 0:
            continue
        path = paper_path(i)
        size1 = os.path.getsize(path)
        with open(path, 'rb') as fin:
            data = fin.read()
            size = len(data)
            assert size1 == size, 'size not consistent'
            info = {'_id': i, 'status': 1, 'md5': hashlib.md5(data).hexdigest(), 'size': size}
            files.append(info)
            p = dbc.esl.papers.find_one({'@id': i})
            c = dbc.esl.venues.find_one({'_id': p['venue']})
            upload = {'_id': i, 'file': i, 'corpus': c['dblp'], 'title': p['info']['title']['text']}
            uploads.append(upload)
        if len(files) % 5000 == 0:
            print datetime.now(), len(files), 'files done'
    if files:
        dbc.common.files.insert_many(files, ordered=False)
    if uploads:
        dbc.common.uploads.insert_many(uploads, ordered=False)
        dbc.common.uploads.create_index('corpus')
    return len(files), len(uploads)


def update_files_from_file(path):
    with open(path, 'r') as fin:
        ids = fin.read().split()
    return update_files(ids)

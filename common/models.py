from django.db import models
from django.contrib.auth.models import User

from datetime import datetime


class Corpus:
    class Meta:
        pk = '_id'
        db = ('common', 'corpora')
    # TODO


class UploadRecord:
    class Meta:
        pk = '_id'
        db = ('common', 'uploads')
    # TODO


class UploadFile:
    class Meta:
        pk = '_id'
        db = ('common', 'files')
    # TODO


class UserProfile:
    class Meta:
        pk = '_id'
        db = ('common', 'users')
    # TODO


class DblpPaper:
    class Meta:
        pk = '@id'
        db = ('esl', 'papers')
    # TODO

class DblpVenue:
    class Meta:
        pk = '_id'
        db = ('esl', 'venues')
    # TODO

class Field:
    class Meta:
        pk = '_id'
        db = ('esl', 'fields')
    # TODO


class UserCorpus(models.Model):
    user = models.ForeignKey(User)
    # db = models.IntegerField(default=0)
    status = models.IntegerField(default=0)
    date_created = models.DateTimeField(default=datetime.now)
    name = models.CharField(max_length=64)  #unique=True
    description = models.CharField(max_length=256, blank=True)
    # ispublic = models.BooleanField(default=True)

    def __unicode__(self):
        return u'<UserCorpus: pk=%d, user=%d, name=%s, status=%d>' % (self.pk, self.user.pk, self.name, self.status)


'''
class Paper(models.Model):  #pk of PaperFileInfo is pid
    # qquuid = models.CharField(max_length=36)
    # author = models.CharField(max_length=200, blank=True)
    # source = models.CharField(max_length=50, blank=True)
    # url = models.CharField(max_length=200, blank=True)
    md5 = models.CharField(max_length=32)
    size = models.PositiveIntegerField(default=0)
    num_words = models.PositiveIntegerField(default=0)
    status = models.IntegerField(default=0)
    bibtex = models.TextField(blank=True)


class UploadRecord(models.Model):
    corpus = models.ForeignKey(Corpus)
    fileinfo = models.ForeignKey(Paper)
    date_added = models.DateTimeField(default=datetime.now)
    title = models.CharField(max_length=64)
'''

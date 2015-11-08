from django.conf.urls import patterns, url

urlpatterns = patterns('eslwriter.views',
	url(r'^$', 'home_view', name='eslwriter'),
    url(r'^dep/$', 'dep_query_view', name='dep'),
    url(r'^sentence/$', 'sentence_query_view', name='sentence'),
)

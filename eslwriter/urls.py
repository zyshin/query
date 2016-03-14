from django.conf.urls import patterns, url
import views

urlpatterns = [
    url(r'^$', views.home_view, name='eslwriter'),
    url(r'^dep/$', views.dep_query_view, name='dep'),
    url(r'^sentence/$', views.sentence_query_view, name='sentence'),
]

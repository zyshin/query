from django.conf.urls import patterns, url, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
	# Uncomment the admin/doc line below to enable admin documentation:
	# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	url(r'^admin/', include(admin.site.urls)),

	# url(r'^', include('common.urls')),

	url(r'^', include('eslwriter.urls')),

	url(r'^accounts/', include('registration.backends.default.urls')),

	# url(r'^', include('fine_uploader.urls')),

	# url(r'^corpus/', include('corpus_building.urls')),

	# url(r'^monitor/', include('monitor.urls')),
)

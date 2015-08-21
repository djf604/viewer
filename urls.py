from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

import views

urlpatterns = patterns('',
                       # Access pages
                       url(r'^$', views.index, name='index'),
                       url(r'^register/$', views.register, name='register'),
                       url(r'^login/$', views.user_login, name='login'),
                       url(r'^logout/$', views.user_logout, name='logout'),
                       url(r'^restricted/$', views.restricted,
                           name='restricted'),
                       url(r'^permission/$', views.permission,
                           name='permission'),

                       # Project
                       url(r'^project/$', views.manage_project,
                           name='manage_project'),
                       url(r'^project/new_project/$',
                           views.new_project, name='new_project'),
                       url(r'^project/edit_project/(?P<project_id>\d+)/$',
                           views.edit_project, name='edit_project'),


                       # Bnid
                       url(r'^bnid/$',
                           views.manage_bnid, name='manage_bnid'),
                       url(r'^bnid/new_bnid/$',
                           views.new_bnid, name='new_bnid'),
                       url(r'^bnid/edit_bnid/(?P<bnid_id>\d+)/$',
                           views.edit_bnid, name='edit_bnid'),
                       url(r'^bnid/delete_bnid/(?P<bnid_id>\d+)/$',
                           views.delete_bnid, name='delete_bnid'),
                       url(r'^get_bnids_by_study/(?P<study_id>\d+)/$',
                           views.get_bnids_by_study, name='get_bnids_by_study'),


                       # Sample
                       url(r'^sample/$', views.manage_sample,
                           name='manage_sample'),
                       url(r'^sample/new_sample/$', views.new_sample,
                           name='new_sample'),
                       url(r'edit_sample/(?P<sample_id>\d+)/$', views.edit_sample,
                           name='edit_sample'),
                       url(r'delete_sample/(?P<sample_id>\d+)/$', views.delete_sample,
                           name='delete_sample'),
                       url(r'^get_samples/(?P<study_id>\d+)/$', views.get_samples,
                           name='get_samples'),

                       # Study
                       url(r'^study/$', views.manage_study, name='manage_study'),
                       url(r'^study/new_study/$', views.new_study, name='new_study'),
                       url(r'^study/edit_study/(?P<study_id>\d+)/$',
                           views.edit_study, name='edit_study'),
                       url(r'^study/delete_study/(?P<study_id>\d+)/$',
                           views.delete_study, name='delete_study'),

                       # Report
                       url(r'^report/$', views.manage_report,
                           name='manage_report'),
                       url(r'^report/edit_report/(?P<report_id>\d+)/$',
                           views.edit_report, name='edit_report'),
                       url(r'report/view_report/(?P<file_id>\d+)/$',
                           views.view_report, name='view_report'),
                       url(r'^report/upload_report/$', views.upload_report,
                           name='upload_report'),
                       url(r'^report/delete_report/(?P<report_id>\d+)/$', views.delete_report,
                           name='delete_report'),
                       url(r'^load_variants/(?P<report_id>\d+)/$', views.load_variants,
                           name='load_variants'),

                       url(r'^files/(?P<path>.*)$',
                           'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT}),

                       # Search
                       url(r'^search/$', views.search_reports, name='search_reports'),
                       url(r'^ajax_search_reports/(?P<search_col>\S+)/(?P<search_term>\S+)/(?P<search_type>\S+)/$',
                           views.ajax_search_reports, name='ajax_search_reports'),

                       ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



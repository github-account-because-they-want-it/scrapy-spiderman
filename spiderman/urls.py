from django.conf.urls import include, url
from . import views


spider_patterns = [
    url(r"^start/$", views.StartSpiderView.as_view(), name="spiderman_start_spider"),
]

spiderrun_patterns = [
    url(r"^stop/$", views.RunStopView.as_view(), name="spiderman_stop_run"),
    url(r"^(?P<run_id>\d+)/log/$", views.RunLogView.as_view(), name="spiderman_run_log"),
    url(r"^(?P<run_id>\d+)/items/$", views.RunItemsView.as_view(), name="spiderman_run_items"),
    url(r"stats/", views.RunStatsView.as_view(), name="spiderman_run_stats")
]

urlpatterns = [
    url(r"^$", views.HomeView.as_view(), name="spiderman_home"),
    url(r"^spider/", include(spider_patterns)),
    url(r"^run/", include(spiderrun_patterns))
]

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/chart-data/', views.get_chart_data, name='chart-data'),
]
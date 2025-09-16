from django.urls import path
from .views import PhotographerListView, PhotographerDetailView, PhotographerUpdateView, PhotographersTestView


urlpatterns = [
    path('', PhotographerListView.as_view(), name='photographer-list'),
    path('<uuid:id>/', PhotographerDetailView.as_view(), name='photographer-detail'),
    path('me/', PhotographerUpdateView.as_view(), name='photographer-me'),
    path('test/', PhotographersTestView.as_view(), name='photographers-test'),
]

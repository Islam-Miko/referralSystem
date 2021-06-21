from django.urls import path
from . import views

urlpatterns = [
    path('invite/send/<str:sender>/<str:receiver>', views.send_invite),
    path('invite/accept/<str:receiver>', views.invitations),
]
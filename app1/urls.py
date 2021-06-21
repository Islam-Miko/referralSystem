from django.urls import path
from . import views

urlpatterns = [
    path('invite/send/<str:sender>/<str:receiver>', views.send_invite),
    # endpoint for sending invitations
    path('invite/view/<str:receiver>', views.invitations),
    # endpoint for abo to see all invitations that were sent to him
    path('invite/sent/<str:sender>', views.sent_invitations),
    # endpoint for sender to see his all invitations
]
from django.urls import path
from . import views

urlpatterns = [
    path('invite/send/<str:sender>/<str:receiver>', views.send_invite),
    # endpoint to send an invitation
    path('invite/view/<str:receiver>', views.invitations),
    # endpoint to see all invitation sent to number
    path('invite/sent/<str:sender>', views.sent_invitations),
    # endpoint to see sent invitations by number
    path('registration/<str:number>', views.registration_function),
    # endpoint to registration
]
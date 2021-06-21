from django.contrib import admin

from .models import Subscribers, Invite
# Register your models here.
admin.site.register(Subscribers)
admin.site.register(Invite)
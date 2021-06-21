from .models  import Invite
from rest_framework import serializers


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = '__all__'
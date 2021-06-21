from .models  import Invite, Subscribers
from rest_framework import serializers


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = '__all__'


class SubsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribers
        fields = '__all__'
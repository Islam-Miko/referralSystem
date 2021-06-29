from .models import Invite, Subscribers
from rest_framework import serializers

from app1.validatoin_func import(isdecim,
                             conditions_for_sender,
                             check_for_notification_property,
                            check_for_registered_receiver)


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = '__all__'


class SubsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribers
        fields = '__all__'



class NumberSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=10,
                                   min_length=10,
                                   validators=[isdecim,
                                               conditions_for_sender])
    receiver = serializers.CharField(min_length=10,
                                     max_length=10,
                                     validators=[isdecim,
                                                 check_for_notification_property,
                                                 check_for_registered_receiver])




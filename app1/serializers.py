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


def isdecim(value):
    if not value.isdecimal():
        raise serializers.ValidationError(['Incorrect type of number!'])


class NumberSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=12,
                                   min_length=12,
                                   validators=[isdecim])
    receiver = serializers.CharField(min_length=12,
                                     max_length=12,
                                     validators=[isdecim])

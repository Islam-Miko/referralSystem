from .models  import Invite, Subscribers
from rest_framework import serializers
from django.db.models import Count, Q
import datetime


def conditions_for_sender(sender):
    """checks all conditions for sender
    limit of 5 invitations to one day
    limit of 30 invitations to one month"""
    senders_invitations_for_day = Invite.objects.filter(
                            Q(sender_id__phone=sender) &
                            Q(start_date__day=datetime.datetime.today().day) &
                            Q(start_date__month=datetime.datetime.today().month
                            )).aggregate(qnt=Count('sender_id'))
    senders_invitations_for_month = Invite.objects.filter(
        Q(sender_id__phone=sender) & Q(start_date__month=datetime.datetime.today().month
                                )).aggregate(qnt=Count('sender_id'))
    if senders_invitations_for_day['qnt'] >= 5:
        raise serializers.ValidationError(['You cannot send more than 5 in one day'])
    if senders_invitations_for_month['qnt'] >= 30:
        raise serializers.ValidationError(['You cannot send more than 30 in one month'])


def isdecim(value):
    if not value.isdecimal():
        raise serializers.ValidationError(['Incorrect type of number!'])


def check_for_notification_property(receiver_phone):
    """checks active field of receiver"""
    receiver_instance = Subscribers.objects.filter(phone=receiver_phone).get()
    if not receiver_instance.active:
        raise serializers.ValidationError(['Abo set notification off!'])

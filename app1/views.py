import datetime


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Subscribers, Invite
from django.db.models import Count, Q


from .errors import AmountError, NotificationOff, MonthAmountError, OnlyOnceError
# Create your views here.

#
# def create_subs(number):
#     """creates new instance of Subscribers"""
#     new_instance = Subscribers(phone=number)
#     new_instance.save()
#

def check_in_db(phone):
    """Searches in DB by phone. if finds obj returns True
    if no obj by phone was found calls create function"""
    query_of_phone = Subscribers.objects.filter(phone=phone).get_or_create(phone=phone)
    print(query_of_phone)

    return query_of_phone[0]
    # get_or_create() returns tuple
    # first element is obj, second is boolean- if instance was created or not
    # thats wy we take first element


def create_new_invite(sender, receiver):
    """creates new inst in Invite"""
    new_invite_instance = Invite(sender_id=sender, receiver_id=receiver)
    new_invite_instance.save()


def conditions_for_sender(sender):
    """checks all conditions for sender
    limit of 5 invitations to one day
    limit of 30 invitations to one month"""
    senders_invitations_for_day = Invite.objects.filter(
        Q(sender_id=sender) & Q(start_date__day=datetime.datetime.today().day
                                )).aggregate(qnt=Count('sender_id'))
    senders_invitations_for_month = Invite.objects.filter(
        Q(sender_id=sender) & Q(start_date__month=datetime.datetime.today().month
                                )).aggregate(qnt=Count('sender_id'))
    if senders_invitations_for_day['qnt'] >= 5:
        raise AmountError
    if senders_invitations_for_month['qnt'] >= 30:
        raise MonthAmountError


def check_for_notification_property(phone):
    """checks active field of receiver"""
    receiver_instance = phone
    if not receiver_instance.active:
        raise NotificationOff


def rewrite_invitations_to_receiver(receiver):
    """gets last invitations to given receiver
    and changes end date, status"""
    last_invitations = Invite.objects.filter(receiver_id=receiver).last()
    if last_invitations is None:
        1  # if receiver was never invited before we do nothing
    else:
        last_invitations.status = 'NOTACTIVE'
        last_invitations.end_date= datetime.datetime.now()


def check_send_only_once(sender, receiver):
    senders_invitations_for_day = Invite.objects.filter(
        Q(sender_id=sender) & Q(receiver_id=receiver) & Q(start_date__day=datetime.datetime.today().day
                                ))
    if senders_invitations_for_day is not None:
        raise OnlyOnceError


@api_view(['GET'])
def send_invite(request, sender, receiver):
    """Checks if sender in DB. If not creates in DB"""
    sender_instance = check_in_db(sender)  # creates new obj in Subs and returns it
    receiver_instance = check_in_db(receiver)  # creates new obj in Subs and returns it
    try:
        check_send_only_once(sender_instance, receiver_instance)
        rewrite_invitations_to_receiver(receiver_instance)
        create_new_invite(sender_instance, receiver_instance)
        conditions_for_sender(sender_instance)
        check_for_notification_property(receiver_instance)
    except AmountError:
        return Response('You sent more than 5 invitations today', status=status.HTTP_405_METHOD_NOT_ALLOWED)
    except NotificationOff:
        return Response('Abonent set notification off', status=status.HTTP_403_FORBIDDEN)
    except MonthAmountError:
        return Response('You sent more than 30 invitations this month', status=status.HTTP_405_METHOD_NOT_ALLOWED)
    except OnlyOnceError:
        return Response('You have already sent an invitations to this person today',
                        status=status.HTTP_403_FORBIDDEN)


    return Response(f'Invite was sent to {receiver}', status=status.HTTP_202_ACCEPTED)

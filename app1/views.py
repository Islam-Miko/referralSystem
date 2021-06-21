import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Subscribers, Invite
from django.db.models import Count, Q


from .errors import AmountError, NotificationOff, MonthAmountError, OnlyOnceError, AcceptedError
from .serializers import InviteSerializer, SubsSerializer
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
        Q(sender_id=sender) & Q(start_date__date=datetime.datetime.today().date
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
        ... # if receiver was never invited before we do nothing
    else:
        last_invitations.status = 'NOTACTIVE'
        last_invitations.end_date= datetime.datetime.now()
        last_invitations.save()


def check_send_only_once(sender, receiver):
    senders_invitations_for_day = Invite.objects.filter(
        Q(sender_id=sender) & Q(receiver_id=receiver) & Q(start_date__day=datetime.datetime.today().day
                                ))
    print(senders_invitations_for_day)
    if senders_invitations_for_day:
        raise OnlyOnceError

def check_for_registered_receiver(receiver):
    q = Invite.objects.filter(receiver_id=receiver).last()
    if q.status == "ACCEPTED":
        raise AcceptedError
@api_view(['GET'])
def send_invite(request, sender, receiver):
    """Checks if sender in DB. If not creates in DB"""
    sender_instance = check_in_db(sender)  # creates new obj in Subs and returns it
    receiver_instance = check_in_db(receiver)  # creates new obj in Subs and returns it
    try:
        check_for_registered_receiver(receiver_instance)
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
    except AcceptedError:
        return Response('Abonement already registered!')


    return Response(f'Invite was sent to {receiver}', status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
def invitations(request, receiver):
    try:
        receiver = Subscribers.objects.get(phone=receiver)
    except ObjectDoesNotExist:
        return Response('This number is not in our system', status=status.HTTP_404_NOT_FOUND)
    all_invitations = Invite.objects.filter(receiver_id=receiver)
    serializer = InviteSerializer(all_invitations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def sent_invitations(request, sender):
    try:
        sender = Subscribers.objects.get(phone=sender)
    except ObjectDoesNotExist:
        return Response('This number is not in our system', status=status.HTTP_404_NOT_FOUND)
    all_sent_invitatins = Invite.objects.filter(sender_id=sender)
    serializer = InviteSerializer(all_sent_invitatins, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def check_invites(object):
    invites = Invite.objects.filter(Q(receiver_id=object) &
                                    Q(end_date__range=[datetime.datetime.today(),
                                                       datetime.datetime(year=2999,
                                                                         month=12,
                                                                         day=31)],))
    if invites:
        return invites.last()
    return False


def change_last_invite(last_invite):
    last_invite.status = "ACCEPTED"
    last_invite.end_date = datetime.datetime.now()
    last_invite.save()
    return last_invite

def create_new_sub(newbie):
    new = Subscribers(phone=newbie)
    new.save()
    return new


@api_view(['GET'])
def someFunction(request, number):
    try:
        abo = Subscribers.objects.get(phone=number)
    except ObjectDoesNotExist:
        created_subscriber = create_new_sub(number)
        seri = SubsSerializer(created_subscriber)
        return Response(seri.data)

    has_invite = check_invites(abo)
    if has_invite:
        changed_last_invite = change_last_invite(has_invite)
        serializer = InviteSerializer(changed_last_invite)
        return Response(serializer.data)
    else:
        return Response("Congrats! You have registered You had no invitations")



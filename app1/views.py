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


def check_in_db(phone):
    """Searches in DB by phone. if finds obj returns True
    if no obj by phone was found calls create function"""
    query_of_phone = Subscribers.objects.filter(phone=phone).get_or_create(phone=phone)
    print(query_of_phone)

    return query_of_phone[0]
    # get_or_create() returns tuple
    # first element is obj, second is boolean- if instance was created or not
    # that is wy we take first element


def create_new_invite(sender, receiver):
    """creates new inst in Invite"""
    new_invite_instance = Invite(sender_id=sender, receiver_id=receiver)
    new_invite_instance.save()


def conditions_for_sender(sender):
    """checks all conditions for sender
    limit of 5 invitations to one day
    limit of 30 invitations to one month"""
    senders_invitations_for_day = Invite.objects.filter(
                            Q(sender_id=sender) &
                            Q(start_date__day=datetime.datetime.today().day) &
                            Q(start_date__month=datetime.datetime.today().month
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
        ...  # if receiver was never invited before we do nothing
    else:
        last_invitations.status = 'NOTACTIVE'
        last_invitations.end_date = datetime.datetime.now()
        last_invitations.save()


def check_send_only_once(sender, receiver):
    senders_invitations_for_day = Invite.objects.filter(
        Q(sender_id=sender) & Q(receiver_id=receiver) & Q(start_date__day=datetime.datetime.today().day))
    if senders_invitations_for_day:
        raise OnlyOnceError


def check_for_registered_receiver(receiver):
    q = Invite.objects.filter(receiver_id=receiver).last()
    if q is None:
        pass
    elif q.status == 'ACCEPTED':
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
    """Shows all invitations to this number"""
    try:
        receiver = Subscribers.objects.get(phone=receiver)
    except ObjectDoesNotExist:
        return Response('This number is not in our system', status=status.HTTP_404_NOT_FOUND)
    all_invitations = Invite.objects.filter(receiver_id=receiver)
    serializer = InviteSerializer(all_invitations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def sent_invitations(request, sender):
    """Shows all sent invitations by given number"""
    try:
        sender = Subscribers.objects.get(phone=sender)
    except ObjectDoesNotExist:
        return Response('This number is not in our system', status=status.HTTP_404_NOT_FOUND)
    all_sent_invitatins = Invite.objects.filter(sender_id=sender)
    serializer = InviteSerializer(all_sent_invitatins, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_last_invitation(obj):
    """returns last object of InviteModel"""
    invitation = Invite.objects.filter(Q(receiver_id=obj) &
                                       Q(end_date__range=[datetime.datetime.today(),
                                                        datetime.datetime(year=2999,
                                                                         month=12,
                                                                         day=31)],))

    return invitation.last()


def change_last_invite(phone):
    abo_subs = Subscribers.objects.filter(phone=phone).get()
    last_invitation = get_last_invitation(abo_subs)
    last_invitation.status = "ACCEPTED"
    last_invitation.end_date = datetime.datetime.now()
    last_invitation.save()


def check_in_db_and_invitation(abo):
    """checks if given number is in db
    or has invit."""
    subs = Subscribers.objects.filter(phone=abo).last()
    if subs:
        subs_invitation = Invite.objects.filter(receiver_id=subs).all()
        if subs_invitation:
            return True, True
        return True, False
    return False, False


def create_subs(number):
    """creates new instance of Subscribers"""
    new_instance = Subscribers(phone=number)
    new_instance.save()


def create_fake_invitation(number):
    """function to prevent sending invitations to registered abos"""
    subs = Subscribers.objects.filter(phone=number).last()
    fake_invitation = Invite(sender_id=subs,
                             receiver_id=subs,
                             status="ACCEPTED",
                             end_date=datetime.datetime.now())
    fake_invitation.save()


@api_view(['GET'])
def registration_function(request, number):
    newAbo_in_db, newAbo_has_invitation = check_in_db_and_invitation(number)

    if not newAbo_in_db:
        create_subs(number)
        create_fake_invitation(number)
        return Response('You have registered. You had no invitations!')
    if not newAbo_has_invitation:
        create_fake_invitation(number)
        return Response('You have successfully registered. You had no invitations!')
    if newAbo_has_invitation:
        change_last_invite(number)
        return Response('Congrats. You have successfully registerd!'
                        'had invitations')

import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Subscribers
from .serializers import InviteSerializer, SubsSerializer
from app1.auxilary_functions import *
# Create your views here.


@api_view(['POST'])
def send_invite(request):
    """Main function"""
    if request.method == 'POST':
        sender = request.data.pop('sender')
        receiver = request.data.pop('receiver')
    if sender == receiver:
        return Response('This is not possible!', status=status.HTTP_403_FORBIDDEN)
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


@api_view(['POST'])
def change_subs(request):
    """Allows to change active attr in Subscribes objects"""
    if request.method == 'POST':
        subs = request.data
        subs_instance = Subscribers.objects.filter(phone=subs.get('phone')).last()
        if subs_instance:
            serializer = SubsSerializer(subs_instance, data=subs)
        else:
            serializer = SubsSerializer(data=subs)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)


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


@api_view(['GET'])
def registration_function(request, number):
    """registration"""
    newAbo_in_db, newAbo_has_invitation = check_in_db_and_invitation(number)
    try:
        if not newAbo_in_db:
            create_subs(number)
            create_fake_invitation(number)
            return Response('You have registered. You had no invitations!')
        if not newAbo_has_invitation:
            create_fake_invitation(number)
            return Response('You have successfully registered. You had no invitations!')
        if newAbo_has_invitation:
            check_registered_already(number)
            change_last_invite(number)
            return Response('Congrats. You have successfully registered!'
                            'had invitations')
    except AlreadyRegisteredError:
        return Response('This number is already registered!', status=status.HTTP_403_FORBIDDEN)

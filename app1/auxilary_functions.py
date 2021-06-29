import datetime

from .models import Subscribers, Invite
from django.db.models import Count, Q

from .errors import (OnlyOnceError, AcceptedError,
                     AlreadyRegisteredError,
                     SelfSendingError)


def check_in_db(phone):
    """Searches in DB by phone. if finds obj returns it
    if no obj by phone was found calls create function"""
    query_of_phone = Subscribers.objects.filter(phone=phone).get_or_create(phone=phone)
    return query_of_phone[0]
    # get_or_create() returns tuple
    # first element is obj, second is boolean- if instance was created or not
    # that is wy we take first element


def check_self_sending(sender, receiver):
    """Checks if numbers are identical"""
    if sender == receiver:
        raise SelfSendingError


def create_new_invite(sender, receiver):
    """creates new inst in Invite"""
    new_invite_instance = Invite(sender_id=sender, receiver_id=receiver)
    new_invite_instance.save()


def rewrite_invitations_to_receiver(receiver):
    """gets last invitations to given receiver
    and changes end date, status"""
    last_invitations = Invite.objects.filter(receiver_id=receiver).last()
    if last_invitations:
        last_invitations.status = 'NOTACTIVE'
        last_invitations.end_date = datetime.datetime.now()
        last_invitations.save()


def check_send_only_once(sender, receiver):
    senders_invitations_for_day = Invite.objects.filter(
        Q(sender_id=sender) & Q(receiver_id=receiver) & Q(start_date__day=datetime.datetime.today().day))
    if senders_invitations_for_day:
        raise OnlyOnceError


def check_for_registered_receiver(receiver):
    """checks if there are invitation to number that were ACCEPTED"""
    q = Invite.objects.filter(receiver_id=receiver).last()
    if q is not None:
        if q.status == 'ACCEPTED':
            raise AcceptedError


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
    and has an invit."""
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


def check_registered_already(number):
    """checks if number already registered"""
    subs = Subscribers.objects.filter(phone=number).last()
    invitation = Invite.objects.filter(receiver_id=subs).last()
    if invitation:
        if invitation.status == "ACCEPTED":
            raise AlreadyRegisteredError

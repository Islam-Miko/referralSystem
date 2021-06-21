from datetime import date, datetime

from django.db import models


# Create your models here.
class Subscribers(models.Model):
    phone = models.CharField('Phone number', max_length=15)
    active = models.BooleanField(verbose_name='Notification', default=True)
    add_date = models.DateField(verbose_name='added date', default=date.today())
    edit_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone


class Invite(models.Model):
    sender_id = models.ForeignKey(Subscribers, on_delete=models.CASCADE,
                                  related_name='sender',verbose_name='Sender')
    receiver_id = models.ForeignKey(Subscribers, on_delete=models.CASCADE,
                                    related_name='receiver', verbose_name='Receiver')
    status = models.CharField('status', max_length=50, default='ACTIVE')
    start_date = models.DateTimeField(verbose_name='sD', auto_now_add=True)
    end_date = models.DateTimeField(verbose_name='eD', default=datetime(
                                                                        year=2999,
                                                                        month=12,
                                                                        day=31
    ))

    def __str__(self):
        return f'From {self.sender_id} to {self.receiver_id}'
from apps.core.sms import sms_center
from apps.project.choices import ProjectStatusChoices
from apps.project.models import Project
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Project)
def send_sms(sender, instance, created, **kwargs):
    if created:
        project_status = instance.status
        match project_status:
            case ProjectStatusChoices.CANCELED:
                sms_center.send_canceled_project_sms(instance)
            case ProjectStatusChoices.TURNED:
                sms_center.send_turned_project_sms(instance)
            case ProjectStatusChoices.SUBMITTED:
                sms_center.send_accepted_project_sms(instance)

from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.models import Book


@receiver(post_delete, sender=Book)
def delete_book_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)

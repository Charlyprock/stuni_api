import os
from django.db.models.signals import pre_delete
from django.dispatch import receiver


def delete_file_model(model_name, field_name="image"):

    @receiver(pre_delete, sender=model_name)
    def delete_file(sender, instance, **kwargs):
        attr = getattr(instance, field_name, None)
        if attr:
            try:
                if os.path.isfile(attr.path):
                    os.remove(attr.path)
            except Exception as e:
                print(f"Error Deleted {field_name}: {e}")
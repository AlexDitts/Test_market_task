from django.db import models
from mptt.models import MPTTModel
from solo.models import SingletonModel


class AbstractBaseModel(models.Model):
    """
    Base class from which all models should be inherited,
    in order to have an option to add behavior to the group of models
    """

    class Meta:
        abstract = True

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )


class AbstractBaseSoloModel(SingletonModel):
    """
    Base class from which all models should be inherited,
    in order to have an option to add behavior to the group of models
    """

    class Meta:
        abstract = True

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )


class AbstractionMPTTModel(MPTTModel):

    class Meta:
        abstract = True

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

from django.db import models


class CoreModel(models.Model):
    pub_date = models.DateTimeField(
        "Дата публикации", auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ("-pub_date",)

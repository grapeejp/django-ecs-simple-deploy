from django.db import models

class TimeStampedModel(models.Model):
    """
    タイムスタンプを持つ抽象基底モデル
    """
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        abstract = True 
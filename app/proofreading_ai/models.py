from django.db import models
from django.utils import timezone


class ProofreadingRequest(models.Model):
    """校正リクエストモデル"""
    original_text = models.TextField('原文')
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    
    class Meta:
        verbose_name = '校正リクエスト'
        verbose_name_plural = '校正リクエスト'
        
    def __str__(self):
        return f"校正リクエスト {self.id}: {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ProofreadingResult(models.Model):
    """校正結果モデル"""
    request = models.ForeignKey(ProofreadingRequest, on_delete=models.CASCADE, related_name='results')
    corrected_text = models.TextField('校正後テキスト')
    completion_time = models.FloatField('処理時間(秒)', null=True, blank=True)
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    
    class Meta:
        verbose_name = '校正結果'
        verbose_name_plural = '校正結果'
        
    def __str__(self):
        return f"校正結果 {self.id}: {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ReplacementDictionary(models.Model):
    """置換辞書モデル"""
    original_word = models.CharField('元の語句', max_length=255)
    replacement_word = models.CharField('置換後の語句', max_length=255)
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    
    class Meta:
        verbose_name = '置換辞書'
        verbose_name_plural = '置換辞書'
        
    def __str__(self):
        return f"{self.original_word} → {self.replacement_word}" 
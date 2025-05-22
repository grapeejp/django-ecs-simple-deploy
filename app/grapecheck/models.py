from django.db import models

# Create your models here.

class Category(models.Model):
    """グレイプのコンテンツカテゴリを表すモデル"""
    name = models.CharField('カテゴリ名', max_length=100)
    slug = models.SlugField('スラッグ', unique=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, 
                              null=True, blank=True, 
                              related_name='children',
                              verbose_name='親カテゴリ')
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'
        ordering = ['name']

    def __str__(self):
        return self.name


class GrapeCheck(models.Model):
    """グレイプらしさ評価結果を保存するモデル"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, 
                                verbose_name='カテゴリ')
    content_text = models.TextField('評価テキスト')
    total_score = models.IntegerField('総合スコア')
    writing_style_score = models.IntegerField('文体スコア')
    structure_score = models.IntegerField('構成スコア')
    keyword_score = models.IntegerField('キーワードスコア')
    improvement_suggestions = models.TextField('改善提案')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    
    class Meta:
        verbose_name = 'グレイプらしさ評価'
        verbose_name_plural = 'グレイプらしさ評価'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.category.name} - {self.total_score}点 ({self.created_at.strftime('%Y-%m-%d')})"

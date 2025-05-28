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


# 校正AI v2用モデル

class CorrectionV2(models.Model):
    """校正AI v2 - 詳細修正情報モデル"""
    
    CATEGORY_CHOICES = [
        ('tone', '言い回しアドバイス'),
        ('typo', '誤字修正'),
        ('dict', '社内辞書ルール'),
        ('geo', '地域矛盾チェック'),
    ]
    
    SEVERITY_CHOICES = [
        ('high', '高'),
        ('medium', '中'),
        ('low', '低'),
    ]
    
    request = models.ForeignKey(ProofreadingRequest, on_delete=models.CASCADE, related_name='corrections_v2')
    original_text = models.CharField('修正前テキスト', max_length=500)
    corrected_text = models.CharField('修正後テキスト', max_length=500)
    reason = models.TextField('修正理由')
    category = models.CharField('カテゴリー', max_length=10, choices=CATEGORY_CHOICES)
    confidence = models.FloatField('信頼度', help_text='0.0-1.0の範囲')
    position = models.IntegerField('文字位置', help_text='元テキスト内での開始位置')
    severity = models.CharField('重要度', max_length=10, choices=SEVERITY_CHOICES, default='medium')
    is_applied = models.BooleanField('適用済み', default=False)
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    
    class Meta:
        verbose_name = '校正修正v2'
        verbose_name_plural = '校正修正v2'
        ordering = ['position']
        
    def __str__(self):
        return f"{self.get_category_display()}: {self.original_text} → {self.corrected_text}"
    
    @property
    def category_color(self):
        """カテゴリーに応じた色を返す"""
        colors = {
            'tone': '#FEF3C7',  # 黄色
            'typo': '#FEE2E2',  # 赤色
            'dict': '#DBEAFE',  # 青色
            'geo': '#FED7AA',   # オレンジ色
        }
        return colors.get(self.category, '#F3F4F6')
    
    @property
    def category_border(self):
        """カテゴリーに応じたボーダー色を返す"""
        borders = {
            'tone': '#F59E0B',
            'typo': '#EF4444',
            'dict': '#3B82F6',
            'geo': '#F97316',
        }
        return borders.get(self.category, '#6B7280')
    
    @property
    def category_icon(self):
        """カテゴリーに応じたアイコンを返す"""
        icons = {
            'tone': '💬',
            'typo': '❌',
            'dict': '📚',
            'geo': '🗺️',
        }
        return icons.get(self.category, '📝')


class CompanyDictionary(models.Model):
    """社内辞書モデル"""
    
    CATEGORY_CHOICES = [
        ('general', '一般用語'),
        ('brand', 'ブランド名'),
        ('product', '製品名'),
        ('department', '部署名'),
        ('title', '役職名'),
        ('technical', '技術用語'),
        ('business', 'ビジネス用語'),
    ]
    
    term = models.CharField('用語', max_length=255)
    correct_form = models.CharField('正式表記', max_length=255)
    alternative_forms = models.TextField('代替表記', blank=True, help_text='カンマ区切りで複数指定可能')
    category = models.CharField('カテゴリー', max_length=50, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField('説明', blank=True)
    usage_example = models.TextField('使用例', blank=True)
    is_active = models.BooleanField('有効', default=True)
    priority = models.IntegerField('優先度', default=1, help_text='数値が大きいほど優先度が高い')
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        verbose_name = '社内辞書'
        verbose_name_plural = '社内辞書'
        ordering = ['-priority', 'term']
        
    def __str__(self):
        return f"{self.term} → {self.correct_form} ({self.get_category_display()})"
    
    def get_alternative_forms_list(self):
        """代替表記をリストで返す"""
        if self.alternative_forms:
            return [form.strip() for form in self.alternative_forms.split(',') if form.strip()]
        return []


class GeographicData(models.Model):
    """地理データモデル"""
    
    TYPE_CHOICES = [
        ('prefecture', '都道府県'),
        ('city', '市区町村'),
        ('region', '地域'),
        ('landmark', 'ランドマーク'),
    ]
    
    name = models.CharField('名称', max_length=255)
    type = models.CharField('種別', max_length=20, choices=TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name='親地域')
    latitude = models.FloatField('緯度', null=True, blank=True)
    longitude = models.FloatField('経度', null=True, blank=True)
    climate_zone = models.CharField('気候区分', max_length=50, blank=True)
    characteristics = models.TextField('特徴', blank=True, help_text='気候や地理的特徴など')
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', default=timezone.now)
    
    class Meta:
        verbose_name = '地理データ'
        verbose_name_plural = '地理データ'
        ordering = ['type', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})" 
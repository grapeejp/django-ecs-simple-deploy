from django import forms
from .models import Category

class GrapeCheckForm(forms.Form):
    """グレイプらしさチェックフォーム"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        empty_label="カテゴリを選択してください",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="カテゴリ"
    )
    
    content_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'ここにチェックしたいテキストを入力してください...'
        }),
        label="テキスト内容",
        required=True,
        max_length=10000,
        help_text="最大10,000文字まで入力できます。"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 親カテゴリでグループ化
        parent_categories = Category.objects.filter(parent__isnull=True, is_active=True)
        choices = []
        
        for parent in parent_categories:
            parent_group = [(parent.id, parent.name)]
            children = Category.objects.filter(parent=parent, is_active=True)
            
            if children:
                for child in children:
                    parent_group.append((child.id, f"-- {child.name}"))
            
            choices.append((parent.name, parent_group))
        
        if choices:
            self.fields['category'].choices = [('', '選択してください')] + choices 
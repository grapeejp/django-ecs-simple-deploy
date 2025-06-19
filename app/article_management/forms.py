from django import forms
from django.core.exceptions import ValidationError
from .models import Article, SocialMediaUser


class ArticleForm(forms.ModelForm):
    """記事フォーム"""
    
    class Meta:
        model = Article
        fields = [
            'title',
            'content',
            'reference_url',
            'writer',
            'social_media_users',
            'facebook_text',
            'notes',
            'status',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '記事タイトルを入力'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '記事の内容・概要を入力'
            }),
            'reference_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'writer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'social_media_users': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'size': 10
            }),
            'facebook_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Facebook投稿用のテキスト（省略可）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考・メモ（省略可）'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # SNSユーザーの選択肢をカスタマイズ
        self.fields['social_media_users'].queryset = SocialMediaUser.objects.all()
        self.fields['social_media_users'].label_from_instance = lambda obj: f"{obj.get_platform_display()} - {obj.handle_name} ({obj.get_status_display()})"
        
        # 新規作成時はステータスを非表示
        if not self.instance.pk:
            self.fields['status'].widget = forms.HiddenInput()
            self.fields['status'].initial = 'pending'
    
    def clean_social_media_users(self):
        """NGユーザーが選択されていないかチェック"""
        users = self.cleaned_data.get('social_media_users')
        if users:
            ng_users = users.filter(status='ng')
            if ng_users.exists():
                ng_names = ', '.join([f"{user.get_platform_display()} - {user.handle_name}" for user in ng_users])
                raise ValidationError(
                    f'NGユーザーが含まれています: {ng_names}'
                )
        return users


class SocialMediaUserForm(forms.ModelForm):
    """SNSユーザーフォーム"""
    
    class Meta:
        model = SocialMediaUser
        fields = [
            'handle_name',
            'platform',
            'profile_url',
            'status',
            'permission_date',
            'permission_expires',
            'usage_conditions',
            'ng_reason',
            'notes',
        ]
        widgets = {
            'handle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'platform': forms.Select(attrs={
                'class': 'form-control'
            }),
            'profile_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/username'
            }),
            'status': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'permission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'permission_expires': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'usage_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'クレジット表記など特別な利用条件'
            }),
            'ng_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'NGの理由（NGの場合のみ）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '備考・メモ'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        ng_reason = cleaned_data.get('ng_reason')
        
        # NGステータスの場合は理由を必須に
        if status == 'ng' and not ng_reason:
            raise ValidationError({
                'ng_reason': 'NGの場合は理由を入力してください。'
            })
        
        return cleaned_data
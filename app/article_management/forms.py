from django import forms
from django.core.exceptions import ValidationError
from .models import Article, SocialMediaUser, PersonalSNSAccount, CorporateSNSAccount
import re


class ArticleForm(forms.ModelForm):
    """記事フォーム"""
    
    class Meta:
        model = Article
        fields = [
            'title',
            'content',
            'reference_url',
            'grape_article_url',
            'social_media_id',
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
                'placeholder': '参照元のSNS投稿URL等'
            }),
            'grape_article_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://grapee.jp/...'
            }),
            'social_media_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SNS投稿のID（Instagramは手動入力）'
            }),
            'writer': forms.Select(attrs={
                'class': 'form-control'
            }),
            'social_media_users': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 10
            }),
            'facebook_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Facebook投稿用のテキスト（1行24文字以内、最大2行）'
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
    
    def clean_facebook_text(self):
        """Facebook投稿テキストのバリデーション（1行24文字以内、最大2行）"""
        facebook_text = self.cleaned_data.get('facebook_text', '')
        if not facebook_text:
            return facebook_text
        
        # 改行で分割
        lines = facebook_text.strip().split('\n')
        
        # 3行以上はエラー
        if len(lines) > 2:
            raise ValidationError('Facebook投稿は最大2行までです。')
        
        # 各行が24文字以内かチェック
        for i, line in enumerate(lines, 1):
            if len(line) > 24:
                raise ValidationError(f'{i}行目が24文字を超えています（{len(line)}文字）。1行は24文字以内にしてください。')
        
        return facebook_text
    
    def clean_reference_url(self):
        """参考記事URLの重複チェック"""
        reference_url = self.cleaned_data.get('reference_url')
        if not reference_url:
            return reference_url
        
        # 既存の記事で同じURLが使用されているかチェック
        existing_articles = Article.objects.filter(reference_url=reference_url)
        
        # 編集時は自分自身を除外
        if self.instance.pk:
            existing_articles = existing_articles.exclude(pk=self.instance.pk)
        
        if existing_articles.exists():
            existing_article = existing_articles.first()
            raise ValidationError(
                f'このURLは既に記事番号 {existing_article.article_id} で使用されています。'
            )
        
        return reference_url


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


class PersonalSNSAccountForm(forms.ModelForm):
    """個人SNSアカウントフォーム"""
    
    class Meta:
        model = PersonalSNSAccount
        fields = [
            'handle_name',
            'real_name',
            'platform',
            'url',
            'status',
            'category',
            'reason',
            'conditions',
            'notes',
        ]
        widgets = {
            'handle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username または ハンドルネーム'
            }),
            'real_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '本名（省略可）'
            }),
            'platform': forms.Select(attrs={
                'class': 'form-control'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/username'
            }),
            'status': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'NGまたは条件付きの理由'
            }),
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '利用条件（クレジット表記など）'
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
        reason = cleaned_data.get('reason')
        
        # NGまたは条件付きの場合は理由を必須に
        if status in ['ng', 'conditional'] and not reason:
            raise ValidationError({
                'reason': f'{self.fields["status"].choices[self.fields["status"].choices.index((status, ""))][1]}の場合は理由を入力してください。'
            })
        
        return cleaned_data


class CorporateSNSAccountForm(forms.ModelForm):
    """企業SNSアカウントフォーム"""
    
    class Meta:
        model = CorporateSNSAccount
        fields = [
            'company_name',
            'account_name',
            'platform',
            'url',
            'sales_status',
            'editorial_status',
            'require_prior_approval',
            'require_post_report',
            'embed_only',
            'allow_image_download',
            'allow_screenshot',
            'credit_format',
            'excluded_content',
            'special_conditions',
            'primary_contact',
            'pr_agency',
            'contact_notes',
            'notes',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '企業名'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'アカウント名'
            }),
            'platform': forms.Select(attrs={
                'class': 'form-control'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/company'
            }),
            'sales_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'editorial_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'require_prior_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'require_post_report': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'embed_only': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_image_download': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_screenshot': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'credit_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'クレジット表記の形式（例：〇〇提供）'
            }),
            'excluded_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '使用不可のコンテンツ（例：競合他社関連、特定の投稿）'
            }),
            'special_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'その他の特殊条件'
            }),
            'primary_contact': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '主要連絡先（担当者名、メールアドレス、電話番号など）'
            }),
            'pr_agency': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'PR会社情報（省略可）'
            }),
            'contact_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '連絡時の注意事項（省略可）'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '補足情報'
            }),
        }
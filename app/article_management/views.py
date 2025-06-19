from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import (
    Article, SocialMediaUser, ArticleHistory,
    PersonalSNSAccount, CorporateSNSAccount
)
from .forms import ArticleForm, SocialMediaUserForm, PersonalSNSAccountForm, CorporateSNSAccountForm
from .utils import SNSAccountChecker


class DashboardView(LoginRequiredMixin, TemplateView):
    """記事管理ダッシュボード"""
    template_name = 'article_management/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        context['pending_count'] = Article.objects.filter(status='pending').count()
        context['approved_count'] = Article.objects.filter(status='approved').count()
        context['today_articles'] = Article.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        # 最近の記事
        context['recent_articles'] = Article.objects.select_related(
            'applicant', 'writer'
        ).order_by('-created_at')[:5]
        
        # NGユーザーを含む記事
        context['ng_articles'] = Article.objects.filter(
            social_media_users__status='ng'
        ).distinct()[:5]
        
        # ユーザー別統計（自分の記事のみ）
        if not self.request.user.is_staff:
            context['my_articles'] = {
                'total': Article.objects.filter(applicant=self.request.user).count(),
                'pending': Article.objects.filter(
                    applicant=self.request.user,
                    status='pending'
                ).count(),
                'approved': Article.objects.filter(
                    applicant=self.request.user,
                    status='approved'
                ).count(),
            }
        
        return context


class ArticleListView(LoginRequiredMixin, ListView):
    """記事一覧"""
    model = Article
    template_name = 'article_management/article_list.html'
    context_object_name = 'articles'
    paginate_by = 300
    
    def get_queryset(self):
        queryset = Article.objects.select_related(
            'applicant', 'writer'
        ).prefetch_related('social_media_users')
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(content__icontains=search) |
                Q(article_id__icontains=search) |
                Q(social_media_id__icontains=search)
            )
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # ライターフィルター（スタッフのみ）
        if self.request.user.is_staff:
            writer_id = self.request.GET.get('writer')
            if writer_id:
                queryset = queryset.filter(writer_id=writer_id)
        else:
            # 一般ユーザーは自分の記事のみ
            queryset = queryset.filter(
                Q(applicant=self.request.user) | Q(writer=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            context['writers'] = User.objects.filter(is_active=True).order_by('username')
        return context


class ArticleDetailView(LoginRequiredMixin, DetailView):
    """記事詳細"""
    model = Article
    template_name = 'article_management/article_detail.html'
    context_object_name = 'article'
    slug_field = 'article_id'
    slug_url_kwarg = 'article_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['histories'] = self.object.histories.select_related('user').all()
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """記事作成"""
    model = Article
    form_class = ArticleForm
    template_name = 'article_management/article_form.html'
    success_url = reverse_lazy('article_management:article_list')
    
    def form_valid(self, form):
        # 申請者を現在のユーザーに設定
        form.instance.applicant = self.request.user
        
        response = super().form_valid(form)
        
        # 履歴を記録
        ArticleHistory.objects.create(
            article=self.object,
            user=self.request.user,
            action='記事作成',
            new_value=self.object.title
        )
        
        return response


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """記事編集"""
    model = Article
    form_class = ArticleForm
    template_name = 'article_management/article_form.html'
    success_url = reverse_lazy('article_management:article_list')
    slug_field = 'article_id'
    slug_url_kwarg = 'article_id'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # スタッフ以外は自分の記事のみ編集可能
            queryset = queryset.filter(
                Q(applicant=self.request.user) | Q(writer=self.request.user)
            )
        return queryset
    
    def form_valid(self, form):
        # 変更前の状態を保存
        old_status = self.object.status
        
        response = super().form_valid(form)
        
        # ステータス変更の履歴を記録
        if old_status != self.object.status:
            ArticleHistory.objects.create(
                article=self.object,
                user=self.request.user,
                action='ステータス変更',
                old_value=dict(Article.STATUS_CHOICES)[old_status],
                new_value=self.object.get_status_display()
            )
        
        return response


class SocialMediaUserListView(LoginRequiredMixin, ListView):
    """SNSユーザー一覧"""
    model = SocialMediaUser
    template_name = 'article_management/social_user_list.html'
    context_object_name = 'users'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = SocialMediaUser.objects.all()
        
        # プラットフォームフィルター
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(handle_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('platform', 'handle_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        
        # 統計情報を追加
        all_users = SocialMediaUser.objects.all()
        context['ok_users_count'] = all_users.filter(status='ok').count()
        context['ng_users_count'] = all_users.filter(status='ng').count()
        context['twitter_count'] = all_users.filter(platform='twitter').count()
        context['instagram_count'] = all_users.filter(platform='instagram').count()
        
        return context


class SocialMediaUserCreateView(LoginRequiredMixin, CreateView):
    """SNSユーザー作成"""
    model = SocialMediaUser
    form_class = SocialMediaUserForm
    template_name = 'article_management/social_user_form.html'
    success_url = reverse_lazy('article_management:social_user_list')


class SocialMediaUserUpdateView(LoginRequiredMixin, UpdateView):
    """SNSユーザー編集"""
    model = SocialMediaUser
    form_class = SocialMediaUserForm
    template_name = 'article_management/social_user_form.html'
    success_url = reverse_lazy('article_management:social_user_list')


@login_required
def check_social_users(request):
    """SNSユーザーの許諾状況をチェックするAPI"""
    user_ids = request.GET.getlist('user_ids[]')
    
    if not user_ids:
        return JsonResponse({'users': []})
    
    users = SocialMediaUser.objects.filter(id__in=user_ids)
    
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'handle_name': user.handle_name,
            'platform': user.get_platform_display(),
            'status': user.status,
            'is_valid': user.is_permission_valid(),
            'ng_reason': user.ng_reason if user.status == 'ng' else None,
        })
    
    return JsonResponse({'users': result})


class PersonalSNSAccountListView(LoginRequiredMixin, ListView):
    """個人SNSアカウント一覧"""
    model = PersonalSNSAccount
    template_name = 'article_management/personal_account_list.html'
    context_object_name = 'accounts'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = PersonalSNSAccount.objects.all()
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # プラットフォームフィルター
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # カテゴリフィルター
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(handle_name__icontains=search) |
                Q(real_name__icontains=search) |
                Q(reason__icontains=search) |
                Q(conditions__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-status', 'handle_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        all_accounts = PersonalSNSAccount.objects.all()
        context['stats'] = {
            'total': all_accounts.count(),
            'ok': all_accounts.filter(status='ok').count(),
            'conditional': all_accounts.filter(status='conditional').count(),
            'ng': all_accounts.filter(status='ng').count(),
        }
        
        # フィルター選択肢
        context['status_choices'] = PersonalSNSAccount.STATUS_CHOICES
        context['platform_choices'] = PersonalSNSAccount.PLATFORM_CHOICES
        context['category_choices'] = PersonalSNSAccount.CATEGORY_CHOICES
        
        return context


class CorporateSNSAccountListView(LoginRequiredMixin, ListView):
    """企業SNSアカウント一覧"""
    model = CorporateSNSAccount
    template_name = 'article_management/corporate_account_list.html'
    context_object_name = 'accounts'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = CorporateSNSAccount.objects.all()
        
        # 総合ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            if status == 'ok':
                queryset = queryset.filter(sales_status='ok', editorial_status='ok')
            elif status == 'ng':
                queryset = queryset.filter(
                    Q(sales_status='ng') | Q(editorial_status='ng')
                )
            elif status == 'checking':
                queryset = queryset.filter(
                    Q(sales_status='checking') | Q(editorial_status='checking')
                ).exclude(
                    Q(sales_status='ng') | Q(editorial_status='ng')
                )
        
        # プラットフォームフィルター
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # 条件フィルター
        if self.request.GET.get('require_prior_approval'):
            queryset = queryset.filter(require_prior_approval=True)
        if self.request.GET.get('embed_only'):
            queryset = queryset.filter(embed_only=True)
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(account_name__icontains=search) |
                Q(primary_contact__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('company_name', 'account_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        all_accounts = CorporateSNSAccount.objects.all()
        ok_count = all_accounts.filter(sales_status='ok', editorial_status='ok').count()
        ng_count = all_accounts.filter(
            Q(sales_status='ng') | Q(editorial_status='ng')
        ).count()
        checking_count = all_accounts.count() - ok_count - ng_count
        
        context['stats'] = {
            'total': all_accounts.count(),
            'ok': ok_count,
            'checking': checking_count,
            'ng': ng_count,
        }
        
        # フィルター選択肢
        context['platform_choices'] = PersonalSNSAccount.PLATFORM_CHOICES
        
        return context


@login_required
def check_sns_url(request):
    """URLからSNSアカウントの利用可否をチェックするAPI"""
    url = request.GET.get('url', '')
    
    if not url:
        return JsonResponse({
            'status': 'error',
            'message': 'URLが指定されていません'
        })
    
    result = SNSAccountChecker.check_url(url)
    
    # アカウント情報を追加
    if result['account']:
        account = result['account']
        if result['type'] == 'personal':
            result['account_info'] = {
                'handle_name': account.handle_name,
                'platform': account.get_platform_display(),
                'category': account.get_category_display() if account.category else None,
            }
        else:  # corporate
            result['account_info'] = {
                'company_name': account.company_name,
                'account_name': account.account_name,
                'platform': account.get_platform_display(),
                'sales_status': account.get_sales_status_display(),
                'editorial_status': account.get_editorial_status_display(),
            }
    
    # アカウントインスタンスは削除（JSONシリアライズできないため）
    result.pop('account', None)
    
    return JsonResponse(result)


@login_required
@require_POST
def update_report_status(request):
    """掲載報告ステータスを更新するAPI"""
    try:
        data = json.loads(request.body)
        article_id = data.get('article_id')
        report_status = data.get('report_status')
        
        # 記事を取得
        article = get_object_or_404(Article, article_id=article_id)
        
        # 権限チェック（スタッフまたは申請者/ライター）
        if not (request.user.is_staff or 
                article.applicant == request.user or 
                article.writer == request.user):
            return JsonResponse({'success': False, 'error': '権限がありません'}, status=403)
        
        # ステータスを更新
        article.report_status = report_status
        article.save()
        
        # 履歴を記録
        ArticleHistory.objects.create(
            article=article,
            user=request.user,
            action='掲載報告ステータス変更',
            new_value=dict(Article.REPORT_STATUS_CHOICES).get(report_status, report_status)
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


class PersonalSNSAccountListView(LoginRequiredMixin, ListView):
    """個人SNSアカウント一覧"""
    model = PersonalSNSAccount
    template_name = 'article_management/personal_account_list.html'
    context_object_name = 'accounts'
    paginate_by = 300
    
    def get_queryset(self):
        queryset = PersonalSNSAccount.objects.all()
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(handle_name__icontains=search) |
                Q(real_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # ステータスフィルター
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # プラットフォームフィルター
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # カテゴリフィルター
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('handle_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        all_accounts = PersonalSNSAccount.objects.all()
        context['stats'] = {
            'total': all_accounts.count(),
            'ok': all_accounts.filter(status='ok').count(),
            'conditional': all_accounts.filter(status='conditional').count(),
            'ng': all_accounts.filter(status='ng').count(),
        }
        
        # フィルター用の選択肢
        context['status_choices'] = PersonalSNSAccount.STATUS_CHOICES
        context['platform_choices'] = PersonalSNSAccount.PLATFORM_CHOICES
        context['category_choices'] = PersonalSNSAccount.CATEGORY_CHOICES
        
        return context


class PersonalSNSAccountCreateView(LoginRequiredMixin, CreateView):
    """個人SNSアカウント作成"""
    model = PersonalSNSAccount
    form_class = PersonalSNSAccountForm
    template_name = 'article_management/personal_account_form.html'
    success_url = reverse_lazy('article_management:personal_account_list')


class PersonalSNSAccountUpdateView(LoginRequiredMixin, UpdateView):
    """個人SNSアカウント編集"""
    model = PersonalSNSAccount
    form_class = PersonalSNSAccountForm
    template_name = 'article_management/personal_account_form.html'
    success_url = reverse_lazy('article_management:personal_account_list')


class CorporateSNSAccountListView(LoginRequiredMixin, ListView):
    """企業SNSアカウント一覧"""
    model = CorporateSNSAccount
    template_name = 'article_management/corporate_account_list.html'
    context_object_name = 'accounts'
    paginate_by = 300
    
    def get_queryset(self):
        queryset = CorporateSNSAccount.objects.all()
        
        # 検索
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) |
                Q(account_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        # ステータスフィルター（厳しい方を採用）
        status = self.request.GET.get('status')
        if status == 'ok':
            queryset = queryset.filter(sales_status='ok', editorial_status='ok')
        elif status == 'checking':
            queryset = queryset.filter(
                Q(sales_status='checking') | Q(editorial_status='checking')
            ).exclude(sales_status='ng', editorial_status='ng')
        elif status == 'ng':
            queryset = queryset.filter(
                Q(sales_status='ng') | Q(editorial_status='ng')
            )
        
        # プラットフォームフィルター
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # 条件フィルター
        if self.request.GET.get('require_prior_approval'):
            queryset = queryset.filter(require_prior_approval=True)
        if self.request.GET.get('embed_only'):
            queryset = queryset.filter(embed_only=True)
        
        return queryset.order_by('company_name', 'account_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 統計情報
        all_accounts = CorporateSNSAccount.objects.all()
        ok_count = all_accounts.filter(sales_status='ok', editorial_status='ok').count()
        checking_count = all_accounts.filter(
            Q(sales_status='checking') | Q(editorial_status='checking')
        ).exclude(Q(sales_status='ng') | Q(editorial_status='ng')).count()
        ng_count = all_accounts.filter(
            Q(sales_status='ng') | Q(editorial_status='ng')
        ).count()
        
        context['stats'] = {
            'total': all_accounts.count(),
            'ok': ok_count,
            'checking': checking_count,
            'ng': ng_count,
        }
        
        # フィルター用の選択肢
        context['platform_choices'] = PersonalSNSAccount.PLATFORM_CHOICES
        
        return context


class CorporateSNSAccountCreateView(LoginRequiredMixin, CreateView):
    """企業SNSアカウント作成"""
    model = CorporateSNSAccount
    form_class = CorporateSNSAccountForm
    template_name = 'article_management/corporate_account_form.html'
    success_url = reverse_lazy('article_management:corporate_account_list')


class CorporateSNSAccountUpdateView(LoginRequiredMixin, UpdateView):
    """企業SNSアカウント編集"""
    model = CorporateSNSAccount
    form_class = CorporateSNSAccountForm
    template_name = 'article_management/corporate_account_form.html'
    success_url = reverse_lazy('article_management:corporate_account_list')

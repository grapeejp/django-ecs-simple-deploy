from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from .models import Article, SocialMediaUser, ArticleHistory
from .forms import ArticleForm, SocialMediaUserForm


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
    paginate_by = 20
    
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

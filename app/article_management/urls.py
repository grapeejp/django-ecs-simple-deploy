from django.urls import path
from . import views

app_name = 'article_management'

urlpatterns = [
    # 記事管理（記事一覧をトップに）
    path('', views.ArticleListView.as_view(), name='article_list'),
    
    # SNSユーザー管理
    path('social-users/', views.SocialMediaUserListView.as_view(), name='social_user_list'),
    path('social-users/create/', views.SocialMediaUserCreateView.as_view(), name='social_user_create'),
    path('social-users/<int:pk>/edit/', views.SocialMediaUserUpdateView.as_view(), name='social_user_edit'),
    
    # 個人SNSアカウント管理
    path('personal-accounts/', views.PersonalSNSAccountListView.as_view(), name='personal_account_list'),
    path('personal-accounts/create/', views.PersonalSNSAccountCreateView.as_view(), name='personal_account_create'),
    path('personal-accounts/<int:pk>/edit/', views.PersonalSNSAccountUpdateView.as_view(), name='personal_account_edit'),
    
    # 企業SNSアカウント管理
    path('corporate-accounts/', views.CorporateSNSAccountListView.as_view(), name='corporate_account_list'),
    path('corporate-accounts/create/', views.CorporateSNSAccountCreateView.as_view(), name='corporate_account_create'),
    path('corporate-accounts/<int:pk>/edit/', views.CorporateSNSAccountUpdateView.as_view(), name='corporate_account_edit'),
    
    # API
    path('api/check-social-users/', views.check_social_users, name='check_social_users'),
    path('api/check-sns-url/', views.check_sns_url, name='check_sns_url'),
    path('api/update-report-status/', views.update_report_status, name='update_report_status'),
    
    # 記事詳細系（最後に配置して他のパスを優先）
    path('create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('<str:article_id>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('<str:article_id>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
]
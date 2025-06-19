from django.urls import path
from . import views

app_name = 'article_management'

urlpatterns = [
    # ダッシュボード
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # 記事管理
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<str:article_id>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('articles/<str:article_id>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    
    # SNSユーザー管理
    path('social-users/', views.SocialMediaUserListView.as_view(), name='social_user_list'),
    path('social-users/create/', views.SocialMediaUserCreateView.as_view(), name='social_user_create'),
    path('social-users/<int:pk>/edit/', views.SocialMediaUserUpdateView.as_view(), name='social_user_edit'),
    
    # API
    path('api/check-social-users/', views.check_social_users, name='check_social_users'),
]
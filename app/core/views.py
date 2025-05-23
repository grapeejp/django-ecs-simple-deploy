from django.shortcuts import render
from django.views.generic import TemplateView

class DashboardView(TemplateView):
    """ダッシュボード表示ビュー"""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ここに必要なコンテキストデータを追加
        return context 
from django.shortcuts import render, redirect
from django.views.generic import FormView, DetailView, ListView
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings

from .models import Category, GrapeCheck
from .forms import GrapeCheckForm
from .services.bedrock_client import BedrockClient

import logging
import json

logger = logging.getLogger(__name__)

class GrapeCheckFormView(FormView):
    """グレイプらしさチェックフォームビュー"""
    template_name = 'grapecheck/check_form.html'
    form_class = GrapeCheckForm
    success_url = '/grapecheck/results/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True, is_active=True)
        return context

    def form_valid(self, form):
        text = form.cleaned_data['content_text']
        category_id = form.cleaned_data['category']
        
        category = Category.objects.get(id=category_id)
        parent_category = category
        subcategory = None
        
        if category.parent:
            parent_category = category.parent
            subcategory = category.name
        
        try:
            client = BedrockClient(region_name=getattr(settings, 'AWS_REGION', None))
            result = client.evaluate_grape_style(text, parent_category.name, subcategory)
            
            # 評価結果を保存
            check_result = GrapeCheck.objects.create(
                category=category,
                content_text=text,
                total_score=result['total_score'],
                writing_style_score=result['writing_style_score'],
                structure_score=result['structure_score'],
                keyword_score=result['keyword_score'],
                improvement_suggestions=result['improvement_suggestions']
            )
            
            # セッションに結果IDを保存
            self.request.session['check_result_id'] = check_result.id
            return redirect('grapecheck:results', pk=check_result.id)
            
        except Exception as e:
            logger.error(f"評価処理エラー: {str(e)}")
            messages.error(self.request, f"評価処理中にエラーが発生しました: {str(e)}")
            return self.form_invalid(form)


class GrapeCheckResultView(DetailView):
    """グレイプらしさチェック結果ビュー"""
    model = GrapeCheck
    template_name = 'grapecheck/check_result.html'
    context_object_name = 'result'
    

class GrapeCheckHistoryListView(ListView):
    """グレイプらしさチェック履歴一覧ビュー"""
    model = GrapeCheck
    template_name = 'grapecheck/check_history.html'
    context_object_name = 'results'
    paginate_by = 10
    ordering = ['-created_at']

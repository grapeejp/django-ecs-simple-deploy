from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
import logging
import time

from .models import ProofreadingRequest, ProofreadingResult, ReplacementDictionary
from .services.bedrock_client import BedrockClient
from .utils import get_html_diff, protect_html_tags, restore_html_tags

logger = logging.getLogger(__name__)

def index(request):
    """
    校正AIのメインページを表示
    """
    return render(request, 'proofreading_ai/index.html')


@require_POST
def proofread(request):
    """
    テキストを校正してJSONレスポンスを返す
    """
    try:
        # POSTデータの取得
        data = json.loads(request.body)
        original_text = data.get('text', '')
        
        if not original_text:
            return JsonResponse({
                'success': False,
                'error': '校正するテキストが入力されていません。'
            })
        
        # HTMLタグを保護
        protected_text, placeholders = protect_html_tags(original_text)
        
        # リクエストをDBに保存
        proofread_request = ProofreadingRequest.objects.create(
            original_text=original_text
        )
        
        # Bedrock APIを使用して校正
        client = BedrockClient()
        
        # 置換辞書の取得（有効なもののみ）
        replacements = ReplacementDictionary.objects.filter(is_active=True).values(
            'original_word', 'replacement_word'
        )
        
        # 校正実行
        corrected_text, completion_time = client.proofread_text(protected_text)
        
        # HTMLタグを復元
        corrected_text = restore_html_tags(corrected_text, placeholders)
        
        # 校正結果をDBに保存
        result = ProofreadingResult.objects.create(
            request=proofread_request,
            corrected_text=corrected_text,
            completion_time=completion_time
        )
        
        # 差分HTMLの生成
        diff_html = get_html_diff(original_text, corrected_text)
        
        return JsonResponse({
            'success': True,
            'original_text': original_text,
            'corrected_text': corrected_text,
            'diff_html': diff_html,
            'completion_time': completion_time
        })
        
    except Exception as e:
        logger.error(f"校正処理中にエラーが発生しました: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'校正処理中にエラーが発生しました: {str(e)}'
        })


@login_required
def history(request):
    """
    校正履歴を表示
    """
    history_items = ProofreadingRequest.objects.all().order_by('-created_at')[:50]
    return render(request, 'proofreading_ai/history.html', {
        'history_items': history_items
    })


@login_required
def dictionary(request):
    """
    置換辞書の管理ページを表示
    """
    dictionaries = ReplacementDictionary.objects.all().order_by('original_word')
    return render(request, 'proofreading_ai/dictionary.html', {
        'dictionaries': dictionaries
    }) 
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
import logging
import time
import threading
import uuid
import html
from django.utils.html import escape
import re
import traceback

from .models import ProofreadingRequest, ProofreadingResult, ReplacementDictionary
# 本番用とモック用両方をインポート
from .services.bedrock_client import BedrockClient
from .services.mock_bedrock_client import MockBedrockClient
from .utils import get_html_diff, protect_html_tags, restore_html_tags, format_corrections, parse_corrections_from_text

logger = logging.getLogger(__name__)

# モックを使用するかどうか（実際の運用ではFalseにする）
USE_MOCK = False

def index(request):
    """
    校正AIのメインページを表示
    """
    # 置換辞書の取得（有効なもののみ）
    dictionaries = ReplacementDictionary.objects.filter(is_active=True).values('original_word', 'replacement_word')
    replacement_dict = {item['original_word']: item['replacement_word'] for item in dictionaries}
    
    return render(request, 'proofreading_ai/index.html', {
        'replacement_dict': json.dumps(replacement_dict, ensure_ascii=False)
    })


@csrf_exempt
@require_POST
def proofread(request):
    """
    テキストを校正してJSONレスポンスを返す
    """
    try:
        # POSTデータの取得
        data = json.loads(request.body)
        original_text = data.get('text', '')
        temperature = float(data.get('temperature', 0.1))
        top_p = float(data.get('top_p', 0.7))
        
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
        
        # 置換辞書の取得（有効なもののみ）
        dictionaries = ReplacementDictionary.objects.filter(is_active=True).values('original_word', 'replacement_word')
        replacement_dict = {item['original_word']: item['replacement_word'] for item in dictionaries}
        
        # Bedrock APIを使用して校正
        client = BedrockClient()
        
        # 校正実行
        corrected_text, tool_uses, usage, model, completion_time, cost_info = client.proofread_text(
            protected_text, replacement_dict
        )
        print('DEBUG 校正AI返り値:', corrected_text, tool_uses, usage, model, completion_time, cost_info)
        
        # HTMLタグを復元
        corrected_text = restore_html_tags(corrected_text, placeholders)
        
        # 修正箇所リストをパース
        corrections = parse_corrections_from_text(corrected_text)
        
        # ハイライトHTMLを生成
        if corrections:
            highlighted_html = format_corrections(original_text, corrections)
        else:
            highlighted_html = format_corrections(corrected_text, [])
        
        # 校正結果をDBに保存
        result = ProofreadingResult.objects.create(
            request=proofread_request,
            corrected_text=highlighted_html,
            completion_time=completion_time
        )
        
        # Claude 3.7のtool_uses, usage, modelも返す
        return JsonResponse({
            'success': True,
            'id': proofread_request.id,
            'original_text': original_text,
            'corrected_text': highlighted_html,
            'tool_uses': tool_uses,
            'usage': usage,
            'model': model,
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0),
            'total_cost': cost_info.get('total_cost', 0),
            'corrections': corrections,
        })
        
    except Exception as e:
        logger.error('校正AIエラー: %s', str(e))
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'校正処理中にエラーが発生しました: {str(e)}\n{traceback.format_exc()}'})


@csrf_exempt
@require_POST
def proofread_async(request):
    """
    非同期で校正処理を開始し、処理IDを返す
    フロントエンドはこのIDを使って処理状況を確認する
    """
    try:
        # POSTデータの取得
        data = json.loads(request.body)
        original_text = data.get('text', '')
        temperature = float(data.get('temperature', 0.1))
        top_p = float(data.get('top_p', 0.7))
        
        if not original_text:
            return JsonResponse({
                'success': False,
                'error': '校正するテキストが入力されていません。'
            })
        
        # 処理IDを生成
        process_id = str(uuid.uuid4())
        
        # 非同期処理開始
        thread = threading.Thread(
            target=process_proofread_async,
            args=(process_id, original_text, temperature, top_p)
        )
        thread.start()
        
        return JsonResponse({
            'success': True,
            'process_id': process_id,
            'message': '校正処理を開始しました。'
        })
        
    except Exception as e:
        logger.error(f"非同期校正処理の開始中にエラーが発生しました: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'校正処理の開始に失敗しました: {str(e)}'
        })


def process_proofread_async(process_id, original_text, temperature, top_p):
    """
    非同期で校正処理を実行する
    """
    try:
        # HTMLタグを保護
        protected_text, placeholders = protect_html_tags(original_text)
        
        # リクエストをDBに保存
        proofread_request = ProofreadingRequest.objects.create(
            original_text=original_text
        )
        
        # 置換辞書の取得（有効なもののみ）
        dictionaries = ReplacementDictionary.objects.filter(is_active=True).values('original_word', 'replacement_word')
        replacement_dict = {item['original_word']: item['replacement_word'] for item in dictionaries}
        
        # Bedrock APIを使用して校正
        client = BedrockClient()
        
        # 校正実行
        corrected_text, tool_uses, usage, model, completion_time, cost_info = client.proofread_text(
            protected_text, replacement_dict
        )
        print('DEBUG 校正AI返り値:', corrected_text, tool_uses, usage, model, completion_time, cost_info)
        
        # HTMLタグを復元
        corrected_text = restore_html_tags(corrected_text, placeholders)
        
        # 修正箇所リストをパース
        corrections = parse_corrections_from_text(corrected_text)
        
        # ハイライトHTMLを生成
        if corrections:
            highlighted_html = format_corrections(original_text, corrections)
        else:
            highlighted_html = format_corrections(corrected_text, [])
        
        # 校正結果をDBに保存
        result = ProofreadingResult.objects.create(
            request=proofread_request,
            corrected_text=highlighted_html,
            completion_time=completion_time
        )
        
        # Claude 3.7のtool_uses, usage, modelも返す
        return JsonResponse({
            'success': True,
            'id': proofread_request.id,
            'original_text': original_text,
            'corrected_text': highlighted_html,
            'tool_uses': tool_uses,
            'usage': usage,
            'model': model,
            'input_tokens': usage.get('input_tokens', 0),
            'output_tokens': usage.get('output_tokens', 0),
            'total_cost': cost_info.get('total_cost', 0),
            'corrections': corrections,
        })
        
    except Exception as e:
        logger.error(f"非同期校正処理中にエラーが発生しました: {str(e)}")
        # エラー情報をキャッシュに保存
        from django.core.cache import cache
        cache.set(
            f"proofread_result_{process_id}",
            {
                'success': False,
                'status': 'error',
                'error': str(e)
            },
            timeout=3600
        )


@csrf_exempt
@require_POST
def check_proofread_status(request):
    """
    非同期校正処理の状況を確認するエンドポイント
    """
    try:
        data = json.loads(request.body)
        process_id = data.get('process_id')
        
        if not process_id:
            return JsonResponse({
                'success': False,
                'error': '処理IDが指定されていません。'
            })
        
        # キャッシュから処理結果を取得
        from django.core.cache import cache
        result = cache.get(f"proofread_result_{process_id}")
        
        if result is None:
            # 処理中または結果が見つからない
            return JsonResponse({
                'success': True,
                'status': 'processing',
                'message': '処理中です。'
            })
        
        # 結果をそのまま返す
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"処理状況の確認中にエラーが発生しました: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'処理状況の確認に失敗しました: {str(e)}'
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


@login_required
@require_POST
def add_dictionary(request):
    """
    置換辞書に新しい項目を追加
    """
    try:
        original_word = request.POST.get('original_word')
        replacement_word = request.POST.get('replacement_word')
        
        if not original_word or not replacement_word:
            return JsonResponse({
                'success': False,
                'error': '置換前と置換後の単語を入力してください。'
            })
        
        # 既存エントリの確認（同じ原語があれば更新）
        try:
            entry = ReplacementDictionary.objects.get(original_word=original_word)
            entry.replacement_word = replacement_word
            entry.save()
            message = f"置換辞書の項目を更新しました: {original_word} → {replacement_word}"
        except ReplacementDictionary.DoesNotExist:
            # 新規作成
            ReplacementDictionary.objects.create(
                original_word=original_word,
                replacement_word=replacement_word
            )
            message = f"置換辞書に項目を追加しました: {original_word} → {replacement_word}"
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"置換辞書の更新中にエラーが発生しました: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'置換辞書の更新に失敗しました: {str(e)}'
        }) 
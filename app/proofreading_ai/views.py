from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
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
import boto3
import os
from django.conf import settings
import csv
from datetime import datetime, timezone, timedelta
from django.core.cache import cache
from django.utils import timezone as django_timezone

from .models import ProofreadingRequest, ProofreadingResult, ReplacementDictionary
# 本番用とモック用両方をインポート
from .services.bedrock_client import BedrockClient
from .services.mock_bedrock_client import MockBedrockClient
from .utils import (
    protect_html_tags_advanced, 
    restore_html_tags_advanced, 
    format_corrections,
    parse_corrections_from_text
)

# チャットワーク通知サービスをインポート
from .services.notification_service import chatwork_service, ChatworkNotificationService

logger = logging.getLogger(__name__)

# モックを使用するかどうか（実際の運用ではFalseにする）
USE_MOCK = False

def get_replacement_dict():
    """
    置換辞書を取得する
    
    Returns:
        dict: 置換辞書（キー: 元の単語、値: 置換後の単語）
    """
    try:
        dictionaries = ReplacementDictionary.objects.filter(is_active=True).values('original_word', 'replacement_word')
        replacement_dict = {item['original_word']: item['replacement_word'] for item in dictionaries}
        logger.info(f"📚 置換辞書取得成功: {len(replacement_dict)}件")
        return replacement_dict
    except Exception as e:
        logger.error(f"❌ 置換辞書取得エラー: {str(e)}")
        return {}

# @login_required  # 一時的にコメントアウト（テスト用）
def index(request):
    """
    校正AIのメインページを表示
    """
    replacement_dict = get_replacement_dict()
    return render(request, 'proofreading_ai/index.html', {
        'replacement_dict': json.dumps(replacement_dict, ensure_ascii=False)
    })


@csrf_exempt
@require_http_methods(["POST"])
def proofread(request):
    """
    テキストを校正してJSONレスポンスを返す（JSONモード対応）
    """
    start_time = time.time()
    logger.info("🚀 校正API呼び出し開始（JSONモード）")
    
    try:
        # リクエストデータの解析
        data = json.loads(request.body)
        text = data.get('text', '')
        use_json_mode = data.get('use_json_mode', True)  # デフォルトはJSONモード
        use_simple_prompt = data.get('use_simple_prompt', False)  # デフォルトは標準プロンプト
        
        logger.info(f"📝 入力テキスト長: {len(text)}文字")
        logger.info(f"⚙️ JSONモード: {use_json_mode}")
        logger.info(f"🚀 シンプルプロンプト: {use_simple_prompt}")
        
        if not text.strip():
            logger.warning("❌ 空のテキストが送信されました")
            return JsonResponse({
                'success': False, 
                'error': '校正するテキストが入力されていません。'
            })
        
        # BedrockClient初期化と校正実行
        logger.info("🤖 BedrockClient初期化開始")
        bedrock_client = BedrockClient()
        logger.info("✅ BedrockClient初期化完了")
        
        logger.info("🔍 Claude 4で校正実行開始")
        result = bedrock_client.proofread_text(text, use_json_mode=use_json_mode, use_simple_prompt=use_simple_prompt)
        logger.info(f"✅ Claude 4校正完了: 処理時間 {result.get('processing_time', 0):.2f}秒")
        
        # エラーがある場合の処理
        if 'error' in result:
            logger.error(f"❌ 校正エラー: {result['error']}")
            return JsonResponse({
                'success': False,
                'error': result['error'],
                'processing_time': result.get('processing_time', 0),
                'mode': result.get('mode', 'unknown')
            })
        
        # 成功時の処理
        corrected_text = result.get('corrected_text', text)
        corrections = result.get('corrections', [])
        processing_time = result.get('processing_time', 0)
        
        # 修正箇所のハイライト処理
        logger.info("🎨 修正箇所ハイライト処理開始")
        
        # JSONモードの場合、correctionsは既に適切な形式
        if use_json_mode:
            # JSON形式のcorrectionsをlegacy形式に変換
            formatted_corrections = []
            for corr in corrections:
                formatted_corrections.append({
                    "original": corr.get("original", ""),
                    "corrected": corr.get("corrected", ""),
                    "reason": corr.get("reason", ""),
                    "category": corr.get("category", "typo"),
                    "line_number": corr.get("line_number", 0)
                })
        else:
            formatted_corrections = corrections
        
        highlighted_text = format_corrections(text, formatted_corrections)
        logger.info("✅ ハイライト処理完了")
        
        total_time = time.time() - start_time
        logger.info(f"🏁 校正API処理完了: 総時間 {total_time:.2f}秒")
        
        return JsonResponse({
            'success': True,
            'corrected_text': highlighted_text,
            'corrections': formatted_corrections,
            'processing_time': processing_time,
            'total_time': total_time,
            'mode': result.get('mode', 'unknown'),
            'original_length': result.get('original_length', len(text)),
            'input_tokens': result.get('input_tokens', 0),
            'output_tokens': result.get('output_tokens', 0),
            'estimated_cost': result.get('estimated_cost', 0),
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析エラー: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'リクエストデータの解析に失敗しました: {str(e)}'
        })
        
    except Exception as e:
        total_time = time.time() - start_time
        error_message = str(e)
        error_type = type(e).__name__
        stack_trace = traceback.format_exc()
        
        logger.error(f"💥 校正処理中にエラー発生: {error_message}")
        logger.error(f"📋 エラー詳細:\n{stack_trace}")
        
        # Chatwork通知を送信
        try:
            chatwork_service = ChatworkNotificationService()
            
            # クライアント情報を取得
            def get_client_ip(request):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    return x_forwarded_for.split(',')[0]
                return request.META.get('REMOTE_ADDR', '不明')
            
            client_ip = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '不明')
            
            # エラー情報をまとめる
            error_context = {
                'error_type': error_type,
                'error_message': error_message,
                'function': 'proofread',
                'processing_time': total_time,
                'text_length': len(text) if 'text' in locals() else 0,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'stack_trace': stack_trace
            }
            
            if chatwork_service.is_configured():
                chatwork_service.send_error_notification(
                    error_type="PROOFREADING_VIEW_ERROR",
                    error_message=f"校正API処理中にエラーが発生: {error_message}",
                    context=error_context
                )
                logger.info("✅ Chatworkエラー通知送信完了")
            else:
                logger.warning("⚠️ Chatwork設定が不完全のため通知をスキップ")
            
        except Exception as notification_error:
            logger.error(f"❌ Chatworkエラー通知送信失敗: {str(notification_error)}")
        
        return JsonResponse({
            'success': False,
            'error': f'校正処理中にエラーが発生しました: {error_message}',
            'error_type': error_type,
            'processing_time': total_time
        })


@csrf_exempt
@require_http_methods(["POST"])
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
        protected_text, placeholders, html_tag_info = protect_html_tags_advanced(original_text)
        
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
        corrected_text, corrections, completion_time, cost_info = client.proofread_text(
            protected_text, replacement_dict, temperature, top_p
        )
        print('DEBUG 校正AI返り値:', corrected_text, corrections, completion_time, cost_info)
        
        # HTMLタグを復元
        corrected_text = restore_html_tags_advanced(corrected_text, placeholders, html_tag_info, corrections)
        
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
        
        # 結果をキャッシュに保存
        cache.set(f'proofread_result_{process_id}', {
            'original_text': original_text,
            'corrected_text': highlighted_html,
            'corrections': corrections,
            'model': client.model_id,
            'input_tokens': cost_info.get('input_tokens', 0),
            'output_tokens': cost_info.get('output_tokens', 0),
            'total_cost': cost_info.get('total_cost', 0),
            'completion_time': completion_time
        }, timeout=3600)  # 1時間キャッシュ
        
        # Claude 3.7のtool_uses, usage, modelも返す
        return {
            'original_text': original_text,
            'corrected_text': highlighted_html,
            'corrections': corrections,
            'model': client.model_id,
            'input_tokens': cost_info.get('input_tokens', 0),
            'output_tokens': cost_info.get('output_tokens', 0),
            'total_cost': cost_info.get('total_cost', 0),
            'completion_time': completion_time
        }
        
    except Exception as e:
        logger.error(f"非同期校正処理中にエラーが発生しました: {str(e)}")
        # エラー情報をキャッシュに保存
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


@csrf_exempt
@require_http_methods(["POST"])
def debug_aws_auth(request):
    """
    AWS認証情報の詳細チェック（デバッグ用）
    """
    logger.info("🔐 AWS認証情報デバッグチェック開始")
    
    try:
        debug_info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'aws_region': os.environ.get('AWS_REGION', 'ap-northeast-1'),
            'environment_variables': {}
        }
        
        # 環境変数チェック（機密情報は一部マスク）
        aws_env_vars = ['AWS_REGION', 'AWS_DEFAULT_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        for var in aws_env_vars:
            value = os.environ.get(var, None)
            if value:
                if 'KEY' in var or 'SECRET' in var:
                    debug_info['environment_variables'][var] = f"{value[:4]}***{value[-4:]}" if len(value) > 8 else "***"
                else:
                    debug_info['environment_variables'][var] = value
            else:
                debug_info['environment_variables'][var] = "未設定"
        
        # Boto3セッション情報
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials:
                debug_info['boto3_session'] = {
                    'access_key': f"{credentials.access_key[:4]}***{credentials.access_key[-4:]}" if credentials.access_key else "なし",
                    'has_secret_key': bool(credentials.secret_key),
                    'has_token': bool(credentials.token),
                    'region': session.region_name or "未設定"
                }
            else:
                debug_info['boto3_session'] = {'status': '認証情報なし'}
        except Exception as boto_error:
            debug_info['boto3_session'] = {'error': str(boto_error)}
        
        # Bedrock接続テスト
        try:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name=debug_info['aws_region'])
            # 簡単な接続テスト（リストモデルは重いので避ける）
            debug_info['bedrock_connection'] = {'status': 'クライアント作成成功'}
        except Exception as bedrock_error:
            debug_info['bedrock_connection'] = {'error': str(bedrock_error)}
        
        # STS（Security Token Service）でアイデンティティ確認
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            debug_info['sts_identity'] = {
                'account': identity.get('Account', '不明'),
                'user_id': identity.get('UserId', '不明'),
                'arn': identity.get('Arn', '不明')
            }
        except Exception as sts_error:
            debug_info['sts_identity'] = {'error': str(sts_error)}
        
        logger.info(f"✅ AWS認証デバッグ完了: {debug_info}")
        return JsonResponse({'success': True, 'debug_info': debug_info})
        
    except Exception as e:
        logger.error(f"❌ AWS認証デバッグエラー: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'stack_trace': traceback.format_exc()
        })


@require_http_methods(["GET"])
def debug_server_status(request):
    """
    サーバー状態の詳細チェック（デバッグ用）
    """
    logger.info("🖥️ サーバー状態デバッグチェック開始")
    
    try:
        import django
        import sys
        
        debug_info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'django_version': django.get_version(),
            'python_version': sys.version,
            'settings': {
                'debug': settings.DEBUG,
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'time_zone': settings.TIME_ZONE
            },
            'environment': {
                'python_path': sys.executable,
                'working_directory': os.getcwd(),
                'virtual_env': os.environ.get('VIRTUAL_ENV', '未設定')
            },
            'packages': {}
        }
        
        # 重要なパッケージのバージョンチェック
        try:
            import boto3
            debug_info['packages']['boto3'] = boto3.__version__
        except ImportError:
            debug_info['packages']['boto3'] = '未インストール'
        
        try:
            import requests
            debug_info['packages']['requests'] = requests.__version__
        except ImportError:
            debug_info['packages']['requests'] = '未インストール'
        
        # BedrockClientの初期化テスト
        try:
            bedrock_client = BedrockClient()
            debug_info['bedrock_client'] = {
                'initialization': '成功',
                'model_id': bedrock_client.model_id,
                'fallback_model_id': bedrock_client.fallback_model_id
            }
        except Exception as bc_error:
            debug_info['bedrock_client'] = {
                'initialization': '失敗',
                'error': str(bc_error)
            }
        
        logger.info(f"✅ サーバー状態デバッグ完了: {debug_info}")
        return JsonResponse({'success': True, 'debug_info': debug_info})
        
    except Exception as e:
        logger.error(f"❌ サーバー状態デバッグエラー: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'stack_trace': traceback.format_exc()
        })


def dictionary_viewer(request):
    """
    校正AIページからアクセス可能な辞書表示機能
    """
    try:
        # CSVファイルから辞書データを読み込み
        # プロジェクトルートからの絶対パスを使用
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(project_root, 'app', 'proofreading', 'replacement_dict.csv')
        dictionary_entries = []
        
        logger.info(f"📁 プロジェクトルート: {project_root}")
        logger.info(f"📂 辞書ファイルパス: {csv_path}")
        logger.info(f"🔍 ファイル存在確認: {os.path.exists(csv_path)}")
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row_num, row in enumerate(csv_reader, 1):
                    if len(row) >= 4:  # 最低4列必要（元の単語, 修正後, 状態, ID）
                        dictionary_entries.append({
                            'id': row_num,
                            'original_word': row[0],
                            'corrected_word': row[1], 
                            'state': row[2],  # '開く' or '閉じる'
                            'entry_id': row[3] if len(row) > 3 else row_num
                        })
                        
            logger.info(f"✅ 辞書読み込み成功: {len(dictionary_entries)}件")
        else:
            logger.error(f"❌ 辞書ファイルが見つかりません: {csv_path}")
        
        # 辞書データをカテゴリ別に分類
        open_entries = [entry for entry in dictionary_entries if entry['state'] == '開く']
        close_entries = [entry for entry in dictionary_entries if entry['state'] == '閉じる']
        
        # 統計情報
        stats = {
            'total_entries': len(dictionary_entries),
            'open_entries': len(open_entries),
            'close_entries': len(close_entries)
        }
        
        logger.info(f"📚 辞書表示: 総エントリ数 {stats['total_entries']}件")
        
        return render(request, 'proofreading_ai/dictionary_viewer.html', {
            'dictionary_entries': dictionary_entries,
            'open_entries': open_entries,
            'close_entries': close_entries,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ 辞書表示エラー: {str(e)}")
        return render(request, 'proofreading_ai/dictionary_viewer.html', {
            'dictionary_entries': [],
            'open_entries': [],
            'close_entries': [],
            'stats': {'total_entries': 0, 'open_entries': 0, 'close_entries': 0},
            'error': str(e)
        })


@csrf_exempt
def submit_feedback(request):
    """
    テスター向けフィードバック送信エンドポイント
    """
    logger.info(f"🔍 フィードバック送信開始 - Method: {request.method}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        # フォームデータの取得
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        feedback_type = request.POST.get('feedback_type', 'general')
        message = request.POST.get('message', '').strip()
        
        logger.info(f"📝 フォームデータ取得: name={name}, email={email}, type={feedback_type}, message_len={len(message)}")
        
        # バリデーション
        if not name or not message:
            logger.warning(f"❌ バリデーションエラー: name={bool(name)}, message={bool(message)}")
            return JsonResponse({
                'success': False, 
                'error': '名前とメッセージは必須です'
            })
        
        if len(message) < 10:
            logger.warning(f"❌ メッセージ長エラー: {len(message)}文字")
            return JsonResponse({
                'success': False,
                'error': 'メッセージは10文字以上で入力してください'
            })
        
        # チャットワーク通知送信
        try:
            logger.info("🤖 チャットワーク通知サービス初期化開始")
            chatwork_service = ChatworkNotificationService()
            
            is_configured = chatwork_service.is_configured()
            logger.info(f"⚙️ チャットワーク設定状況: {is_configured}")
            
            if is_configured:
                context = {
                    'name': name,
                    'email': email,
                    'feedback_type': feedback_type,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': request.META.get('REMOTE_ADDR', '')
                }
                
                logger.info(f"📤 フィードバック通知送信開始: {name}")
                success = chatwork_service.send_feedback_notification(
                    name=name,
                    feedback=message,
                    context=context
                )
                logger.info(f"📊 フィードバック通知送信結果: {success}")
                
                if success:
                    logger.info(f"✅ フィードバック通知送信成功: {name}")
                    return JsonResponse({
                        'success': True,
                        'message': 'フィードバックを送信しました。ありがとうございます！'
                    })
                else:
                    logger.error(f"❌ フィードバック通知送信失敗: {name}")
                    return JsonResponse({
                        'success': False,
                        'error': '送信に失敗しました。しばらく時間をおいて再度お試しください。'
                    })
            else:
                logger.warning("⚠️ チャットワーク設定が不完全なため、フィードバック送信をスキップ")
                return JsonResponse({
                    'success': False,
                    'error': 'フィードバック機能が一時的に利用できません。'
                })
                
        except Exception as notification_error:
            logger.error(f"❌ フィードバック通知エラー: {str(notification_error)}")
            logger.error(f"📋 スタックトレース: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': '送信処理でエラーが発生しました。'
            })
            
    except Exception as e:
        logger.error(f"❌ フィードバック処理エラー: {str(e)}")
        logger.error(f"📋 スタックトレース: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': 'システムエラーが発生しました。'
        })


def feedback_form(request):
    """
    フィードバックフォーム表示ページ
    """
    return render(request, 'proofreading_ai/feedback_form.html') 
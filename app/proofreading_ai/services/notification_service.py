import os
import requests
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class ChatworkNotificationService:
    """チャットワークへのエラー通知サービス"""
    
    def __init__(self):
        """
        チャットワーク通知サービスの初期化
        """
        self.api_token = getattr(settings, 'CHATWORK_API_TOKEN', os.environ.get('CHATWORK_API_TOKEN'))
        self.room_id = getattr(settings, 'CHATWORK_ROOM_ID', os.environ.get('CHATWORK_ROOM_ID'))
        self.api_url = "https://api.chatwork.com/v2"
        
        if not self.api_token or not self.room_id:
            logger.warning("⚠️ チャットワーク設定が不完全です（API_TOKEN or ROOM_ID missing）")
    
    def is_configured(self) -> bool:
        """
        チャットワーク設定が完了しているかチェック
        """
        return bool(self.api_token and self.room_id)
    
    def send_error_notification(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        エラー通知をチャットワークに送信
        
        Args:
            error_type: エラーの種類 (例: "BEDROCK_INIT_ERROR", "MODEL_INVOKE_ERROR")
            error_message: エラーメッセージ
            context: 追加のコンテキスト情報
            
        Returns:
            bool: 送信成功した場合True
        """
        if not self.is_configured():
            logger.warning("⚠️ チャットワーク設定が不完全なため、通知をスキップします")
            return False
        
        try:
            # エラーメッセージの構築
            message = self._build_error_message(error_type, error_message, context)
            
            # チャットワークAPIに送信
            return self._send_message(message, "error")
            
        except Exception as e:
            logger.error(f"❌ チャットワーク通知送信エラー: {str(e)}")
            return False
    
    def send_warning_notification(self, warning_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        警告通知をチャットワークに送信
        """
        if not self.is_configured():
            return False
        
        try:
            message = self._build_warning_message(warning_message, context)
            return self._send_message(message, "warning")
        except Exception as e:
            logger.error(f"❌ チャットワーク警告通知送信エラー: {str(e)}")
            return False
    
    def send_info_notification(self, info_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        情報通知をチャットワークに送信
        """
        if not self.is_configured():
            return False
            
        try:
            message = self._build_info_message(info_message, context)
            return self._send_message(message, "info")
        except Exception as e:
            logger.error(f"❌ チャットワーク情報通知送信エラー: {str(e)}")
            return False
    
    def _build_error_message(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        エラーメッセージを構築
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message_parts = [
            "[To:all]",
            "🚨 【エラー発生】校正AIシステム",
            "",
            f"⏰ 発生時刻: {timestamp}",
            f"🔴 エラー種別: {error_type}",
            f"📝 メッセージ: {error_message}",
        ]
        
        if context:
            message_parts.append("")
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                if key.lower() in ['user_id', 'request_id', 'model_id', 'function_name']:
                    message_parts.append(f"   - {key}: {value}")
        
        message_parts.extend([
            "",
            "👨‍💻 対応が必要な場合は開発チームまでお知らせください。",
            f"🔗 ログ確認: AWS CloudWatch > django-ecs-app"
        ])
        
        return "\n".join(message_parts)
    
    def _build_warning_message(self, warning_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        警告メッセージを構築
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message_parts = [
            "⚠️ 【警告】校正AIシステム",
            "",
            f"⏰ 発生時刻: {timestamp}",
            f"📝 メッセージ: {warning_message}",
        ]
        
        if context:
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                message_parts.append(f"   - {key}: {value}")
        
        return "\n".join(message_parts)
    
    def _build_info_message(self, info_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        情報メッセージを構築
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message_parts = [
            "ℹ️ 【情報】校正AIシステム",
            "",
            f"⏰ 時刻: {timestamp}",
            f"📝 メッセージ: {info_message}",
        ]
        
        if context:
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                message_parts.append(f"   - {key}: {value}")
        
        return "\n".join(message_parts)
    
    def _send_message(self, message: str, priority: str = "info") -> bool:
        """
        チャットワークAPIにメッセージを送信
        
        Args:
            message: 送信するメッセージ
            priority: 優先度 (error, warning, info)
            
        Returns:
            bool: 送信成功した場合True
        """
        try:
            url = f"{self.api_url}/rooms/{self.room_id}/messages"
            headers = {
                "X-ChatWorkToken": self.api_token,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "body": message
            }
            
            logger.info(f"📤 チャットワーク通知送信開始 (優先度: {priority})")
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ チャットワーク通知送信成功 (priority: {priority})")
                return True
            else:
                logger.error(f"❌ チャットワーク通知送信失敗: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ チャットワーク通知送信タイムアウト")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ チャットワーク通知送信リクエストエラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ チャットワーク通知送信予期しないエラー: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        チャットワーク接続テスト
        """
        if not self.is_configured():
            logger.error("❌ チャットワーク設定が不完全です")
            return False
        
        try:
            test_message = f"🧪 【接続テスト】校正AIシステム\n\n⏰ テスト時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ チャットワーク通知機能が正常に動作しています。"
            
            return self._send_message(test_message, "info")
        except Exception as e:
            logger.error(f"❌ チャットワーク接続テストエラー: {str(e)}")
            return False


# シングルトンインスタンス（グローバルで使用）
chatwork_service = ChatworkNotificationService() 
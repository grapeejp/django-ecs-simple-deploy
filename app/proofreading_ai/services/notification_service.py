import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.conf import settings
import traceback

logger = logging.getLogger(__name__)

class ChatworkNotificationService:
    """チャットワークへのエラー通知サービス（改良版）"""
    
    def __init__(self):
        """
        チャットワーク通知サービスの初期化
        """
        self.api_token = getattr(settings, 'CHATWORK_API_TOKEN', os.environ.get('CHATWORK_API_TOKEN'))
        self.room_id = getattr(settings, 'CHATWORK_ROOM_ID', os.environ.get('CHATWORK_ROOM_ID'))
        self.api_url = "https://api.chatwork.com/v2"
        
        # 自分のアカウント情報（個人宛メンション用）
        # TODO: find_my_chatwork_id.pyの実行結果で正確な値に更新する必要がある場合があります
        self.my_account_id = "9575983"  # 柳本 安利さんの正しいアカウントID
        self.my_chatwork_id = "yasutoshi-yanagimoto"  # 開発エンジニアの正しいChatwork ID
        self.personal_room_id = "21235770"  # 個人ルームID（要確認）
        
        # 個人宛メンション設定（環境変数で制御可能）
        self.use_personal_mention = os.environ.get('CHATWORK_USE_PERSONAL_MENTION', 'true').lower() == 'true'
        
        if not self.api_token or not self.room_id:
            logger.warning("⚠️ チャットワーク設定が不完全です（API_TOKEN or ROOM_ID missing）")
    
    def _get_japan_time(self) -> str:
        """
        日本時間を取得（JST +9時間）
        """
        # UTC時間に9時間を追加してJSTにする
        japan_time = datetime.utcnow() + timedelta(hours=9)
        return japan_time.strftime("%Y年%m月%d日 %H時%M分")
    
    def _get_mention_prefix(self) -> str:
        """
        メンション用プレフィックスを取得
        
        Returns:
            str: 個人宛メンション有効時は "[To:account_id] 名前さん\n"、無効時は "[To:all]\n"
        """
        if self.use_personal_mention:
            return f"[To:{self.my_account_id}] 柳本さん\n"
        else:
            return "[To:all]\n"
    
    def is_configured(self) -> bool:
        """
        チャットワーク設定が完了しているかチェック
        """
        return bool(self.api_token and self.room_id)
    
    def send_error_notification(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        エラー通知をチャットワークに送信（改良版）
        
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
            success = self._send_message(message, "error")
            
            if success:
                logger.info(f"✅ チャットワークエラー通知送信成功: {error_type}")
            else:
                logger.error(f"❌ チャットワークエラー通知送信失敗: {error_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ チャットワーク通知送信エラー: {str(e)}")
            logger.error(f"📋 詳細トレース: {traceback.format_exc()}")
            return False
    
    def send_warning_notification(self, warning_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        警告通知をチャットワークに送信（改良版）
        """
        if not self.is_configured():
            return False
        
        try:
            message = self._build_warning_message(warning_message, context)
            success = self._send_message(message, "warning")
            
            if success:
                logger.info(f"✅ チャットワーク警告通知送信成功")
            else:
                logger.error(f"❌ チャットワーク警告通知送信失敗")
            
            return success
        except Exception as e:
            logger.error(f"❌ チャットワーク警告通知送信エラー: {str(e)}")
            logger.error(f"📋 詳細トレース: {traceback.format_exc()}")
            return False
    
    def send_info_notification(self, info_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        情報通知をチャットワークに送信（改良版）
        """
        if not self.is_configured():
            return False
            
        try:
            message = self._build_info_message(info_message, context)
            success = self._send_message(message, "info")
            
            if success:
                logger.info(f"✅ チャットワーク情報通知送信成功")
            else:
                logger.error(f"❌ チャットワーク情報通知送信失敗")
            
            return success
        except Exception as e:
            logger.error(f"❌ チャットワーク情報通知送信エラー: {str(e)}")
            logger.error(f"📋 詳細トレース: {traceback.format_exc()}")
            return False
    
    def send_feedback_notification(self, name: str, feedback: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        フィードバック通知をチャットワークに送信（新機能）
        
        Args:
            name: 送信者名
            feedback: フィードバック内容
            context: 追加情報（post_id, user_id等）
            
        Returns:
            bool: 送信成功した場合True
        """
        if not self.is_configured():
            return False
        
        try:
            message = self._build_feedback_message(name, feedback, context)
            success = self._send_message(message, "feedback")
            
            if success:
                logger.info(f"✅ チャットワークフィードバック通知送信成功: {name}")
            else:
                logger.error(f"❌ チャットワークフィードバック通知送信失敗: {name}")
            
            return success
        except Exception as e:
            logger.error(f"❌ チャットワークフィードバック通知送信エラー: {str(e)}")
            logger.error(f"📋 詳細トレース: {traceback.format_exc()}")
            return False
    
    def _build_error_message(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        エラーメッセージを構築（日本時間対応・個人宛メンション対応）
        """
        japan_time = self._get_japan_time()
        mention_prefix = self._get_mention_prefix()
        
        message_parts = [
            mention_prefix + "🚨 【エラー発生】校正AIシステム",
            "",
            f"⏰ 発生時刻: {japan_time}",
            f"🔴 エラー種別: {error_type}",
            f"📝 メッセージ: {error_message}",
        ]
        
        if context:
            message_parts.append("")
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                if key.lower() in ['user_id', 'request_id', 'model_id', 'function_name', 'post_id']:
                    message_parts.append(f"   - {key}: {value}")
        
        message_parts.extend([
            "",
            "👨‍💻 対応が必要な場合は開発チームまでお知らせください。",
            f"🔗 ログ確認: AWS CloudWatch > django-ecs-app"
        ])
        
        return "\n".join(message_parts)
    
    def _build_warning_message(self, warning_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        警告メッセージを構築（日本時間対応・個人宛メンション対応）
        """
        japan_time = self._get_japan_time()
        mention_prefix = self._get_mention_prefix()
        
        message_parts = [
            mention_prefix + "⚠️ 【警告】校正AIシステム",
            "",
            f"⏰ 発生時刻: {japan_time}",
            f"📝 メッセージ: {warning_message}",
        ]
        
        if context:
            message_parts.append("")
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                message_parts.append(f"   - {key}: {value}")
        
        return "\n".join(message_parts)
    
    def _build_info_message(self, info_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        情報メッセージを構築（日本時間対応・個人宛メンション対応）
        """
        japan_time = self._get_japan_time()
        mention_prefix = self._get_mention_prefix()
        
        message_parts = [
            mention_prefix + "ℹ️ 【情報】校正AIシステム",
            "",
            f"⏰ 発生時刻: {japan_time}",
            f"📝 メッセージ: {info_message}",
        ]
        
        if context:
            message_parts.append("")
            message_parts.append("📊 詳細情報:")
            for key, value in context.items():
                message_parts.append(f"   - {key}: {value}")
        
        return "\n".join(message_parts)
    
    def _build_feedback_message(self, name: str, feedback: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        フィードバックメッセージを構築（日本時間対応・個人宛メンション対応）
        """
        japan_time = self._get_japan_time()
        mention_prefix = self._get_mention_prefix()
        
        # カテゴリーのアイコンマッピング
        category_icons = {
            'bug': '🐛 バグ報告',
            'improvement': '💡 機能改善提案',
            'feature': '✨ 新機能要望',
            'ui': '🎨 UI/UX改善',
            'performance': '⚡ パフォーマンス',
            'general': '💬 その他・一般的な意見'
        }
        
        feedback_type = context.get('feedback_type', 'general') if context else 'general'
        category_display = category_icons.get(feedback_type, '💬 その他')
        
        message_parts = [
            mention_prefix + "📝 【ユーザーフィードバック】校正AIシステム",
            "",
            f"⏰ 受信時刻: {japan_time}",
            f"👤 送信者: {name}",
            f"📂 カテゴリー: {category_display}",
        ]
        
        # メールアドレスがある場合は追加
        if context and context.get('email'):
            message_parts.append(f"📧 メール: {context['email']}")
        
        message_parts.extend([
            "",
            f"💬 フィードバック内容:",
            f"「{feedback}」",
        ])
        
        if context:
            message_parts.append("")
            message_parts.append("📊 技術情報:")
            for key, value in context.items():
                if key in ['timestamp', 'user_agent', 'ip_address']:
                    if key == 'user_agent':
                        # User Agentは短縮表示
                        short_ua = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        message_parts.append(f"   - ブラウザ: {short_ua}")
                    elif key == 'ip_address':
                        message_parts.append(f"   - IPアドレス: {value}")
                    elif key == 'timestamp':
                        message_parts.append(f"   - タイムスタンプ: {value}")
        
        message_parts.extend([
            "",
            "🔧 対応方針:",
            "- 内容を確認して改善検討を行います",
            "- 必要に応じて開発チームで議論します",
            "- 重要な要望は次回アップデートで対応予定",
            "",
            "🙏 貴重なフィードバックをありがとうございます！"
        ])
        
        return "\n".join(message_parts)
    
    def _send_message(self, message: str, priority: str = "info") -> bool:
        """
        チャットワークAPIにメッセージを送信（ローカルでもAPIトークン・ルームIDが空でなければ必ず送信）
        """
        # APIトークン・ルームIDが空の場合のみローカルモード
        if not self.api_token or not self.room_id:
            print("【ローカルモード】Chatwork通知内容（APIトークンまたはルームIDが未設定のため送信スキップ）")
            print(f"API_TOKEN={self.api_token}, ROOM_ID={self.room_id}")
            print("-----")
            print(message)
            print("-----")
            logger.warning("⚠️ Chatwork設定が未設定のため、通知をスキップ（ローカルデバッグ用print出力）")
            return False  # 送信失敗

        try:
            url = f"{self.api_url}/rooms/{self.room_id}/messages"
            headers = {
                "X-ChatWorkToken": self.api_token,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"body": message}

            print(f"【Chatwork送信リクエスト】url={url}")
            print(f"headers={headers}")
            print(f"data={data}")

            import requests
            response = requests.post(url, headers=headers, data=data, timeout=10)
            print(f"【Chatworkレスポンス】status={response.status_code}")
            print(f"body={response.text}")
            logger.info(f"Chatwork送信レスポンス: {response.status_code} {response.text}")

            if response.status_code == 200:
                return True
            else:
                logger.error(f"❌ Chatwork通知送信失敗: {response.status_code} {response.text}")
                return False
        except Exception as e:
            print(f"❌ Chatwork通知送信例外: {str(e)}")
            import traceback
            print(traceback.format_exc())
            logger.error(f"❌ Chatwork通知送信例外: {str(e)}\n{traceback.format_exc()}")
            return False
    
    def test_connection(self) -> bool:
        """
        チャットワーク接続テスト（改良版）
        """
        if not self.is_configured():
            logger.error("❌ チャットワーク設定が不完全です")
            return False
        
        try:
            japan_time = self._get_japan_time()
            test_message = f"🧪 【接続テスト】校正AIシステム\n\n⏰ テスト時刻: {japan_time}\n✅ チャットワーク通知機能が正常に動作しています。"
            
            success = self._send_message(test_message, "test")
            
            if success:
                logger.info("✅ チャットワーク接続テスト成功")
            else:
                logger.error("❌ チャットワーク接続テスト失敗")
            
            return success
        except Exception as e:
            logger.error(f"❌ チャットワーク接続テストエラー: {str(e)}")
            logger.error(f"📋 詳細トレース: {traceback.format_exc()}")
            return False


# シングルトンインスタンス（グローバルで使用）
chatwork_service = ChatworkNotificationService() 
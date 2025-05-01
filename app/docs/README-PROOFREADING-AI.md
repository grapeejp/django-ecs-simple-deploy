# 校正AI機能 引継ぎ仕様書

## 1. 概要

AI文章校正システムは、AWS Bedrock上のClaude 3.7 Sonnetモデルを活用して、日本語文章の校正とタグ推薦を行うDjangoベースのシステムです。本書では、校正AI機能を別アプリに移植するために必要な情報をまとめています。

## 2. システムアーキテクチャ

### 2.1 全体構成

システムは以下のようなフローで動作します：

1. ユーザーが文章校正をリクエスト
2. Djangoアプリが非同期タスクをCeleryに登録
3. CeleryワーカーがAWS Bedrockに推論リクエスト送信
4. AWS BedrockがClaude AIモデルにプロンプト送信
5. Claude AIモデルが校正結果を返却
6. 結果がデータベースに保存され、ユーザーに表示

### 2.2 主要コンポーネント

- **Djangoアプリケーション**: MVTパターンとサービスレイヤーを組み合わせた設計
- **Celeryワーカー**: 非同期処理を担当
- **AWS Bedrock**: Claude AIモデルへのアクセスを提供
- **PostgreSQL**: 校正履歴などのデータ保存
- **Redis**: Celeryのメッセージブローカーとキャッシュストア

## 3. 校正AI機能の実装詳細

### 3.1 AWS Bedrock連携

```python
# core/services/bedrock_client.py
import boto3
import json
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class BedrockClient:
    """AWS Bedrockクライアント"""
    
    def __init__(self):
        """クライアントの初期化"""
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_DEFAULT_REGION,
        )
        # Claude 3.5 Sonnetモデル
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    
    def invoke_model(self, prompt, max_tokens=4000, temperature=0.7):
        """AIモデルを呼び出す"""
        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['content'][0]['text']
            
        except ClientError as e:
            logger.error(f"AWS Bedrock APIエラー: {str(e)}")
            raise
```

### 3.2 プロンプト設計

#### 校正用プロンプト

```python
# corrections/services/prompt_service.py
class CorrectionPromptService:
    """校正用プロンプト生成サービス"""
    
    @staticmethod
    def generate_correction_prompt(text, correction_rules=None):
        """校正用のプロンプトを生成する"""
        base_prompt = """あなたは校正のエキスパートです。以下の文章を校正してください。

校正のルール:
1. 文法的な誤りを修正
2. 言葉の統一性を確保
3. 冗長な表現を簡潔に
4. 専門用語の適切な使用を確認

以下の形式でJSON形式で結果を返してください:
{
    "corrected_text": "校正後の文章全体",
    "corrections": [
        {
            "original": "元の表現",
            "corrected": "校正後の表現",
            "reason": "修正理由",
            "position": 文中での位置（文字インデックス）
        },
        ...
    ]
}

校正が必要ない場合は、"corrections"を空の配列にしてください。

校正対象の文章:
"""

        # 特定の校正ルールがある場合は追加
        if correction_rules:
            rules_text = "\n追加の校正ルール:\n"
            for rule in correction_rules:
                rules_text += f"- {rule}\n"
            base_prompt += rules_text
        
        # 校正対象テキストを追加
        full_prompt = f"{base_prompt}\n{text}"
        
        return full_prompt
```

### 3.3 Celeryタスク

```python
# corrections/tasks.py
from celery import shared_task
from .services import CorrectionService, CorrectionPromptService
from core.services.bedrock_client import BedrockClient
import json
import logging
import time

logger = logging.getLogger(__name__)

@shared_task
def process_correction_task(correction_id):
    """校正処理タスク"""
    try:
        # 校正情報の取得
        correction = CorrectionService.get_correction_by_id(correction_id)
        
        if not correction or correction.status != 'pending':
            logger.warning(f"校正ID {correction_id} は処理できません: 存在しないか処理中でない")
            return
        
        # 処理中ステータスに更新
        CorrectionService.update_correction_status(correction_id, 'processing')
        
        # AWS Bedrockクライアント準備
        bedrock_client = BedrockClient()
        
        # プロンプト生成
        prompt = CorrectionPromptService.generate_correction_prompt(correction.original_text)
        
        # AIモデル呼び出し
        start_time = time.time()
        response = bedrock_client.invoke_model(prompt)
        processing_time = time.time() - start_time
        
        # レスポース解析
        try:
            result = json.loads(response)
            
            # 校正結果を保存
            CorrectionService.save_correction_result(
                correction_id=correction_id,
                corrected_text=result.get('corrected_text', correction.original_text),
                corrections=result.get('corrections', []),
                processing_time=processing_time
            )
            
            # 処理完了に更新
            CorrectionService.update_correction_status(correction_id, 'completed')
            
        except json.JSONDecodeError:
            logger.error(f"JSON解析エラー: {response[:500]}...")
            CorrectionService.update_correction_status(correction_id, 'failed')
            
    except Exception as e:
        logger.error(f"校正処理エラー: {str(e)}")
        CorrectionService.update_correction_status(correction_id, 'failed')
```

## 4. データモデル

### 4.1 Correctionモデル

```python
class Correction(models.Model):
    """文章校正モデル"""
    # 校正ステータスの選択肢
    STATUS_CHOICES = (
        ('pending', '処理中'),
        ('completed', '完了'),
        ('failed', '失敗')
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="corrections", verbose_name="ユーザー")
    original_text = models.TextField("元のテキスト")
    corrected_text = models.TextField("校正後のテキスト", blank=True)
    status = models.CharField("ステータス", max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_model = models.CharField("使用AIモデル", max_length=50, default="claude-3-5-sonnet")
    processing_time = models.FloatField("処理時間(秒)", null=True, blank=True)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)
```

### 4.2 CorrectionDetailモデル

```python
class CorrectionDetail(models.Model):
    """校正詳細モデル"""
    correction = models.ForeignKey(Correction, on_delete=models.CASCADE, related_name="details", verbose_name="校正")
    original_phrase = models.CharField("元のフレーズ", max_length=255)
    corrected_phrase = models.CharField("校正後のフレーズ", max_length=255)
    reason = models.TextField("校正理由")
    position = models.IntegerField("位置", help_text="元テキスト内での位置（文字インデックス）")
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
```

## 5. API仕様

### 5.1 校正リクエストAPI

**エンドポイント**: `/api/v1/corrections/`  
**メソッド**: POST  

#### リクエスト例

```json
{
  "text": "これは校正対象の文章です。誤字や表現の乱れがあるかもしれません。",
  "title": "サンプル文章",
  "creator_name": "山田太郎",
  "creator_department": "マーケティング部",
  "correction_level": "standard"
}
```

#### レスポンス例

```json
{
  "id": "12345abc-67de-89fa-bcde-123456789012",
  "status": "pending",
  "created_at": "2023-05-01T12:34:56.789Z",
  "estimated_completion_time": "2023-05-01T12:35:56.789Z"
}
```

### 5.2 校正結果取得API

**エンドポイント**: `/api/v1/corrections/{id}/`  
**メソッド**: GET  

#### レスポンス例

```json
{
  "id": "12345abc-67de-89fa-bcde-123456789012",
  "title": "サンプル文章",
  "creator_name": "山田太郎",
  "creator_department": "マーケティング部",
  "status": "completed",
  "created_at": "2023-05-01T12:34:56.789Z",
  "completed_at": "2023-05-01T12:36:12.345Z",
  "original_text": "これは校正対象の文章です。誤字や表現の乱れがあるかもしれません。",
  "corrected_text": "これは校正対象の文章です。誤字や表現の乱れがあるかもしれません。",
  "corrections": [
    {
      "original": "乱れ",
      "corrected": "ゆらぎ",
      "reason": "より適切な表現への修正提案",
      "position": 16
    }
  ],
  "processing_time": 75.6
}
```

## 6. プロンプトエンジニアリング手法

### 6.1 主要テクニック

- **ステップバイステップの指示**: 複雑なタスクを小さなステップに分解
- **Few-shotプロンプティング**: 具体例を示して期待する出力パターンを学習させる
- **チェーン・オブ・ソート**: 思考プロセスを明示的に示す
- **出力形式の明確化**: JSON等の構造化された出力形式を指定

### 6.2 カスタム校正ルールの適用

```python
# カスタム校正ルールの例
custom_rules = [
    "「〜ですが」は「〜ですが、」と書き、カンマを必ず入れる",
    "「及び」ではなく「および」を使用する",
    "数字は半角で表記し、千の位ごとにカンマを入れる（例: 1,000）",
    "英字の略語は全て大文字で表記する（例: AI, API, IoT）",
]
```

## 7. 移植手順

1. AWS Bedrockアクセス権限を設定
2. データモデルを新環境に移植
3. ベースとなるDjango+Celery+Redisインフラを構築
4. BedrockClientとプロンプトサービスを実装
5. Celeryタスクと関連サービスを実装
6. REST APIエンドポイントを作成
7. 単体テストと統合テストを実施

## 8. 注意事項

- AWS Bedrockのリージョン設定とAPIキーの管理に注意
- 処理中のステータス管理と例外処理を適切に実装
- 長文処理時のタイムアウト対策を考慮すること
- セキュリティ面でのAPI認証とIPアドレス制限を設定

## 9. 依存関係

```
boto3>=1.26.0
Django>=4.2.0
celery>=5.3.0
redis>=4.5.0
psycopg2-binary>=2.9.5
```

以上の内容が、校正AI機能を別アプリに移植するための基本情報です。実装や詳細についてはソースコードと合わせて確認してください。 
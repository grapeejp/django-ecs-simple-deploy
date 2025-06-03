# 📢 チャットワークエラー報告機能セットアップガイド

## 📋 概要

校正AIシステムでエラーが発生した際に、自動的にチャットワークに通知を送信する機能です。

## 🎯 機能

- ✅ **BedrockClient初期化エラー**: AWS Bedrock接続失敗時の通知
- ✅ **モデル呼び出しエラー**: Claude API実行時エラーの詳細通知
- ✅ **エラー種別の分類**: アクセス拒否、バリデーション、スロットリング等
- ✅ **安全な認証情報管理**: AWS Secrets Managerによる暗号化保存
- ✅ **環境別設定**: staging/production環境の個別管理

## 🛠️ セットアップ手順

### 1. チャットワークAPIの準備

#### APIトークンの取得
1. [チャットワーク API管理画面](https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php)にアクセス
2. 「新しいAPIトークンを発行」をクリック
3. APIトークンをコピーして保存

#### ルームIDの確認
1. 通知を送信したいチャットワークのルームを開く
2. URLから`rid=` の後の数値を確認
   ```
   例: https://www.chatwork.com/#!rid123456789
   → Room ID: 123456789
   ```

### 2. AWS Secrets Managerでの設定

#### 自動セットアップ（推奨）
```bash
# 本番環境
./scripts/setup_chatwork_secrets.sh production

# ステージング環境
./scripts/setup_chatwork_secrets.sh staging

# コマンドライン引数での指定も可能
./scripts/setup_chatwork_secrets.sh production your-api-token your-room-id
```

#### 手動セットアップ
```bash
# 1. Secrets Managerにシークレット作成
aws secretsmanager create-secret \
    --name "django-ecs-chatwork-production" \
    --description "Chatwork API credentials for Django ECS application" \
    --secret-string '{
        "CHATWORK_API_TOKEN": "your-api-token-here",
        "CHATWORK_ROOM_ID": "your-room-id-here"
    }'

# 2. CloudFormationスタック更新
aws cloudformation deploy \
    --template-file cloudformation/ecs-cluster.yml \
    --stack-name django-ecs-cluster-production \
    --parameter-overrides \
        Environment=production \
        ChatworkApiToken=your-api-token-here \
        ChatworkRoomId=your-room-id-here \
    --capabilities CAPABILITY_IAM
```

### 3. ECSサービスの更新

チャットワーク環境変数を含む新しいタスク定義でECSサービスを更新：

```bash
# 本番環境
aws cloudformation deploy \
    --template-file cloudformation/ecs-service.yml \
    --stack-name django-ecs-service-production \
    --parameter-overrides Environment=production

# サービス再デプロイ（環境変数の更新を反映）
aws ecs update-service \
    --cluster django-ecs-cluster-production \
    --service django-ecs-service-production \
    --force-new-deployment
```

## 🧪 テスト方法

### ローカル環境でのテスト

1. **環境変数の設定**
   ```bash
   export CHATWORK_API_TOKEN="your-api-token"
   export CHATWORK_ROOM_ID="your-room-id"
   ```

2. **テストスクリプト実行**
   ```bash
   python test_chatwork_notification.py
   ```

3. **期待される結果**
   ```
   🧪 チャットワーク通知機能テスト開始
   ✅ チャットワーク通知機能が正常に動作しています
   ✅ エラー通知テスト成功
   ✅ 警告通知テスト成功
   🎉 すべてのテストが成功しました！
   ```

### 本番環境での確認

1. **ECSタスクログの確認**
   ```bash
   aws logs filter-log-events \
       --log-group-name "/ecs/django-app-production" \
       --filter-pattern "チャットワーク" \
       --start-time $(date -d '1 hour ago' +%s)000
   ```

2. **実際のエラー発生時の動作確認**
   - Bedrock権限エラーや一時的な接続エラーが発生した際
   - チャットワークに自動通知が送信されることを確認

## 🔧 設定の確認・変更

### Secrets Managerの確認
```bash
# シークレットの存在確認
aws secretsmanager describe-secret \
    --secret-id "django-ecs-chatwork-production"

# シークレットの値確認（API Token: マスク済み）
aws secretsmanager get-secret-value \
    --secret-id "django-ecs-chatwork-production" \
    --query 'SecretString' --output text | jq
```

### 設定の更新
```bash
# API Tokenの更新
aws secretsmanager update-secret \
    --secret-id "django-ecs-chatwork-production" \
    --secret-string '{
        "CHATWORK_API_TOKEN": "new-api-token",
        "CHATWORK_ROOM_ID": "same-room-id"
    }'

# ECSサービス再デプロイ（変更を反映）
aws ecs update-service \
    --cluster django-ecs-cluster-production \
    --service django-ecs-service-production \
    --force-new-deployment
```

## 📊 通知メッセージの例

### エラー通知
```
[To:all]
🚨 【エラー発生】校正AIシステム

⏰ 発生時刻: 2025-05-30 18:30:45
🔴 エラー種別: MODEL_ACCESS_DENIED
📝 メッセージ: モデルアクセス拒否: arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/apac.anthropic.claude-sonnet-4

📊 詳細情報:
   - function_name: _invoke_model_with_profile
   - model_id: arn:aws:bedrock:ap-northeast-1:026090540679:inference-profile/apac.anthropic.claude-sonnet-4

👨‍💻 対応が必要な場合は開発チームまでお知らせください。
🔗 ログ確認: AWS CloudWatch > django-ecs-app
```

### 警告通知
```
⚠️ 【警告】校正AIシステム

⏰ 発生時刻: 2025-05-30 18:25:30
📝 メッセージ: プロンプトファイルが見つかりません

📊 詳細情報:
   - file_path: /app/proofreading_ai/prompt.md
```

## 🔒 セキュリティ

- ✅ **APIトークンの暗号化**: AWS Secrets Managerで保存
- ✅ **IAM権限の最小化**: Secrets Manager読み取り権限のみ
- ✅ **ネットワーク隔離**: VPC内での通信
- ✅ **ログ保護**: APIトークンはログに出力されない

## 🚨 トラブルシューティング

### よくある問題

1. **「チャットワーク設定が不完全です」のエラー**
   - Secrets Managerの設定を確認
   - ECSタスクが新しいタスク定義を使用しているか確認

2. **「チャットワーク通知送信エラー」**
   - APIトークンの有効性を確認
   - ルームIDの正確性を確認
   - ネットワーク接続を確認

3. **通知が送信されない**
   - IAMロールにSecrets Manager権限があるか確認
   - CloudWatch Logsでエラーログを確認

### デバッグコマンド
```bash
# ECSタスクの環境変数確認
aws ecs describe-task-definition \
    --task-definition django-app \
    --query 'taskDefinition.containerDefinitions[0].secrets'

# 最新のECSタスクログ確認
aws logs filter-log-events \
    --log-group-name "/ecs/django-app-production" \
    --filter-pattern "チャットワーク"
```

## 📚 関連ファイル

- `app/proofreading_ai/services/notification_service.py` - 通知サービス実装
- `app/proofreading_ai/services/bedrock_client.py` - BedrockClient統合
- `cloudformation/ecs-cluster.yml` - Secrets Manager設定
- `cloudformation/ecs-service.yml` - ECSタスク定義
- `scripts/setup_chatwork_secrets.sh` - セットアップスクリプト
- `test_chatwork_notification.py` - テストスクリプト 
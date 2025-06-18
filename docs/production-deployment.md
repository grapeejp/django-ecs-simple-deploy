# 本番環境デプロイガイド

## 概要
本ドキュメントは、Django ECS Simple Deployプロジェクトの本番環境へのデプロイ手順を説明します。

## 前提条件

### 必要な権限
- AWS CLI設定済み
- ECR、ECS、CloudFormation、IAM、ACM、Route53の権限
- Docker実行環境

### SSL証明書
- ワイルドカード証明書（*.grape-app.jp）が設定済み
- 証明書ARN: `arn:aws:acm:ap-northeast-1:026090540679:certificate/97f351e3-23b6-42c6-8076-78f71b3d2c95`

## デプロイ手順

### 1. 事前確認
```bash
# 現在のブランチ確認
git branch --show-current

# 最新のコードを取得
git pull origin main

# AWS認証情報確認
aws sts get-caller-identity
```

### 2. 本番環境デプロイ実行
```bash
# デプロイスクリプト実行
./scripts/deploy-production.sh
```

### 3. デプロイフロー
1. **確認プロンプト**: 本番環境デプロイの確認
2. **ブランチ確認**: mainブランチ以外の場合は再確認
3. **Dockerビルド**: プラットフォーム指定でビルド
4. **ECRプッシュ**: タイムスタンプ付きタグでプッシュ
5. **CloudFormation**: クラスター → サービスの順でデプロイ
6. **ヘルスチェック**: 自動的にヘルスチェック実行

## アーキテクチャ

### インフラ構成
```
Internet → CloudFront → ALB → ECS Fargate → RDS
                      ↓
                   Route53 DNS
```

### スタック構成
- **クラスタースタック**: `django-ecs-cluster-production`
  - VPC、サブネット、セキュリティグループ
  - ALB、ターゲットグループ
  - ECSクラスター
  - IAMロール

- **サービススタック**: `django-ecs-service-production`
  - ECSタスク定義
  - ECSサービス

### ドメイン設定
| ドメイン | 用途 | 証明書 |
|----------|------|--------|
| `grape-app.jp` | メインドメイン | ワイルドカード |
| `www.grape-app.jp` | WWWリダイレクト | ワイルドカード |
| `prod.grape-app.jp` | 本番環境識別用 | ワイルドカード |

## 環境変数

### 本番環境固有設定
```yaml
ALLOWED_HOSTS: 'prod.grape-app.jp,grape-app.jp,www.grape-app.jp'
DEBUG: "False"
HTTPS_ENABLED: "True"
AWS_REGION: ap-northeast-1
```

### 機密情報（手動設定が必要）
- `SECRET_KEY`: Django秘密鍵
- `CHATWORK_API_TOKEN`: ChatWork API トークン
- `CHATWORK_ROOM_ID`: ChatWork ルームID
- `GOOGLE_OAUTH_CLIENT_ID`: Google OAuth クライアントID
- `GOOGLE_OAUTH_CLIENT_SECRET`: Google OAuth クライアントシークレット

## 監視とログ

### CloudWatch Logs
- ロググループ: `/ecs/django-app-production`
- 保持期間: 30日

### ヘルスチェック
- パス: `/health/`
- 間隔: 120秒
- タイムアウト: 60秒

### メトリクス監視
- ECSサービス: CPU、メモリ使用率
- ALB: リクエスト数、レスポンス時間
- RDS: 接続数、CPU使用率

## トラブルシューティング

### よくある問題

#### 1. デプロイ失敗
```bash
# スタック状態確認
aws cloudformation describe-stacks --stack-name django-ecs-cluster-production
aws cloudformation describe-stacks --stack-name django-ecs-service-production

# イベント確認
aws cloudformation describe-stack-events --stack-name django-ecs-service-production
```

#### 2. ECSタスク起動失敗
```bash
# サービス状態確認
aws ecs describe-services --cluster production-cluster --services django-ecs-service-production

# タスク確認
aws ecs list-tasks --cluster production-cluster --service-name django-ecs-service-production

# ログ確認
aws logs get-log-events --log-group-name "/ecs/django-app-production" --log-stream-name "最新のストリーム名"
```

#### 3. ヘルスチェック失敗
```bash
# ターゲットグループ確認
aws elbv2 describe-target-health --target-group-arn "ターゲットグループARN"

# 直接ヘルスチェック
curl -I https://prod.grape-app.jp/health/
```

### ロールバック手順
```bash
# 前のタスク定義に戻す
aws ecs update-service \
    --cluster production-cluster \
    --service django-ecs-service-production \
    --task-definition django-app-production:前のリビジョン番号
```

## セキュリティ

### IAMロール
- **TaskExecutionRole**: コンテナ起動用の最小権限
- **TaskRole**: アプリケーション実行用（Bedrock、CloudWatch Logs）

### ネットワークセキュリティ
- プライベートサブネットでECS実行
- ALBからのトラフィックのみ許可
- HTTPS強制リダイレクト

### 機密情報管理
- AWS Secrets Managerの使用推奨
- 環境変数での平文保存は避ける

## 運用

### 定期メンテナンス
- 月次: CloudWatch Logsの確認・クリーンアップ
- 週次: ECSタスクの状態確認
- 日次: アプリケーションログの確認

### スケーリング
```bash
# サービスのスケーリング
aws ecs update-service \
    --cluster production-cluster \
    --service django-ecs-service-production \
    --desired-count 4
```

### バックアップ
- RDSの自動バックアップ設定
- 重要なファイルのS3バックアップ

## 緊急時対応

### サービス停止
```bash
aws ecs update-service \
    --cluster production-cluster \
    --service django-ecs-service-production \
    --desired-count 0
```

### 緊急メンテナンスページ
- ALBでメンテナンスページへリダイレクト設定
- Route53でメンテナンス用サーバーへ切り替え

## 連絡先
- 開発チーム: development@grape-app.jp
- 運用チーム: operations@grape-app.jp
- 緊急時: emergency@grape-app.jp 
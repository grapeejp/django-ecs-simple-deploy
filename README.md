# Django ECS シンプルデプロイ

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

AWS ECS（Elastic Container Service）を使用してDjangoアプリケーションを簡単にデプロイするためのテンプレートリポジトリです。

## 概要

このリポジトリは、最小限の設定でDjangoアプリケーションをAWS ECSにデプロイするためのベストプラクティスとテンプレートを提供します。Dockerコンテナを使用し、AWS Fargateによるサーバーレスアーキテクチャを採用しています。

## 特徴

- 🚀 **シンプルな構成**: 最小限のファイルとコード
- 🔒 **セキュリティ**: 非rootユーザー実行、環境変数管理
- 📊 **スケーラビリティ**: AWS Fargateによる自動スケーリング
- 🔄 **CI/CD対応**: GitHub Actionsによる自動デプロイ
- 📁 **静的ファイル管理**: AWS S3との連携設定済み

## 前提条件

- AWSアカウント
- AWS CLIのインストールと設定
- Dockerのインストール
- Python 3.11以上

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/grapeejp/django-ecs-simple-deploy.git
cd django-ecs-simple-deploy
```

### 2. ローカル開発環境のセットアップ

```bash
# Djangoプロジェクト作成
docker-compose up -d

# ブラウザで確認
# http://localhost:8000
```

### 3. AWS環境変数設定

```bash
export AWS_ACCOUNT_ID=<あなたのAWSアカウントID>
export AWS_REGION=ap-northeast-1
```

### 4. ECRリポジトリ作成とイメージプッシュ

```bash
# ECRにログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# リポジトリ作成（初回のみ）
aws ecr create-repository --repository-name django-ecs-app

# イメージビルドとプッシュ
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest .
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
```

### 5. ECSクラスター作成とデプロイ

```bash
# CloudFormationを使用したECSクラスター作成
aws cloudformation create-stack \
  --stack-name django-ecs-cluster \
  --template-body file://cloudformation/ecs-cluster.yml \
  --capabilities CAPABILITY_IAM

# サービスデプロイ
aws cloudformation create-stack \
  --stack-name django-ecs-service \
  --template-body file://cloudformation/ecs-service.yml \
  --parameters ParameterKey=ImageUrl,ParameterValue=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
```

## ディレクトリ構成

```
django-ecs-simple-deploy/
├── app/                    # Djangoアプリケーション
├── cloudformation/         # AWSリソース定義
│   ├── ecs-cluster.yml     # ECSクラスター
│   └── ecs-service.yml     # ECSサービス
├── docker/                 # Docker関連ファイル
│   ├── Dockerfile          # 本番用Dockerfile
│   └── nginx/              # Nginxコンフィグ
├── scripts/                # デプロイ用スクリプト
├── .github/workflows/      # GitHub Actions
├── docker-compose.yml      # 開発環境設定
└── README.md               # このファイル
```

## ベストプラクティス

### コンテナ設計

- **軽量イメージ**: python:3.11-slimベースイメージを使用
- **マルチステージビルド**: 本番イメージのサイズ最適化
- **非rootユーザー実行**: セキュリティ強化のため
- **環境変数**: 設定は環境変数で注入

### ECS設定

- **Fargate**: サーバーレスでインフラ管理不要
- **Auto Scaling**: CPU使用率に基づく自動スケーリング
- **ヘルスチェック**: エンドポイントでの状態確認

### セキュリティ

- **HTTPS**: ACMとALBによるSSL/TLS対応
- **Secret Manager**: DBパスワードなどの機密情報管理
- **WAF**: 基本的なWebアプリケーション保護

### データベース

- **RDS**: マネージドPostgreSQLサービス
- **バックアップ**: 自動バックアップの設定
- **マルチAZ**: 高可用性構成

### 監視とログ

- **CloudWatch**: ログとメトリクスの収集
- **アラート**: 異常検知時の通知設定
- **X-Ray**: アプリケーショントレーシング

## アーキテクチャ

```
                  ┌─────────────┐
                  │    Route53   │
                  └──────┬──────┘
                         │
                         ▼
┌────────────┐    ┌─────────────┐    ┌─────────────┐
│CloudFront  │◄───┤ Application │◄───┤ ECS Fargate │
│ (optional) │    │Load Balancer│    │   Service   │
└────────────┘    └──────┬──────┘    └──────┬──────┘
                         │                  │
                         │                  │
                  ┌──────┴──────┐    ┌─────┴──────┐
                  │ Target Group│    │   ECR      │
                  └─────────────┘    │ Repository │
                                     └────────────┘
```

## アクセス方法

デプロイが完了すると、以下のURLでアプリケーションにアクセスできます：

http://django-Appli-Eel6airECEW2-1499847413.ap-northeast-1.elb.amazonaws.com

**注意**: DNSの伝播には数分かかる場合があります。また、サービスのデプロイ完了を待つ必要もあります。

## 貢献方法

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 参考リソース

- [AWS Fargate公式ドキュメント](https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Django on AWS ECSのベストプラクティス](https://testdriven.io/blog/deploying-django-to-ecs-with-terraform/)
- [CloudFormation Template Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-reference.html)

## ライセンス

MITライセンスに基づいて配布されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 連絡先

グレイプジャパン - [https://github.com/grapeejp](https://github.com/grapeejp)

プロジェクトリンク: [https://github.com/grapeejp/django-ecs-simple-deploy](https://github.com/grapeejp/django-ecs-simple-deploy) 
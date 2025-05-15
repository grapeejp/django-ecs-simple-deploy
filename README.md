# Django ECS Simple Deploy

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

AWS ECS（Elastic Container Service）を使用してDjangoアプリケーションを簡単にデプロイするためのテンプレートリポジトリです。

## 概要

このリポジトリは、最小限の設定でDjangoアプリケーションをAWS ECSにデプロイするためのベストプラクティスとテンプレートを提供します。Dockerコンテナを使用し、AWS Fargateによるサーバーレスアーキテクチャを採用しています。

ステージング環境と本番環境の両方に対応し、`deploy.sh`スクリプトを使って簡単にデプロイできます。

## 特徴

- 🚀 **シンプルな構成**: 最小限のファイルとコード
- 🔒 **セキュリティ**: 非rootユーザー実行、環境変数管理
- 📊 **スケーラビリティ**: AWS Fargateによる自動スケーリング
- 🔄 **CI/CD対応**: GitHub Actionsによる自動デプロイ
- 📁 **静的ファイル管理**: AWS S3との連携設定済み
- 🌐 **複数環境対応**: ステージング環境と本番環境の簡単な切り替え
- 🖥️ **クロスプラットフォーム**: ARM64アーキテクチャ（M1/M2/M3 Mac）からx86_64環境へのデプロイをサポート

## 前提条件

- AWSアカウント
- AWS CLI v2のインストールと設定
- Dockerのインストール
- Python 3.11以上

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/django-ecs-simple-deploy.git
cd django-ecs-simple-deploy
```

### 2. ローカル開発環境のセットアップ

```bash
# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Linuxまたは MacOS
# または
.venv\Scripts\activate  # Windows

# 依存パッケージのインストール
pip install -r app/requirements.txt

# Djangoアプリケーション実行
cd app
python manage.py migrate
python manage.py runserver
```

### 3. AWS環境変数設定

`.env.staging`や`.env.production`ファイルに環境変数を設定します：

```bash
AWS_ACCOUNT_ID=your_aws_account_id
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### 4. デプロイ

#### ステージング環境へのデプロイ

```bash
./deploy.sh staging
```

#### 本番環境へのデプロイ

```bash
./deploy.sh production
```

## ディレクトリ構成

```
django-ecs-simple-deploy/
├── app/                    # Djangoアプリケーション
├── cloudformation/         # AWSリソース定義
│   ├── ecs-cluster.yml     # ECSクラスター定義
│   ├── ecs-service.yml     # 本番環境サービス定義
│   └── ecs-service-staging.yml # ステージング環境サービス定義
├── docker/                 # Docker関連ファイル
│   ├── Dockerfile          # 本番用Dockerfile
│   └── nginx/              # Nginxコンフィグ
├── scripts/                # デプロイ用スクリプト
├── .github/workflows/      # GitHub Actions
├── .env.staging            # ステージング環境設定
├── .env.production         # 本番環境設定
├── deploy.sh               # デプロイスクリプト
├── docker-compose.yml      # 開発環境設定
└── README.md               # このファイル
```

## デプロイスクリプトの仕組み

`deploy.sh`スクリプトは以下の処理を実行します：

1. **環境変数の読み込み**
   - ステージングまたは本番用の`.env.*`ファイルから設定を読み込み

2. **ECRへのログイン**
   - AWS ECRにDockerクライアントからログイン

3. **ECRリポジトリの確認/作成**
   - リポジトリが存在しない場合は新規作成

4. **Dockerイメージのビルドとプッシュ**
   - ARM64→x86_64のクロスプラットフォームビルド
   - ECRへのイメージプッシュ

5. **AWS Secrets Managerの設定**
   - シークレットの確認/作成（例: Django SECRET_KEY）

6. **CloudFormationスタックのデプロイ**
   - ECSクラスタースタックの確認/作成
   - ECSサービススタックの作成

7. **デプロイ情報の表示**
   - アプリケーションのアクセスURL表示

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

デプロイが完了すると、以下のようなURLでアプリケーションにアクセスできます：

- ステージング環境: http://django-Appli-VSNxHzXCt8uR-72974778.ap-northeast-1.elb.amazonaws.com
- 本番環境: http://django-Appli-21kFlF5Lv7wZ-1653648924.ap-northeast-1.elb.amazonaws.com

**注意**: DNSの伝播には数分かかる場合があります。また、サービスのデプロイ完了を待つ必要もあります。

## 開発〜デプロイの流れ

### 開発環境とプロダクション環境

このプロジェクトでは以下の2つの環境をサポートしています：

- **開発環境（Staging）**: `django-ecs-service-staging`
- **本番環境（Production）**: `django-ecs-service-production`

各環境は分離されており、独自のECSサービス、タスク定義、およびCloudWatchアラームを持ちます。

### 開発ワークフロー

1. **ローカル開発**
   ```bash
   # ローカル環境起動
   cd app
   python manage.py runserver
   
   # コードの変更
   # http://localhost:8000 で動作確認
   ```

2. **ステージング環境へのデプロイ**
   ```bash
   # ワンコマンドでステージング環境にデプロイ
   ./deploy.sh staging
   ```

3. **テストと検証**
   - ステージング環境のURLでアプリケーションをテスト
   - ブラウザでアクセスしてUI/機能確認

4. **本番環境へのデプロイ**
   ```bash
   # ワンコマンドで本番環境にデプロイ
   ./deploy.sh production
   ```

### CI/CD自動化

GitHub Actionsを使用して自動デプロイを設定できます：

1. `.github/workflows/deploy.yml`を設定
2. リポジトリに以下のGitHub Secretsを追加
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `AWS_ACCOUNT_ID`

設定例：
```yaml
name: Deploy to ECS

on:
  push:
    branches: [ main, develop ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'staging' }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: django-ecs-app
        run: |
          docker build --platform=linux/amd64 -t $ECR_REGISTRY/$ECR_REPOSITORY:latest -f docker/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Deploy to ECS
        run: |
          ./deploy.sh $ENVIRONMENT
```

## トラブルシューティング

### よくある問題

1. **エラー: exec /usr/local/bin/python: exec format error**  
   原因: アーキテクチャの不一致  
   解決策: プラットフォームオプションを確認 `--platform=linux/amd64`

2. **コンテナが起動しない**  
   確認点: CloudWatch Logsでログを確認

3. **ヘルスチェック失敗**  
   確認点: ALBのターゲットグループの状態を確認

4. **デプロイがロールバックする**  
   確認点: CloudFormationスタックイベントでエラー内容を確認

5. **CloudWatch Alarm名が競合するエラー**  
   解決策: CloudFormationテンプレートのアラーム名に一意の識別子（TimestampSuffix）を追加する

### デプロイエラーの詳細確認

CloudFormationのスタック状態確認:
```bash
aws cloudformation describe-stack-events --stack-name django-ecs-service-production
```

ECSサービスのステータス確認:
```bash
aws ecs describe-services --cluster django-ecs-cluster-production --services django-ecs-service-production
```

CloudWatchログの確認:
```bash
aws logs get-log-events --log-group-name /ecs/django-app-production --log-stream-name <最新のストリーム名>
```

## 連絡先

プロジェクト管理者: [yourusername](https://github.com/yourusername)

プロジェクトリンク: [https://github.com/yourusername/django-ecs-simple-deploy](https://github.com/yourusername/django-ecs-simple-deploy)

## ライセンス

MIT 
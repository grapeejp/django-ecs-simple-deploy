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
   docker-compose up -d
   
   # コードの変更
   # http://localhost:8000 で動作確認
   ```

2. **ステージング環境へのデプロイ**
   ```bash
   # 環境変数設定
   export AWS_ACCOUNT_ID=<あなたのAWSアカウントID>
   export AWS_REGION=ap-northeast-1
   
   # イメージビルドとプッシュ
   docker build --platform=linux/amd64 -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:staging .
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:staging
   
   # ステージング環境へのデプロイ
   aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
     --stack-name django-ecs-service-staging \
     --parameter-overrides Environment=staging \
     --capabilities CAPABILITY_NAMED_IAM
   ```

3. **テストと検証**
   ```bash
   # ステージング環境のURLを取得
   aws elbv2 describe-load-balancers --names django-Appli-21kFlF5Lv7wZ
   
   # ブラウザでアクセスしてテスト
   # http://django-Appli-XXXXX.ap-northeast-1.elb.amazonaws.com
   ```

4. **本番環境へのデプロイ**
   ```bash
   # latestタグでイメージビルド
   docker build --platform=linux/amd64 -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest .
   docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
   
   # 本番環境へのデプロイ
   aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
     --stack-name django-ecs-service-production \
     --parameter-overrides Environment=production \
     --capabilities CAPABILITY_NAMED_IAM
   ```

### CI/CD自動化

GitHub Actionsを使用して自動デプロイを設定できます：

1. `.github/workflows/deploy.yml`を設定
2. リポジトリに以下のGitHub Secretsを追加
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`

設定例：
```yaml
name: Deploy to ECS

on:
  push:
    branches: [ main ]  # mainブランチにプッシュされたら実行

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
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
          docker build --platform=linux/amd64 -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Deploy to ECS
        run: |
          aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
            --stack-name django-ecs-service-production \
            --parameter-overrides Environment=production \
            --capabilities CAPABILITY_NAMED_IAM
```

### CI/CD設定の詳細

このプロジェクトでは、GitHub Actionsを使用して3つの主要なワークフローを設定しています：

#### 1. テスト実行ワークフロー (test.yml)

```yaml
name: Run Tests

on:
  pull_request:
    branches: [ develop, main ]  # developとmainへのPR時に実行

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r app/requirements.txt
          pip install pytest pytest-django ruff flake8 bandit
          
      - name: Run tests
        run: pytest
        
      - name: Apply auto-format with ruff
        run: ruff format app
        
      - name: Lint with ruff
        run: ruff check app
        
      - name: Security check with bandit
        run: bandit -r app --exclude app/tests,app/config/settings.py
```

**主な機能**:
- Pythonの自動テスト実行（pytest）
- コード整形（ruff format）
- 静的解析（ruff check）
- セキュリティチェック（bandit）
- PRごとの自動実行で品質保証

#### 2. ステージング環境デプロイワークフロー (staging.yml)

```yaml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]  # developブランチへのプッシュ時に実行
  workflow_dispatch:       # 手動実行も可能

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      # AWS認証とECRログイン
      
      - name: Build and push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: django-ecs-app
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:latest-staging -f docker/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest-staging
          
      - name: Deploy ECS Cluster
        run: |
          aws cloudformation deploy \
            --stack-name django-ecs-cluster-staging \
            --template-file cloudformation/ecs-cluster.yml \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides Environment=staging
            
      - name: Deploy ECS Service
        run: |
          aws cloudformation deploy \
            --stack-name django-ecs-service-staging \
            --template-file cloudformation/ecs-service-staging.yml \
            --parameter-overrides ImageUrl=$IMAGE_URI \
            --capabilities CAPABILITY_NAMED_IAM
            
      - name: Get Application URL
        run: |
          ALB_DNS=$(aws cloudformation describe-stacks --stack-name django-ecs-cluster-staging --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNSName'].OutputValue" --output text)
          echo "::notice ::ステージング環境URL: http://$ALB_DNS"
```

**主な機能**:
- M3チップ（ARM64）からx86_64環境へのクロスプラットフォームビルド
- ECRへの`latest-staging`タグ付きイメージプッシュ
- CloudFormationによるインフラスタック作成/更新
- デプロイ完了後のアクセスURL表示

#### 3. 本番環境デプロイワークフロー (production.yml)

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]     # mainブランチへのプッシュ時に実行
  release:
    types: [created]       # リリース作成時にも実行
  workflow_dispatch:       # 手動実行も可能

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Get version from tag
        id: get_version
        run: echo ::set-output name=VERSION::${GITHUB_REF#refs/tags/}
        if: startsWith(github.ref, 'refs/tags/')
      
      # AWS認証とECRログイン
      
      - name: Build and push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: django-ecs-app
          VERSION: ${{ steps.get_version.outputs.VERSION || 'latest' }}
        run: |
          # バージョンタグとlatestタグの両方でプッシュ
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION -t $ECR_REGISTRY/$ECR_REPOSITORY:latest -f docker/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
          
      - name: Deploy ECS Cluster
        run: |
          aws cloudformation deploy \
            --stack-name django-ecs-cluster-production \
            --template-file cloudformation/ecs-cluster.yml \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides Environment=production
            
      - name: Deploy ECS Service
        run: |
          aws cloudformation deploy \
            --stack-name django-ecs-service-production \
            --template-file cloudformation/ecs-service.yml \
            --parameter-overrides \
              ImageUrl=$IMAGE_URI \
              Environment=production \
            --capabilities CAPABILITY_NAMED_IAM
```

**主な機能**:
- バージョンタグ（v1.2.3など）と`latest`タグの併用
- 本番環境用パラメータでのデプロイ
- リリース作成時の自動デプロイ

#### CI/CD環境設定（GitHub Secrets）

GitHub Repositoryに以下のSecretsを設定する必要があります：

| Secret名 | 説明 | 用途 |
|---------|------|------|
| `AWS_ACCESS_KEY_ID` | AWSアクセスキー | AWS APIの認証 |
| `AWS_SECRET_ACCESS_KEY` | AWSシークレットキー | AWS APIの認証 |
| `AWS_REGION` | AWSリージョン（例: ap-northeast-1） | デプロイ先のリージョン指定 |
| `AWS_ACCOUNT_ID` | AWSアカウントID | ECRリポジトリのフルパス生成 |
| `SECRET_KEY` | Django SECRET_KEY | テスト実行時に使用 |
| `SLACK_WEBHOOK_URL` | Slack通知用WebhookURL | デプロイ結果の通知（オプション） |

#### デプロイ時の環境分離

環境ごとに分離されたデプロイパラメータを使用しています：

- **ステージング**: `Environment=staging`
  - 専用のALB、ターゲットグループ
  - `latest-staging`タグのイメージ
  - CloudFormationスタック名に`-staging`サフィックス

- **本番**: `Environment=production`
  - 専用のALB、ターゲットグループ
  - `latest`タグのイメージ（およびバージョンタグ）
  - CloudFormationスタック名に`-production`サフィックス

### ブランチ戦略とCI/CD連携フロー

本プロジェクトでは、以下のブランチ戦略とCI/CDパイプラインを採用しています：

```
feature/* → develop → main
   ↓           ↓        ↓
  テスト    ステージング  本番
```

#### 1. 開発フロー（feature ブランチ）

1. **新規ブランチ作成**
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/new-awesome-feature
   ```

2. **開発作業**
   - ローカルでの開発とテスト
   - コミットとプッシュ
   ```bash
   git add .
   git commit -m "feat: 素晴らしい機能を追加"
   git push origin feature/new-awesome-feature
   ```

3. **プルリクエスト（PR）作成**
   - GitHubでfeature/new-awesome-feature → develop へのPRを作成
   - 自動テストが実行される（PR作成時）
   ```yaml
   # .github/workflows/test.yml の例
   name: Test
   
   on:
     pull_request:
       branches: [ develop, main ]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: Set up Python
           uses: actions/setup-python@v2
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
         - name: Run tests
           run: |
             pytest
   ```

#### 2. ステージング環境へのデプロイ（develop ブランチ）

1. **developへのマージ**
   - テスト通過後、PRをdevelopブランチにマージ
   - マージ後、自動的にステージング環境へのデプロイが開始

2. **自動デプロイ設定**
   ```yaml
   # .github/workflows/deploy-staging.yml の例
   name: Deploy to Staging
   
   on:
     push:
       branches: [ develop ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         
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
             docker build --platform=linux/amd64 -t $ECR_REGISTRY/$ECR_REPOSITORY:staging .
             docker push $ECR_REGISTRY/$ECR_REPOSITORY:staging
         
         - name: Deploy to ECS Staging
           run: |
             aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
               --stack-name django-ecs-service-staging \
               --parameter-overrides Environment=staging \
               --capabilities CAPABILITY_NAMED_IAM
   ```

3. **ステージング環境でのテスト確認**
   - 自動テストだけでなく、ステージング環境で手動テストも実施
   - 問題があれば、新たなfixブランチを作成して修正

#### 3. 本番環境へのデプロイ（main ブランチ）

1. **mainへのマージ**
   - ステージング環境での確認が完了したら、develop → main へのPRを作成
   - コードレビュー後、mainブランチにマージ
   - タグを付与（リリースバージョン管理のため）
   ```bash
   git checkout main
   git pull
   git tag -a v1.2.3 -m "バージョン1.2.3をリリース"
   git push origin v1.2.3
   ```

2. **自動デプロイ設定**
   ```yaml
   # .github/workflows/deploy-production.yml の例
   name: Deploy to Production
   
   on:
     push:
       branches: [ main ]
       tags:
         - 'v*'  # タグがプッシュされた場合も実行
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         
         - name: Get version from tag
           id: get_version
           run: echo ::set-output name=VERSION::${GITHUB_REF#refs/tags/}
           if: startsWith(github.ref, 'refs/tags/')
         
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
             VERSION: ${{ steps.get_version.outputs.VERSION || 'latest' }}
           run: |
             # タグバージョンとlatestタグの両方でプッシュ
             docker build --platform=linux/amd64 -t $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
             docker push $ECR_REGISTRY/$ECR_REPOSITORY:$VERSION
             docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
         
         - name: Deploy to ECS Production
           run: |
             aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
               --stack-name django-ecs-service-production \
               --parameter-overrides Environment=production \
               --capabilities CAPABILITY_NAMED_IAM
   ```

3. **デプロイ後の確認**
   - 本番環境でのサービス状態を確認
   - CloudWatchでログとメトリクスをモニタリング
   - 問題が発生した場合は、ロールバックを検討

#### CI/CD連携図

```
┌───────────┐      ┌───────┐      ┌───────┐      ┌───────────┐
│ feature/* │─────▶│develop│─────▶│ main  │─────▶│ リリース  │
└───────────┘      └───────┘      └───────┘      └───────────┘
       │               │              │                │
       ▼               ▼              ▼                ▼
┌───────────┐      ┌───────┐      ┌───────┐      ┌───────────┐
│自動テスト │      │自動デプロイ │ │自動デプロイ │ │タグリリース │
│ (PR時)    │      │(ステージング)│ │ (本番)    │ │ (v1.2.3)  │
└───────────┘      └───────┘      └───────┘      └───────────┘
```

この流れにより、コード品質を保ちながら、段階的かつ安全にデプロイを実現できます。

### トラブルシューティング

デプロイ中に問題が発生した場合：

1. **CloudFormationのスタック状態確認**
   ```bash
   aws cloudformation describe-stack-events --stack-name django-ecs-service-production
   ```

2. **ECSサービスのステータス確認**
   ```bash
   aws ecs describe-services --cluster django-ecs-cluster-production --services django-ecs-service-production
   ```

3. **CloudWatchログの確認**
   ```bash
   aws logs get-log-events --log-group-name /ecs/django-app-production --log-stream-name <最新のストリーム名>
   ```

4. **エラー発生時のスタック削除と再デプロイ**
   ```bash
   # ROLLBACK_COMPLETE状態のスタックは更新できないため削除が必要
   aws cloudformation delete-stack --stack-name django-ecs-service-production
   aws cloudformation wait stack-delete-complete --stack-name django-ecs-service-production
   
   # 削除完了後に再デプロイ
   aws cloudformation deploy --template-file cloudformation/ecs-service.yml \
     --stack-name django-ecs-service-production \
     --parameter-overrides Environment=production \
     --capabilities CAPABILITY_NAMED_IAM
   ```


## 連絡先

グレイプジャパン - [https://github.com/grapeejp](https://github.com/grapeejp)

プロジェクトリンク: [https://github.com/grapeejp/django-ecs-simple-deploy](https://github.com/grapeejp/django-ecs-simple-deploy) 
# CI/CD整備

本ドキュメントでは、Django ECSプロジェクトのCI/CD（継続的インテグレーション/継続的デプロイメント）パイプラインの構築方法について説明します。

## CI/CDの目的

- 開発の効率化と品質向上
- 人為的ミスの削減
- デプロイ頻度の向上と時間短縮
- 自動テストによる品質保証

## GitHub Actionsによる実装

本プロジェクトでは、GitHub Actionsを使用してCI/CDパイプラインを構築します。

### ワークフロー概要

以下の3つの主要ワークフローを実装します：

1. **テストワークフロー**: すべてのプルリクエストに対して実行
2. **ステージングデプロイワークフロー**: `main`ブランチへのマージ時に実行
3. **本番デプロイワークフロー**: リリースタグ作成時に実行

### ディレクトリ構成

```
.github/
└── workflows/
    ├── test.yml         # テスト実行ワークフロー
    ├── staging.yml      # ステージング環境デプロイワークフロー
    └── production.yml   # 本番環境デプロイワークフロー
```

### テストワークフロー実装手順

1. `.github/workflows/test.yml`ファイルを作成：

```yaml
name: Run Tests

on:
  pull_request:
    branches: [ main ]

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
        
    - name: Run tests
      run: |
        cd app
        python manage.py test
        
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
```

### ステージングデプロイワークフロー実装手順

1. `.github/workflows/staging.yml`ファイルを作成：

```yaml
name: Deploy to Staging

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
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
      
    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: django-ecs-app
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -t $ECR_REGISTRY/$ECR_REPOSITORY:latest .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
        
    - name: Deploy to ECS
      run: |
        aws cloudformation deploy \
          --stack-name django-ecs-service-staging \
          --template-file cloudformation/ecs-service.yml \
          --parameter-overrides \
            ImageUrl=${{ steps.login-ecr.outputs.registry }}/django-ecs-app:${{ github.sha }} \
            Environment=staging
```

### 本番デプロイワークフロー実装手順

1. `.github/workflows/production.yml`ファイルを作成：

```yaml
name: Deploy to Production

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
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
      
    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: django-ecs-app
        IMAGE_TAG: ${{ github.event.release.tag_name }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        
    - name: Deploy to ECS
      run: |
        aws cloudformation deploy \
          --stack-name django-ecs-service-prod \
          --template-file cloudformation/ecs-service.yml \
          --parameter-overrides \
            ImageUrl=${{ steps.login-ecr.outputs.registry }}/django-ecs-app:${{ github.event.release.tag_name }} \
            Environment=production
```

## GitHub Secretsの設定

GitHub上で以下のシークレットを設定します：

1. リポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
2. 以下のシークレットを追加：
   - `AWS_ACCESS_KEY_ID`: AWSアクセスキーID
   - `AWS_SECRET_ACCESS_KEY`: AWSシークレットアクセスキー
   - `AWS_REGION`: AWSリージョン（例：ap-northeast-1）
   - `AWS_ACCOUNT_ID`: AWSアカウントID

## テスト自動化

### ユニットテストの実装

1. Djangoアプリケーションのテストを実装：

```python
# app/hello_django/tests.py
from django.test import TestCase, Client
from django.urls import reverse

class HealthCheckTest(TestCase):
    def test_health_check(self):
        client = Client()
        response = client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')
```

### カバレッジ測定

テストカバレッジを測定して報告するため、以下の手順を実装：

1. `coverage`パッケージをインストール：

```bash
pip install coverage
```

2. カバレッジレポート生成用のワークフローステップを追加：

```yaml
- name: Generate coverage report
  run: |
    pip install coverage
    cd app
    coverage run manage.py test
    coverage xml
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./app/coverage.xml
```

## デプロイ自動化の詳細設定

### 複数環境の切り替え

環境ごとに異なる設定を適用するため、以下の方法を実装：

1. CloudFormationテンプレートにパラメーターを追加：

```yaml
Parameters:
  Environment:
    Type: String
    Default: staging
    AllowedValues:
      - staging
      - production
```

2. 環境変数を条件付きで設定：

```yaml
  WebService:
    Type: AWS::ECS::Service
    Properties:
      TaskDefinition:
        Fn::GetAtt: [TaskDefinition, Arn]
      ContainerDefinitions:
        - Name: django-app
          Environment:
            - Name: DJANGO_SETTINGS_MODULE
              Value: !If [IsProduction, "hello_django.settings.production", "hello_django.settings.staging"]
```

### デプロイ通知の設定

Slack通知を設定して、デプロイ結果を自動通知：

```yaml
- name: Slack notification
  uses: rtCamp/action-slack-notify@v2
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    SLACK_CHANNEL: deployments
    SLACK_COLOR: ${{ job.status }}
    SLACK_TITLE: Deploy to ${{ matrix.environment }}
    SLACK_MESSAGE: 'Deployment to ${{ matrix.environment }} ${{ job.status }}'
```

## CI/CD改善のロードマップ

### 短期的な改善項目

- [ ] E2Eテストの追加（Selenium/Cypress）
- [ ] セキュリティスキャンの統合（Snyk/Trivy）
- [ ] コードの静的解析（SonarQube）

### 中長期的な改善項目

- [ ] ブルー/グリーンデプロイの実装
- [ ] カナリアリリースの導入
- [ ] インフラのコード化（Terraform）の完全導入 
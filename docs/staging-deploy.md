# ステージング環境デプロイ手順書（Option B: ハイブリッド方式）

## 概要

本ドキュメントは、AWS ECS へのステージング環境デプロイにおいて、VPC競合問題やALBリスナールール競合を回避するための**Option B（ハイブリッド方式）**の詳細な手順を記載しています。

### Option B（ハイブリッド方式）とは

- **基盤インフラ**（VPC、ALB、ECSクラスター）：CloudFormationで**1回だけ**作成
- **アプリケーションデプロイ**：GitHub Actions + AWS CLIで既存リソースを更新
- **新規リソースは作成しない**：VPC上限問題を完全に回避

### なぜこの方式を採用するのか

1. **VPC上限問題の回避**：AWSアカウントのVPC上限は5個（デフォルト）
2. **ALBリスナールール競合の回避**：タイムスタンプ付きスタック名による無限ループを防止
3. **高速デプロイ**：インフラ作成なし、アプリケーションのみ更新
4. **シンプルな管理**：固定リソース名による明確な構成

## 前提条件

- AWS CLIがインストール・設定済み
- DockerおよびDocker Composeがインストール済み
- 適切なIAM権限を持つAWSアカウント
- GitHubリポジトリへのアクセス権限

## 1. 初回セットアップ（基盤インフラの作成）

**⚠️ 重要：この手順は環境ごとに1回だけ実行します**

### 1.1 既存スタックの確認

```bash
# 既存のECS関連スタックを確認
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?contains(StackName, 'django-ecs')].[StackName,StackStatus]" \
  --output table
```

### 1.2 基盤インフラスタックの作成/更新

```bash
# 環境変数の設定
export AWS_REGION=ap-northeast-1
export ENVIRONMENT=staging

# クラスタースタックの作成（VPC、ALB、ECSクラスター含む）
aws cloudformation deploy \
  --stack-name django-ecs-cluster-${ENVIRONMENT} \
  --template-file cloudformation/ecs-cluster.yml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Environment=${ENVIRONMENT}
```

### 1.3 作成されるリソース

- **VPC**: 1つのみ（再利用）
- **パブリック/プライベートサブネット**: 各2つ
- **ALB**: 1つ（複数サービスで共有）
- **ECSクラスター**: 1つ
- **セキュリティグループ**: 必要最小限

### 1.4 重要な出力値の確認

```bash
# スタックの出力値を確認（後の手順で使用）
aws cloudformation describe-stacks \
  --stack-name django-ecs-cluster-${ENVIRONMENT} \
  --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
  --output table
```

## 2. タスク定義の管理

### 2.1 タスク定義JSONファイルの作成

`task-definition-staging.json` を作成：

```json
{
  "family": "django-app-staging",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "django-app",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/django-ecs-app:${IMAGE_TAG}",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DEBUG",
          "value": "0"
        },
        {
          "name": "ALLOWED_HOSTS",
          "value": "*.elb.amazonaws.com,staging.grape-app.jp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/django-app-staging",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 2.2 環境変数の管理

- **ALLOWED_HOSTS**: ALBのDNS名とカスタムドメインを含める
- **DEBUG**: ステージング環境では0（本番モード）
- その他の環境変数はSecrets Managerから取得することを推奨

## 3. ECSサービスの作成（初回のみ）

**⚠️ 初回のみ実行。2回目以降は「4. CI/CDワークフロー設定」へ**

```bash
# サービス作成用のJSONファイル
cat > ecs-service-staging.json << EOF
{
  "serviceName": "django-ecs-service-staging",
  "taskDefinition": "django-app-staging",
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:${AWS_REGION}:${AWS_ACCOUNT_ID}:targetgroup/...",
      "containerName": "django-app",
      "containerPort": 8000
    }
  ],
  "desiredCount": 2,
  "launchType": "FARGATE",
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-xxx", "subnet-yyy"],
      "securityGroups": ["sg-xxx"],
      "assignPublicIp": "DISABLED"
    }
  },
  "healthCheckGracePeriodSeconds": 60
}
EOF

# サービスの作成
aws ecs create-service \
  --cluster django-ecs-cluster-staging \
  --cli-input-json file://ecs-service-staging.json
```

## 4. CI/CDワークフロー設定

### 4.1 GitHub Actions ワークフロー

`.github/workflows/auto_deploy_staging.yml`:

```yaml
name: Deploy to Staging (Option B)

on:
  push:
    branches: [ develop ]

env:
  AWS_REGION: ap-northeast-1
  ECR_REPOSITORY: django-ecs-app
  ECS_CLUSTER: django-ecs-cluster-staging
  ECS_SERVICE: django-ecs-service-staging
  TASK_DEFINITION_FAMILY: django-app-staging

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2
    
    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f docker/Dockerfile .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
    
    - name: Fill in the new image ID in the task definition
      id: task-def
      uses: aws-actions/amazon-ecs-render-task-definition@v1
      with:
        task-definition: task-definition-staging.json
        container-name: django-app
        image: ${{ steps.build-image.outputs.image }}
    
    - name: Deploy Amazon ECS task definition
      uses: aws-actions/amazon-ecs-deploy-task-definition@v1
      with:
        task-definition: ${{ steps.task-def.outputs.task-definition }}
        service: ${{ env.ECS_SERVICE }}
        cluster: ${{ env.ECS_CLUSTER }}
        wait-for-service-stability: true
```

### 4.2 重要なポイント

1. **固定リソース名**：タイムスタンプを使用しない
2. **既存サービスの更新**：新規作成ではなく更新
3. **タスク定義のバージョニング**：自動的に新しいリビジョンが作成される
4. **ロールバック可能**：前のタスク定義リビジョンに戻せる

## 5. 手動デプロイ手順（デバッグ用）

CI/CDが動作しない場合の手動デプロイ手順：

```bash
# 1. ECRにログイン
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 2. Dockerイメージをビルド・プッシュ
docker build -t django-ecs-app:latest -f docker/Dockerfile .
docker tag django-ecs-app:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/django-ecs-app:latest

# 3. タスク定義を登録
aws ecs register-task-definition --cli-input-json file://task-definition-staging.json

# 4. サービスを更新（新しいタスク定義を使用）
aws ecs update-service \
  --cluster django-ecs-cluster-staging \
  --service django-ecs-service-staging \
  --task-definition django-app-staging \
  --force-new-deployment
```

## 6. トラブルシューティング

### 6.1 VPC上限エラー

```
The maximum number of VPCs has been reached
```

**解決方法**：
1. 既存VPCを再利用（新規作成しない）
2. 不要なVPCを削除
3. AWS Supportに上限緩和を申請

### 6.2 ALBリスナールール競合

```
A rule with the given priority already exists
```

**解決方法**：
1. 固定Priority値を使用
2. 環境ごとに異なるPriority値を設定
3. Host-headerやPath-patternで分離

### 6.3 タスクが起動しない

```bash
# タスクの状態を確認
aws ecs describe-tasks \
  --cluster django-ecs-cluster-staging \
  --tasks $(aws ecs list-tasks --cluster django-ecs-cluster-staging --service-name django-ecs-service-staging --query 'taskArns[0]' --output text)

# CloudWatch Logsでエラーを確認
aws logs tail /ecs/django-app-staging --follow
```

### 6.4 ヘルスチェック失敗

**確認項目**：
1. セキュリティグループでポート8000が開いているか
2. Djangoアプリケーションが正しく起動しているか
3. ALLOWED_HOSTSにALBのDNS名が含まれているか

## 7. ベストプラクティス

### 7.1 リソース命名規則

```
クラスター: django-ecs-cluster-{environment}
サービス: django-ecs-service-{environment}
タスク定義: django-app-{environment}
```

### 7.2 セキュリティ

- IAMロールは最小権限の原則に従う
- Secrets ManagerまたはSSM Parameter Storeで機密情報を管理
- プライベートサブネットでタスクを実行

### 7.3 監視

- CloudWatch Logsでアプリケーションログを確認
- CloudWatch Metricsでリソース使用率を監視
- X-Rayでアプリケーションのトレースを実施

## 8. よくある質問（FAQ）

**Q: なぜCloudFormationを完全に使わないのか？**
A: CloudFormationでタスク定義やサービスを管理すると、更新のたびにスタック全体の更新が必要になり、デプロイが遅くなります。基盤インフラのみCloudFormationで管理し、アプリケーションデプロイは高速化のために分離しています。

**Q: VPCを削除したい場合は？**
A: まず、VPC内のすべてのリソース（ECSサービス、ALB、NAT Gatewayなど）を削除する必要があります。その後、CloudFormationスタックを削除します。

**Q: 本番環境も同じ方式で良いか？**
A: はい。環境名を変えるだけで同じ方式が使用できます。ただし、本番環境ではBlue/Greenデプロイメントの検討も推奨します。

## 9. 次のステップ

1. **HTTPS対応**：ACM証明書の追加とALBリスナーの設定
2. **オートスケーリング**：Application Auto Scalingの設定
3. **Blue/Greenデプロイメント**：CodeDeployとの連携
4. **監視強化**：DatadogやNew Relicの導入

---

**最終更新日**: 2024年6月19日
**作成者**: Claude（AI Assistant）
**レビュー**: 未実施
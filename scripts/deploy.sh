#!/bin/bash
set -e

# 環境変数のチェック
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "エラー: AWS_ACCOUNT_ID環境変数が設定されていません"
  exit 1
fi

if [ -z "$AWS_REGION" ]; then
  echo "エラー: AWS_REGION環境変数が設定されていません"
  exit 1
fi

# 環境の設定（デフォルトはproduction）
ENVIRONMENT=${ENVIRONMENT:-production}

# ECRへのログイン
echo "ECRにログインしています..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# ECRリポジトリが存在するか確認し、なければ作成
REPO_NAME="django-ecs-app"
REPO_EXISTS=$(aws ecr describe-repositories --repository-names $REPO_NAME 2>/dev/null || echo "not_exists")

if [[ $REPO_EXISTS == "not_exists" ]]; then
  echo "ECRリポジトリを作成しています: $REPO_NAME"
  aws ecr create-repository --repository-name $REPO_NAME
fi

# イメージのビルドとプッシュ
echo "Dockerイメージをビルドしています..."
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest -f docker/Dockerfile .

echo "ECRにイメージをプッシュしています..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest

# CloudFormationスタックのデプロイ
CLUSTER_STACK_NAME="django-ecs-cluster-$ENVIRONMENT"
SERVICE_STACK_NAME="django-ecs-service-$ENVIRONMENT"

# クラスタースタックが存在するか確認
CLUSTER_EXISTS=$(aws cloudformation describe-stacks --stack-name $CLUSTER_STACK_NAME 2>/dev/null || echo "not_exists")

if [[ $CLUSTER_EXISTS == "not_exists" ]]; then
  echo "ECSクラスタースタックを作成しています..."
  aws cloudformation create-stack \
    --stack-name $CLUSTER_STACK_NAME \
    --template-body file://cloudformation/ecs-cluster.yml \
    --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    --capabilities CAPABILITY_IAM

  echo "スタックの作成が完了するまで待機しています..."
  aws cloudformation wait stack-create-complete --stack-name $CLUSTER_STACK_NAME
else
  echo "既存のECSクラスタースタックを更新しています..."
  aws cloudformation update-stack \
    --stack-name $CLUSTER_STACK_NAME \
    --template-body file://cloudformation/ecs-cluster.yml \
    --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
    --capabilities CAPABILITY_IAM || echo "更新の必要はありません"
fi

# サービススタックが存在するか確認
SERVICE_EXISTS=$(aws cloudformation describe-stacks --stack-name $SERVICE_STACK_NAME 2>/dev/null || echo "not_exists")

IMAGE_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest"

if [[ $SERVICE_EXISTS == "not_exists" ]]; then
  echo "ECSサービススタックを作成しています..."
  aws cloudformation create-stack \
    --stack-name $SERVICE_STACK_NAME \
    --template-body file://cloudformation/ecs-service.yml \
    --parameters ParameterKey=ImageUrl,ParameterValue=$IMAGE_URL ParameterKey=Environment,ParameterValue=$ENVIRONMENT

  echo "スタックの作成が完了するまで待機しています..."
  aws cloudformation wait stack-create-complete --stack-name $SERVICE_STACK_NAME
else
  echo "既存のECSサービススタックを更新しています..."
  aws cloudformation update-stack \
    --stack-name $SERVICE_STACK_NAME \
    --template-body file://cloudformation/ecs-service.yml \
    --parameters ParameterKey=ImageUrl,ParameterValue=$IMAGE_URL ParameterKey=Environment,ParameterValue=$ENVIRONMENT || echo "更新の必要はありません"
fi

# ALBのDNS名を取得して表示
echo "デプロイが完了しました！"
ALB_DNS=$(aws cloudformation describe-stacks --stack-name $CLUSTER_STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNSName'].OutputValue" --output text)

echo ""
echo "アプリケーションにアクセスするには以下のURLを使用してください:"
echo "http://$ALB_DNS"
echo "" 
#!/bin/bash
# チャットワークSecrets Manager設定スクリプト

set -e

# カラー設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 チャットワーク Secrets Manager セットアップ${NC}"
echo "================================================"

# 環境設定
if [ -z "$1" ]; then
    echo -e "${YELLOW}使用方法: $0 <environment> [api_token] [room_id]${NC}"
    echo "例: $0 production your-api-token your-room-id"
    echo "例: $0 staging  # 対話式入力"
    exit 1
fi

ENVIRONMENT=$1
STACK_NAME="django-ecs-cluster-${ENVIRONMENT}"

echo -e "${BLUE}📋 環境: ${ENVIRONMENT}${NC}"

# API トークンとルームIDの取得
if [ -n "$2" ] && [ -n "$3" ]; then
    CHATWORK_API_TOKEN=$2
    CHATWORK_ROOM_ID=$3
    echo -e "${GREEN}✅ コマンドライン引数から認証情報を取得${NC}"
else
    echo -e "${YELLOW}💬 チャットワーク認証情報を入力してください:${NC}"
    
    read -p "API Token: " -s CHATWORK_API_TOKEN
    echo
    read -p "Room ID: " CHATWORK_ROOM_ID
    
    if [ -z "$CHATWORK_API_TOKEN" ] || [ -z "$CHATWORK_ROOM_ID" ]; then
        echo -e "${RED}❌ API TokenまたはRoom IDが入力されていません${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 認証情報の入力完了${NC}"
fi

# CloudFormationスタックの存在確認
echo -e "${BLUE}🔍 CloudFormationスタック確認: ${STACK_NAME}${NC}"
if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text >/dev/null 2>&1; then
    echo -e "${RED}❌ CloudFormationスタック '${STACK_NAME}' が見つかりません${NC}"
    echo "先にECSクラスターをデプロイしてください:"
    echo "aws cloudformation deploy --template-file cloudformation/ecs-cluster.yml --stack-name ${STACK_NAME} --capabilities CAPABILITY_IAM"
    exit 1
fi

echo -e "${GREEN}✅ CloudFormationスタック確認完了${NC}"

# CloudFormationスタックの更新
echo -e "${BLUE}🚀 CloudFormationスタック更新開始${NC}"
aws cloudformation deploy \
    --template-file cloudformation/ecs-cluster.yml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        ChatworkApiToken="$CHATWORK_API_TOKEN" \
        ChatworkRoomId="$CHATWORK_ROOM_ID" \
    --capabilities CAPABILITY_IAM

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ CloudFormationスタック更新完了${NC}"
else
    echo -e "${RED}❌ CloudFormationスタック更新に失敗しました${NC}"
    exit 1
fi

# Secrets Managerの確認
echo -e "${BLUE}🔍 Secrets Manager確認${NC}"
SECRET_NAME="django-ecs-chatwork-${ENVIRONMENT}"

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Secrets Manager設定完了: ${SECRET_NAME}${NC}"
    
    # シークレットの値を確認（APIトークンは隠す）
    echo -e "${BLUE}📊 設定内容確認:${NC}"
    SECRET_VALUE=$(aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --query 'SecretString' --output text)
    
    API_TOKEN_MASKED=$(echo "$SECRET_VALUE" | jq -r '.CHATWORK_API_TOKEN' | sed 's/./*/g')
    ROOM_ID=$(echo "$SECRET_VALUE" | jq -r '.CHATWORK_ROOM_ID')
    
    echo "   - API Token: $API_TOKEN_MASKED"
    echo "   - Room ID: $ROOM_ID"
else
    echo -e "${YELLOW}⚠️ チャットワーク設定が見つかりません（空のパラメータの可能性）${NC}"
fi

# ECSサービス情報の表示
echo -e "${BLUE}📋 ECSサービス情報${NC}"
ECS_CLUSTER="django-ecs-cluster-${ENVIRONMENT}"
ECS_SERVICE="django-ecs-service-${ENVIRONMENT}"

if aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ECSサービス確認完了: ${ECS_SERVICE}${NC}"
    echo -e "${YELLOW}💡 新しい環境変数を適用するには、ECSサービスの再デプロイが必要です:${NC}"
    echo "aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment"
else
    echo -e "${YELLOW}⚠️ ECSサービスが見つかりません: ${ECS_SERVICE}${NC}"
    echo "ECSサービスのデプロイが必要です"
fi

echo
echo -e "${GREEN}🎉 チャットワーク Secrets Manager セットアップ完了！${NC}"
echo
echo -e "${BLUE}📝 次のステップ:${NC}"
echo "1. ECSサービスの再デプロイ（新しい環境変数を適用）"
echo "2. チャットワーク通知のテスト実行"
echo "3. エラー発生時の自動通知確認"
echo
echo -e "${BLUE}🧪 テスト方法:${NC}"
echo "python test_chatwork_notification.py" 
# 本番環境モニタリング設定ガイド

このドキュメントでは、Django ECS Simple Deploy プロジェクトの本番環境におけるモニタリング設定について説明します。適切なモニタリングは、問題の早期発見と迅速な対応を可能にし、サービスの安定運用に不可欠です。

## 目次

1. [CloudWatch メトリクス監視](#cloudwatch-メトリクス監視)
2. [ログ監視](#ログ監視)
3. [アラート設定](#アラート設定)
4. [ヘルスチェック](#ヘルスチェック)
5. [カスタムメトリクス](#カスタムメトリクス)
6. [ダッシュボード](#ダッシュボード)

## CloudWatch メトリクス監視

### 基本メトリクス

以下の基本メトリクスを監視することをお勧めします：

#### ECSメトリクス
- **CPUUtilization**: CPU使用率
- **MemoryUtilization**: メモリ使用率
- **RunningTaskCount**: 実行中のタスク数

#### ALBメトリクス
- **HTTPCode_Target_2XX_Count**: 成功レスポンス数
- **HTTPCode_Target_4XX_Count**: クライアントエラー数
- **HTTPCode_Target_5XX_Count**: サーバーエラー数
- **TargetResponseTime**: レスポンス時間

#### RDSメトリクス
- **CPUUtilization**: CPU使用率
- **DatabaseConnections**: 接続数
- **FreeableMemory**: 利用可能メモリ
- **FreeStorageSpace**: 空きストレージ

### メトリクス監視の設定

CloudWatchコンソールで以下の手順で設定します：

1. AWSマネジメントコンソールにログイン
2. CloudWatchサービスを選択
3. 左側のナビゲーションから「メトリクス」を選択
4. 「すべてのメトリクス」タブで、監視したいサービス（ECS、ALB、RDSなど）を選択
5. 関連するメトリクスを選択して「グラフ化されたメトリクス」タブに追加
6. 「アクション」→「アラームの作成」でアラート設定

## ログ監視

### CloudWatch Logs設定

ECSタスク定義では、以下のログ設定を使用しています：

```json
"logConfiguration": {
  "logDriver": "awslogs",
  "options": {
    "awslogs-group": "/ecs/django-app",
    "awslogs-region": "${AWS_REGION}",
    "awslogs-stream-prefix": "ecs"
  }
}
```

### ログフィルターとアラート

重要なログパターンに基づいたメトリクスフィルターを作成します：

1. CloudWatch Logsコンソールでロググループを選択
2. 「アクション」→「メトリクスフィルターの作成」を選択
3. フィルターパターンを定義（例：`ERROR`、`CRITICAL`、`EXCEPTION`）
4. メトリクス名と名前空間を設定
5. 作成したメトリクスに対してアラームを設定

### 主要ログフィルターパターン例

```
# エラーログ検出
?ERROR ?Error ?error

# 例外検出
?Exception ?exception ?EXCEPTION

# データベース関連エラー
?DatabaseError ?IntegrityError ?OperationalError

# セキュリティ関連
?Unauthorized ?Forbidden ?CSRF
```

## アラート設定

### 主要アラート

以下のアラートを設定することをお勧めします：

1. **高CPU使用率アラート**
   - メトリクス: ECS CPUUtilization
   - しきい値: 80% 以上が5分間続く
   - アクション: SNS通知

2. **高メモリ使用率アラート**
   - メトリクス: ECS MemoryUtilization
   - しきい値: 85% 以上が5分間続く
   - アクション: SNS通知

3. **エラーレート高アラート**
   - メトリクス: ALB HTTPCode_Target_5XX_Count
   - しきい値: 1分間に5回以上
   - アクション: SNS通知

4. **異常レスポンスタイムアラート**
   - メトリクス: ALB TargetResponseTime
   - しきい値: 2秒以上が5分間続く
   - アクション: SNS通知

5. **データベース接続枯渇アラート**
   - メトリクス: RDS DatabaseConnections
   - しきい値: 最大接続数の80%以上
   - アクション: SNS通知

### アラート通知設定

1. SNSトピックの作成:
```bash
aws sns create-topic --name django-app-alerts
```

2. SNSトピックへのサブスクリプション追加:
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:region:account-id:django-app-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

3. CloudWatch アラームとSNSトピックの連携:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "High-CPU-Utilization" \
  --alarm-description "CPU utilization exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ClusterName,Value=django-ecs-cluster Name=ServiceName,Value=django-app-service \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:region:account-id:django-app-alerts
```

## ヘルスチェック

### ALBヘルスチェック

ALBターゲットグループでは以下のヘルスチェック設定を使用します：

- **パス**: `/health/`（アプリケーションの専用ヘルスチェックエンドポイント）
- **ポート**: トラフィックポート
- **プロトコル**: HTTP
- **正常しきい値**: 3（正常とみなすまでの連続成功回数）
- **非正常しきい値**: 2（非正常とみなすまでの連続失敗回数）
- **タイムアウト**: 5秒
- **間隔**: 30秒

### Djangoヘルスチェックエンドポイント

アプリケーションに以下のようなヘルスチェックエンドポイントを実装します：

```python
# app/views.py
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

def health_check(request):
    # データベース接続確認
    db_healthy = True
    try:
        connections['default'].cursor()
    except OperationalError:
        db_healthy = False
    
    # その他のサービス依存確認をここに追加
    
    status = 200 if db_healthy else 500
    health_status = {
        'status': 'healthy' if db_healthy else 'unhealthy',
        'database': 'connected' if db_healthy else 'disconnected',
        # 他のコンポーネントのステータスを追加
    }
    
    return JsonResponse(health_status, status=status)
```

URLの設定:
```python
# urls.py
from django.urls import path
from app.views import health_check

urlpatterns = [
    # 他のURLパターン
    path('health/', health_check, name='health_check'),
]
```

## カスタムメトリクス

### アプリケーションメトリクス

アプリケーションから以下のカスタムメトリクスを収集することをお勧めします：

1. **APIリクエスト数**: エンドポイント別リクエスト数
2. **APIレスポンスタイム**: エンドポイント別処理時間
3. **ユーザーアクション**: 重要ユーザーアクション完了数
4. **エラー数**: タイプ別エラー数
5. **キャッシュヒット率**: キャッシュの効率性

### CloudWatchカスタムメトリクス実装

Djangoミドルウェアを使ってカスタムメトリクスを実装します：

```python
# middleware.py
import time
import boto3
from django.conf import settings

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.cloudwatch = boto3.client('cloudwatch')

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # パスが /health/ でない場合のみメトリクスを送信
        if not request.path.startswith('/health/'):
            # リクエスト時間メトリクス
            self.cloudwatch.put_metric_data(
                Namespace='Django/API',
                MetricData=[
                    {
                        'MetricName': 'ResponseTime',
                        'Dimensions': [
                            {
                                'Name': 'Path',
                                'Value': request.path
                            },
                        ],
                        'Value': duration,
                        'Unit': 'Seconds'
                    },
                ]
            )
            
            # ステータスコードメトリクス
            self.cloudwatch.put_metric_data(
                Namespace='Django/API',
                MetricData=[
                    {
                        'MetricName': f'StatusCode_{str(response.status_code)[0]}xx',
                        'Dimensions': [
                            {
                                'Name': 'Path',
                                'Value': request.path
                            },
                        ],
                        'Value': 1,
                        'Unit': 'Count'
                    },
                ]
            )
        
        return response
```

## ダッシュボード

### CloudWatchダッシュボード

主要メトリクスを可視化するダッシュボードを作成します：

```bash
aws cloudwatch put-dashboard \
  --dashboard-name "Django-App-Overview" \
  --dashboard-body file://dashboard.json
```

`dashboard.json`の例:
```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "CPUUtilization", "ServiceName", "django-app-service", "ClusterName", "django-ecs-cluster" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "ECS CPU Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ECS", "MemoryUtilization", "ServiceName", "django-app-service", "ClusterName", "django-ecs-cluster" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "ECS Memory Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", "app/django-alb/1234567890" ],
          [ ".", "HTTPCode_Target_4XX_Count", ".", "." ],
          [ ".", "HTTPCode_Target_5XX_Count", ".", "." ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "ALB Response Codes",
        "period": 300,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/django-alb/1234567890" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "ALB Response Time",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "django-db" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "RDS CPU Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "django-db" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "ap-northeast-1",
        "title": "RDS Connections",
        "period": 300,
        "stat": "Average"
      }
    }
  ]
}
```

### カスタムダッシュボードツール

より高度な監視ダッシュボードには以下のサービスも検討できます：

- **Grafana**: より詳細なダッシュボードを作成可能
- **Datadog**: APM機能を含む包括的なモニタリング
- **New Relic**: アプリケーションパフォーマンスに特化したモニタリング

## 定期メンテナンスとレビュー

モニタリング設定は定期的に見直し、以下の点を確認してください：

1. アラートの適切性（誤検知が多くないか）
2. しきい値の適切性（サービスの成長に合わせて調整）
3. 監視対象の過不足（新機能に対応した監視の追加）
4. 障害対応プロセスの有効性

推奨レビュー頻度: 四半期ごと 
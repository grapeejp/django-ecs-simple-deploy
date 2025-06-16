# 明日の作業（6月17日）

## 🚨 優先度：高 - ステージング環境Google OAuth設定問題の解決

### 📋 問題の概要
- **現象**: ステージング環境でGoogle OAuth認証が失敗
- **エラー**: `SocialApp for provider 'google' not found`
- **原因**: ステージング環境のデータベースにGoogle SocialApp設定が存在しない
- **コールバックURI**: `http://staging.grape-app.jp/accounts/google/login/callback/` （正しい）

### 🔧 解決手順

#### 1. Google Cloud Console設定確認
- [ ] Google Cloud Consoleにアクセス
- [ ] OAuth 2.0 クライアントIDの設定確認
- [ ] 承認済みリダイレクトURIに以下が含まれているか確認：
  ```
  http://localhost:8000/accounts/google/login/callback/
  http://staging.grape-app.jp/accounts/google/login/callback/
  ```
- [ ] OAuth同意画面が「内部（Internal）」に設定されているか確認
- [ ] ドメイン制限（`@grapee.co.jp`）が有効か確認

#### 2. 認証情報の取得
- [ ] Google OAuth Client ID をコピー
- [ ] Google OAuth Client Secret をコピー

#### 3. ステージング環境への設定適用

**方法A: ECSタスク定義の環境変数更新（推奨）**
```bash
# 現在のタスク定義を取得
aws ecs describe-task-definition --task-definition django-app-staging-simple --output json > current_task_def.json

# 環境変数にGoogle OAuth設定を追加
# GOOGLE_OAUTH_CLIENT_ID=<取得したClient ID>
# GOOGLE_OAUTH_CLIENT_SECRET=<取得したClient Secret>

# 新しいタスク定義を登録
aws ecs register-task-definition --cli-input-json file://updated_task_def.json

# ECSサービスを更新
aws ecs update-service --cluster django-ecs-cluster-staging --service django-ecs-service-staging-simple --task-definition django-app-staging-simple:<新しいリビジョン>
```

**方法B: ECS Execを使用した直接設定**
```bash
# 実行中のタスクIDを取得
aws ecs list-tasks --cluster django-ecs-cluster-staging --service-name django-ecs-service-staging-simple

# ECS Execでコンテナに接続
aws ecs execute-command --cluster django-ecs-cluster-staging --task <TASK_ID> --container django-app --interactive --command "/bin/bash"

# コンテナ内で管理コマンドを実行
export GOOGLE_OAUTH_CLIENT_ID="<取得したClient ID>"
export GOOGLE_OAUTH_CLIENT_SECRET="<取得したClient Secret>"
python manage.py setup_google_oauth --site-domain staging.grape-app.jp
```

#### 4. 動作確認
- [ ] ステージング環境にアクセス: `http://staging.grape-app.jp/`
- [ ] 「Google Workspaceでログイン」ボタンをクリック
- [ ] Google認証画面が正常に表示されるか確認
- [ ] `@grapee.co.jp`アカウントでログイン試行
- [ ] ダッシュボードにリダイレクトされるか確認

#### 5. トラブルシューティング

**ログ確認コマンド:**
```bash
# ステージング環境のログ確認
aws logs filter-log-events --log-group-name "/ecs/django-app-staging-simple" --start-time $(($(date +%s) - 600))000 --filter-pattern "google"

# エラーログ確認
aws logs filter-log-events --log-group-name "/ecs/django-app-staging-simple" --start-time $(($(date +%s) - 600))000 --filter-pattern "ERROR"
```

**よくある問題と解決策:**
- **redirect_uri_mismatch**: Google Cloud ConsoleのリダイレクトURI設定を確認
- **ドメイン制限エラー**: OAuth同意画面の設定とアダプターの`hd`パラメータを確認
- **SocialApp not found**: データベースの設定が正しく保存されているか確認

### 📝 参考情報

**関連ファイル:**
- `app/core/management/commands/setup_google_oauth.py` - OAuth設定管理コマンド
- `app/core/adapters.py` - ドメイン制限アダプター
- `app/config/settings.py` - OAuth設定
- `docs/google_oauth_setup.md` - 詳細な設定手順

**現在の設定状況:**
- ローカル環境: Google OAuth正常動作
- ステージング環境: SocialApp未設定（要対応）
- コールバックURI: 正しく設定済み

### ⏰ 予想作業時間
- Google Cloud Console確認: 15分
- ステージング環境設定: 30分
- 動作確認・テスト: 15分
- **合計: 約1時間**

### ✅ 完了条件
- [ ] ステージング環境でGoogle OAuth認証が正常に動作する
- [ ] `@grapee.co.jp`アカウントでログイン・ダッシュボードアクセスが可能
- [ ] エラーログにOAuth関連のエラーが出力されない

# 6月17日（月）の作業予定

## 🚨 現状の問題点

### 1. Google OAuth認証エラー（最優先）
- **症状**: ステージング環境で「外部アカウントによるログインに失敗しました」エラー
- **根本原因**: ステージング環境のデータベースにGoogle SocialAppの設定が存在しない
- **エラーログ**: `SocialApp for provider 'google' not found`
- **影響**: ユーザーがGoogle認証でログインできない状態

### 2. セキュリティ問題
- **HTTP通信**: 現在ステージング環境はHTTPのみ（http://staging.grape-app.jp）
- **認証情報の平文送信**: OAuth認証時の機密情報が暗号化されていない
- **本番運用不可**: HTTPSなしでは本番環境として使用できない

### 3. 設定の不整合
- **ローカル環境**: Google OAuth正常動作（localhost:8000とstaging.grape-app.jpの両方に対応）
- **ステージング環境**: データベース設定が不完全
- **環境間の差異**: 本番デプロイ時に同様の問題が発生する可能性

## 📋 作業計画

### Phase 1: Google OAuth認証修正（優先度：高）
**予想作業時間**: 1時間

#### 1.1 Google Cloud Console設定確認
- [ ] OAuth 2.0クライアントIDの設定確認
- [ ] 承認済みリダイレクトURIの確認
  - `http://staging.grape-app.jp/accounts/google/login/callback/`
  - `https://staging.grape-app.jp/accounts/google/login/callback/` （HTTPS化後用）
- [ ] クライアントIDとシークレットの取得

#### 1.2 ステージング環境への設定適用
**方法A: ECSタスク定義での環境変数設定（推奨）**
```bash
# 新しいタスク定義リビジョンを作成
aws ecs register-task-definition \
  --family django-app-staging-simple \
  --task-definition-arn <現在のタスク定義ARN> \
  --container-definitions '[
    {
      "name": "django-app",
      "environment": [
        {"name": "GOOGLE_OAUTH_CLIENT_ID", "value": "<CLIENT_ID>"},
        {"name": "GOOGLE_OAUTH_CLIENT_SECRET", "value": "<CLIENT_SECRET>"}
      ]
    }
  ]'
```

**方法B: ECS Execでの直接設定**
```bash
# ECSタスクに接続してDjangoシェルで設定
aws ecs execute-command \
  --cluster django-ecs-cluster-staging \
  --task <TASK_ID> \
  --container django-app \
  --interactive \
  --command "/bin/bash"

# コンテナ内でDjangoシェル実行
python manage.py shell
```

#### 1.3 動作確認
- [ ] ステージング環境でGoogle OAuth認証テスト
- [ ] ログイン・ログアウトの動作確認
- [ ] CloudWatchログでエラーがないことを確認

### Phase 2: HTTPS化対応（優先度：高）
**予想作業時間**: 2-3時間

#### 2.1 SSL証明書の取得
```bash
# AWS Certificate Manager (ACM) で証明書リクエスト
aws acm request-certificate \
  --domain-name staging.grape-app.jp \
  --validation-method DNS \
  --region ap-northeast-1
```

#### 2.2 ALB設定の更新
- [ ] HTTPS リスナー（ポート443）の追加
- [ ] SSL証明書のALBへの関連付け
- [ ] HTTP→HTTPSリダイレクトの設定
- [ ] セキュリティポリシーの設定

#### 2.3 CloudFormationテンプレート更新
```yaml
# ALBにHTTPSリスナー追加
HTTPSListener:
  Type: AWS::ElasticLoadBalancingV2::Listener
  Properties:
    LoadBalancerArn: !Ref ApplicationLoadBalancer
    Port: 443
    Protocol: HTTPS
    Certificates:
      - CertificateArn: !Ref SSLCertificate
    DefaultActions:
      - Type: forward
        TargetGroupArn: !Ref TargetGroup

# HTTP→HTTPSリダイレクト
HTTPRedirectListener:
  Type: AWS::ElasticLoadBalancingV2::Listener
  Properties:
    LoadBalancerArn: !Ref ApplicationLoadBalancer
    Port: 80
    Protocol: HTTP
    DefaultActions:
      - Type: redirect
        RedirectConfig:
          Protocol: HTTPS
          Port: 443
          StatusCode: HTTP_301
```

#### 2.4 Django設定の更新
```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 2.5 Google OAuth設定の更新
- [ ] Google Cloud ConsoleでHTTPS URLを追加
- [ ] リダイレクトURIを`https://staging.grape-app.jp/accounts/google/login/callback/`に更新

### Phase 3: 本番環境準備（優先度：中）
**予想作業時間**: 1時間

#### 3.1 本番用ドメイン設定
- [ ] `grape-app.jp`と`www.grape-app.jp`の証明書取得
- [ ] 本番用CloudFormationテンプレート作成
- [ ] 本番用Google OAuth設定

#### 3.2 環境分離の強化
- [ ] 本番とステージングの完全分離
- [ ] 環境変数による設定の切り替え
- [ ] データベースの分離確認

## 🔧 トラブルシューティング準備

### よくある問題と対処法
1. **証明書検証エラー**: DNS検証レコードの設定確認
2. **HTTPS接続エラー**: セキュリティグループのポート443開放確認
3. **OAuth認証エラー**: リダイレクトURIの完全一致確認
4. **Mixed Content警告**: 静的ファイルのHTTPS配信確認

### 緊急時のロールバック手順
```bash
# 問題発生時は前のタスク定義リビジョンに戻す
aws ecs update-service \
  --cluster django-ecs-cluster-staging \
  --service django-ecs-service-staging-simple \
  --task-definition django-app-staging-simple:<前のリビジョン番号>
```

## 📊 成功指標

### Phase 1完了時
- [ ] ステージング環境でGoogle OAuth認証が正常動作
- [ ] エラーログにSocialApp関連エラーが出ない
- [ ] ユーザーがGoogle認証でログイン・ログアウト可能

### Phase 2完了時
- [ ] `https://staging.grape-app.jp`でアクセス可能
- [ ] HTTP→HTTPSの自動リダイレクト動作
- [ ] SSL証明書が有効（ブラウザで警告なし）
- [ ] Google OAuth認証がHTTPS環境で正常動作

### Phase 3完了時
- [ ] 本番環境のHTTPS設定完了
- [ ] 本番・ステージング環境の完全分離
- [ ] 本番デプロイの準備完了

## ⚠️ 注意事項

1. **作業順序**: OAuth修正→HTTPS化の順番で実施（HTTPSでOAuth設定変更が必要なため）
2. **ダウンタイム**: HTTPS化時に一時的なサービス停止の可能性
3. **DNS伝播**: 証明書検証とDNS変更に最大48時間かかる場合がある
4. **バックアップ**: 作業前に現在の設定をバックアップ
5. **テスト**: 各フェーズ完了後に必ず動作確認を実施

## 📞 エスカレーション

問題発生時の連絡先と対応手順を事前に確認しておく。
- AWS サポート（必要に応じて）
- Google Cloud サポート（OAuth関連）
- DNS設定の管理者

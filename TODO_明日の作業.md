# 📋 明日の作業TODO (2025/05/31)

## 🔥 最優先作業

### 1. 新機能の本番デプロイ ⚡
**状況**: 辞書表示機能＆HTMLタグ修正機能がmainブランチにマージ済みだが、本番環境にデプロイ未完了

**必要な作業**:
```bash
# 1. Dockerイメージのビルド・プッシュ
docker build --platform=linux/amd64 -t django-ecs-app:latest .
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin 026090540679.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag django-ecs-app:latest 026090540679.dkr.ecr.ap-northeast-1.amazonaws.com/django-ecs-app:latest
docker push 026090540679.dkr.ecr.ap-northeast-1.amazonaws.com/django-ecs-app:latest

# 2. ECSサービスの更新（新しいタスク定義で再デプロイ）
aws ecs update-service --cluster django-ecs-cluster-production --service django-ecs-service-production --force-new-deployment
```

**期待される結果**:
- 辞書表示機能が本番で利用可能
- HTMLタグ修正機能が本番で動作
- ユーザーが「📖 辞書ルールを確認」ボタンでCSVデータを閲覧可能

---

## 📝 新規機能開発

### 2. チャットワークエラー報告機能の実装
**Issue**: #44
**概要**: 校正処理でエラーが発生した際に自動でチャットワークに通知

**作業ステップ**:
1. 新しいfeatureブランチ作成: `feature/chatwork-error-notification`
2. チャットワークAPI設定
3. エラー通知サービスクラス作成
4. 既存のエラーハンドリングに通知機能統合
5. 環境変数設定（本番・ステージング）

**技術要件**:
- チャットワークAPI v2使用
- 環境変数: `CHATWORK_API_TOKEN`, `CHATWORK_ROOM_ID`
- エラーレベル: ERROR, WARNING, INFO

---

## 🏗️ インフラ作業

### 3. ECSドメイン差し替え作業
**Issue**: #45
**概要**: 現在のECSアプリケーションのドメインを新しいドメインに変更

**事前準備**:
- 新ドメインの確認
- SSL証明書の準備状況確認
- ダウンタイム許容時間の確認

**作業ステップ**:
1. CloudFormationテンプレート更新
2. ステージング環境での事前テスト
3. 本番環境でのドメイン切り替え
4. 動作確認・監視

---

## 🧹 メンテナンス作業

### 4. 設定ファイルの整理
```bash
# コミットされていない変更をコミット
git add issue_template.txt
git commit -m "docs: issue テンプレートを更新"
git push origin main
```

### 5. 本番環境の動作確認
- 502エラーが解消されているか確認
- 新機能デプロイ後の動作テスト
- CloudWatchログの確認

---

## 📊 進捗状況

### ✅ 完了済み
- [x] ブランチ整理（18個のブランチ削除）
- [x] 開発サーバー整理（重複プロセス停止）
- [x] 辞書表示機能の実装・マージ
- [x] HTMLタグ修正機能の実装・マージ
- [x] 502エラー修正（インフラ側）

### 🔄 作業中
- [ ] 新機能の本番デプロイ ← **明日最優先**

### 📋 作業待ち
- [ ] チャットワークエラー報告機能
- [ ] ECSドメイン差し替え作業

---

## 📞 緊急時の連絡先・参考情報

**AWS環境**:
- 本番クラスター: `django-ecs-cluster-production`
- 本番サービス: `django-ecs-service-production`
- 現在のタスク定義: `django-app:7`

**GitHubリポジトリ**: `grapeejp/django-ecs-simple-deploy`

**重要なファイル**:
- `docker/Dockerfile` - Dockerイメージ設定
- `cloudformation/ecs-cluster.yml` - インフラ設定
- `app/proofreading_ai/views.py` - 辞書表示機能
- `app/proofreading_ai/services/bedrock_client.py` - HTMLタグ修正機能

---

**作業開始時の最初のコマンド**:
```bash
cd /Users/yanagimotoyasutoshi/Desktop/django-ecs-simple-deploy
git status
git pull origin main
```

お疲れ様でした！🎉 
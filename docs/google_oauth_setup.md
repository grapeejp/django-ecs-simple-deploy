# Google Workspace OAuth設定手順

## 概要
グレイプ社内ツールでは、@grapee.jpドメインのGoogle Workspaceアカウントのみでのログインを実装しています。

## 1. Google Cloud Console設定

### 1.1 プロジェクト作成・選択
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択

### 1.2 OAuth 2.0 認証情報の作成
1. **API とサービス** → **認証情報** に移動
2. **+ 認証情報を作成** → **OAuth 2.0 クライアント ID**
3. アプリケーションの種類: **ウェブアプリケーション**
4. 名前: `グレイプ社内ツール`
5. **承認済みのリダイレクト URI** に以下を追加：
   - 本番環境: `https://your-domain.com/accounts/google/login/callback/`
   - 開発環境: `http://localhost:8000/accounts/google/login/callback/`

### 1.3 Google Workspace ドメイン制限設定
1. **OAuth同意画面** に移動
2. **Internal** (内部) を選択（Google Workspaceアカウント必須）
3. アプリ情報を入力：
   - アプリ名: `グレイプ社内効率化ツール`
   - ユーザーサポートメール: `it@grapee.jp`
   - デベロッパー連絡先情報: `it@grapee.jp`

## 2. Django設定

### 2.1 環境変数設定
`.env`ファイルに以下を追加：

```bash
# Google Workspace OAuth設定
GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id-here
GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret-here
```

### 2.2 ドメイン制限の仕組み
- **hd パラメータ**: `grapee.jp` を指定してGoogle Workspaceドメインを制限
- **カスタムアダプター**: `GrapeeWorkspaceAdapter` で二重チェック
- **自動拒否**: @grapee.jp以外のアカウントは自動的にログイン拒否

## 3. 使用方法

### 3.1 ログインフロー
1. ユーザーが「Google Workspace でログイン」ボタンをクリック
2. Googleの認証画面で@grapee.jpアカウントを選択
3. ドメインチェック通過後、自動でアカウント作成・ログイン
4. ダッシュボードにリダイレクト

### 3.2 セキュリティ機能
- **ドメイン制限**: @grapee.jp以外は完全ブロック
- **自動アカウント作成**: 承認されたドメインのみ
- **新規登録無効**: 社内メンバーのみアクセス可能

## 4. トラブルシューティング

### 4.1 よくある問題
- **「アクセスがブロックされました」**: OAuth同意画面が外部設定になっている
- **「ドメインエラー」**: hd パラメータの設定確認
- **「認証情報エラー」**: CLIENT_ID/SECRET の設定確認

### 4.2 ログ確認
```bash
# Django開発サーバーのログでエラー確認
cd app && python manage.py runserver
```

## 5. 本番環境への適用

### 5.1 環境変数設定
```bash
# 本番環境の環境変数
export GOOGLE_OAUTH_CLIENT_ID="production-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="production-client-secret"
```

### 5.2 ドメイン設定更新
- ALLOWED_HOSTS に本番ドメインを追加
- OAuth リダイレクト URI を本番URL に設定

## 6. 管理者向け

### 6.1 新しいメンバーの追加
- Google Workspace管理者がアカウント作成
- 自動的にツールへのアクセス権限付与

### 6.2 アクセス制御
- Google Workspace側でアカウント無効化 → 自動的にツールアクセスも無効
- きめ細かい権限制御はDjango側で実装 
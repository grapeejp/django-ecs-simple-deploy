# TODO: 明日の作業 - 2025年6月18日

## 🚨 優先度：高 - 無限リロード問題の最終解決

### 1. 認証システムの安定化
- [ ] **auth-check.jsの段階的復活**
  - 現在：完全無効化済み ✅
  - 目標：適切な条件でのみ動作するよう修正
  - 実装：ページロード時の認証チェック頻度制限
  
- [ ] **セッション管理の最適化**
  - Django設定の最終調整
  - セッション有効期限の適切な設定
  - Cookie設定の確認

### 2. 校正AI機能のテスト
- [ ] **安定したローカル環境でのテスト**
  - ログイン → 校正AIページアクセス
  - テキスト入力 → 校正実行
  - 履歴機能の確認
  - 辞書管理機能の確認

- [ ] **校正AI機能の詳細確認**
  - Bedrock連携の動作確認
  - エラーハンドリングの確認
  - レスポンス速度の測定

### 3. ステージング環境への反映
- [ ] **修正のステージングデプロイ**
  - Dockerイメージビルド
  - ECSタスク定義更新
  - サービス更新
  - 動作確認

- [ ] **本番環境準備**
  - 本番用の設定確認
  - セキュリティ設定の最終チェック

## 📝 技術的な検討事項

### A. auth-check.js復活戦略
```javascript
// 修正案：適切な制限付きで復活
document.addEventListener('DOMContentLoaded', function() {
    // ログインページでは実行しない
    if (window.location.pathname.includes('/accounts/login/')) return;
    
    // 認証チェックは最大5回まで
    let checkCount = 0;
    const maxChecks = 5;
    
    function checkAuth() {
        if (checkCount >= maxChecks) return;
        checkCount++;
        
        // 認証チェック実装...
    }
});
```

### B. セッション設定の最終版
```python
# settings.py 推奨設定
SESSION_SAVE_EVERY_REQUEST = False  # 重要：無限リロード防止
SESSION_COOKIE_AGE = 86400  # 24時間
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

## 🔧 デバッグ環境準備

### 推奨ローカル起動コマンド
```bash
# 安定版サーバー起動（リロード無効）
cd app && python manage.py runserver 127.0.0.1:8001 --noreload

# プロセス確認（重複チェック）
ps aux | grep "python.*runserver" | grep -v grep
```

### 校正AI機能テスト手順
1. demo1ユーザーでログイン（パスワード: grape2025demo）
2. `/proofreading_ai/` にアクセス
3. サンプルテキストで校正実行
4. 履歴ページ `/proofreading_ai/history/` 確認
5. 辞書機能 `/proofreading_ai/dictionary/` 確認

## ⚡ 完了した作業（確認済み）

- ✅ 無限リロード・リダイレクト問題の根本修正
- ✅ AllowedUserモデル属性参照エラー修正
- ✅ 複数プロセス重複実行問題の解決
- ✅ ログインページレイアウト修正
- ✅ HTTPS対応（ステージング環境）
- ✅ Google OAuth認証機能

## 🎯 最終目標

**安定したローカル環境 → 校正AI機能の完全動作確認 → ステージング環境での最終テスト**

---

*注意：明日の作業開始前に必ず `git pull origin main` で最新状態を確認すること*

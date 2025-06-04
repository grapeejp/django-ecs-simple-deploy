#!/bin/bash

echo "🚨 Basic認証テストを開始します..."

# テスト用のドメイン
STAGING_DOMAIN="staging.grape-app.jp"
PRODUCTION_DOMAIN="prod.grape-app.jp"

# 認証情報
STAGING_USER="grape"
STAGING_PASS="staging2024!"
PRODUCTION_USER="grape"
PRODUCTION_PASS="production2024!"

echo ""
echo "=== 🔴 認証なしアクセステスト（失敗するはず） ==="

echo "🚨 ステージング環境（認証なし）:"
curl -v -H "Host: $STAGING_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP|< WWW-Authenticate" || echo "エラー: アクセスできませんでした"

echo ""
echo "🚨 本番環境（認証なし）:"
curl -v -H "Host: $PRODUCTION_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP|< WWW-Authenticate" || echo "エラー: アクセスできませんでした"

echo ""
echo "=== ✅ 正しい認証情報でのアクセステスト（成功するはず） ==="

echo "🚨 ステージング環境（正しい認証）:"
curl -v -u "$STAGING_USER:$STAGING_PASS" -H "Host: $STAGING_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP" || echo "エラー: アクセスできませんでした"

echo ""
echo "🚨 本番環境（正しい認証）:"
curl -v -u "$PRODUCTION_USER:$PRODUCTION_PASS" -H "Host: $PRODUCTION_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP" || echo "エラー: アクセスできませんでした"

echo ""
echo "=== 🔴 間違った認証情報でのアクセステスト（失敗するはず） ==="

echo "🚨 ステージング環境（間違ったパスワード）:"
curl -v -u "$STAGING_USER:wrongpassword" -H "Host: $STAGING_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP" || echo "エラー: アクセスできませんでした"

echo ""
echo "🚨 本番環境（間違ったパスワード）:"
curl -v -u "$PRODUCTION_USER:wrongpassword" -H "Host: $PRODUCTION_DOMAIN" http://localhost/ 2>&1 | grep -E "< HTTP" || echo "エラー: アクセスできませんでした"

echo ""
echo "🚨 Basic認証テスト完了！"
echo ""
echo "期待される結果:"
echo "- 認証なし: HTTP/1.1 401 Unauthorized"
echo "- 正しい認証: HTTP/1.1 200 OK (またはDjangoからのレスポンス)"
echo "- 間違った認証: HTTP/1.1 401 Unauthorized" 
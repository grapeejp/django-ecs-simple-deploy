#!/usr/bin/env node

/**
 * Instagram #猫 人気投稿分析デモ
 * Claude MAX + MCP + Playwrightを使用
 */

require('dotenv').config();
const { automate } = require('../src/automation');

async function demoInstagram() {
  console.log('🐱 Instagram #猫 人気投稿分析を開始します...');
  
  try {
    const result = await automate(`
      MCPでPlaywrightを使って以下を実行してください：
      
      1. Instagramにアクセス
      2. #猫 のハッシュタグを検索
      3. 人気投稿上位5件を取得
      4. 以下の情報を抽出：
         - 投稿URL
         - 投稿者名
         - いいね数
         - 投稿内容（最初の50文字）
         - 投稿日
      5. ./output/instagram/demo-cats-${new Date().toISOString().split('T')[0]}.csvで保存
      
      ログイン情報は環境変数から取得してください。
    `);
    
    console.log('✅ Instagram分析完了！');
    console.log('📄 結果ファイル: ./output/instagram/demo-cats-*.csv');
    
  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
    process.exit(1);
  }
}

// スクリプトが直接実行された場合
if (require.main === module) {
  demoInstagram();
}

module.exports = { demoInstagram }; 
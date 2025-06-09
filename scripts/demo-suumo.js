#!/usr/bin/env node

/**
 * Suumo 横浜市2DK物件検索デモ
 * Claude MAX + MCP + Playwrightを使用
 */

require('dotenv').config();
const { automate } = require('../src/automation');

async function demoSuumo() {
  console.log('🏠 Suumo 横浜市2DK物件検索を開始します...');
  
  try {
    const result = await automate(`
      MCPでPlaywrightを使って以下を実行してください：
      
      1. Suumoにアクセス
      2. 神奈川県 > 横浜市で検索
      3. 2DK、2LDKの物件を検索
      4. 人気物件上位5件を取得
      5. 以下の情報を抽出：
         - 物件名
         - 家賃
         - 管理費
         - 間取り
         - 面積
         - 最寄り駅と徒歩分数
         - 築年数
         - URL
      6. ./output/reports/demo-yokohama-properties-${new Date().toISOString().split('T')[0]}.csvで保存
      
      二人暮らしに適した物件を優先してください。
    `);
    
    console.log('✅ Suumo検索完了！');
    console.log('📄 結果ファイル: ./output/reports/demo-yokohama-properties-*.csv');
    
  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
    process.exit(1);
  }
}

// スクリプトが直接実行された場合
if (require.main === module) {
  demoSuumo();
}

module.exports = { demoSuumo }; 
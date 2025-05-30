#!/usr/bin/env python3
"""
辞書ファイルの読み込みテスト
"""
import os
import csv

def test_dictionary_loading():
    # 相対パス（ビューと同じロジック）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'app', 'proofreading', 'replacement_dict.csv')
    
    print(f"📁 現在のディレクトリ: {current_dir}")
    print(f"📂 CSVファイルパス: {csv_path}")
    print(f"🔍 ファイル存在確認: {os.path.exists(csv_path)}")
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            entries = list(csv_reader)
            print(f"✅ 読み込み成功: {len(entries)}行")
            
            # カテゴリ別統計
            open_count = sum(1 for row in entries if len(row) > 2 and row[2] == '開く')
            close_count = sum(1 for row in entries if len(row) > 2 and row[2] == '閉じる')
            
            print(f"📊 統計:")
            print(f"  - 開く: {open_count}件")
            print(f"  - 閉じる: {close_count}件")
            print(f"  - 総計: {len(entries)}件")
            
            # 最初の5行を表示
            print(f"\n📝 サンプル（最初の5行）:")
            for i, row in enumerate(entries[:5], 1):
                if len(row) >= 3:
                    print(f"  {i}. {row[0]} → {row[1]} ({row[2]})")
    else:
        print("❌ ファイルが見つかりません")
        # 代替パスを試す
        alt_paths = [
            os.path.join(current_dir, 'app', 'proofreading_ai', 'replacement_dict.csv'),
            os.path.join(current_dir, 'replacement_dict.csv'),
            os.path.join(current_dir, '..', 'replacement_dict.csv')
        ]
        
        print("\n🔍 代替パス検索:")
        for alt_path in alt_paths:
            print(f"  {alt_path}: {os.path.exists(alt_path)}")

if __name__ == "__main__":
    test_dictionary_loading() 
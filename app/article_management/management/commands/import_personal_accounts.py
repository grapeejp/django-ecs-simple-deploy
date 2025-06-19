import csv
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from article_management.models import PersonalSNSAccount


class Command(BaseCommand):
    help = 'NG・条件付きユーザーとOKユーザーのCSVファイルをインポートします'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ng-csv',
            type=str,
            help='NG・条件付きユーザーのCSVファイルパス'
        )
        parser.add_argument(
            '--ok-csv',
            type=str,
            help='OKユーザーのCSVファイルパス'
        )
    
    def handle(self, *args, **options):
        if options['ng_csv']:
            self.import_ng_users(options['ng_csv'])
        
        if options['ok_csv']:
            self.import_ok_users(options['ok_csv'])
    
    def detect_platform(self, url):
        """URLからプラットフォームを判定"""
        if not url:
            return None
            
        url_lower = url.lower()
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'threads.com' in url_lower:
            return 'threads'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'blog' in url_lower or any(x in url_lower for x in ['.jp', '.com', 'ameblo']):
            return 'blog'
        return None
    
    def import_ng_users(self, csv_path):
        """NG・条件付きユーザーをインポート"""
        self.stdout.write('NG・条件付きユーザーのインポートを開始します...')
        
        imported = 0
        skipped = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # 空行やヘッダー行をスキップ
                if not row.get('ID　＠なしで入力') or row.get('ID　＠なしで入力').strip() == '':
                    continue
                
                handle_name = row.get('ID　＠なしで入力', '').strip()
                url = row.get('URL', '').strip()
                platform_str = row.get('メディア', '').strip()
                reason = row.get('理由', '').strip()
                ng_date = row.get('NGになった時期', '').strip()
                
                # プラットフォームを判定
                platform = self.detect_platform(url) if url else self.detect_platform(platform_str)
                if not platform:
                    if platform_str.lower() in ['twitter', 'instagram', 'tiktok', 'youtube']:
                        platform = platform_str.lower()
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'プラットフォームが判定できません: {handle_name}')
                        )
                        skipped += 1
                        continue
                
                # ステータスを判定
                status = 'ng'  # デフォルトはNG
                conditions = ''
                
                # 条件付きOKのパターンを検出
                if 'OK' in reason or '可能' in reason or 'のみ' in reason:
                    status = 'conditional'
                    conditions = reason
                    reason = ''
                
                # 既存チェック
                exists = PersonalSNSAccount.objects.filter(
                    handle_name=handle_name,
                    platform=platform
                ).exists()
                
                if exists:
                    self.stdout.write(
                        self.style.WARNING(f'既に存在: {handle_name} ({platform})')
                    )
                    skipped += 1
                    continue
                
                # 作成
                try:
                    PersonalSNSAccount.objects.create(
                        handle_name=handle_name,
                        platform=platform,
                        url=url,
                        status=status,
                        reason=reason,
                        conditions=conditions,
                        notes=ng_date if ng_date else ''
                    )
                    imported += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'インポート: {handle_name} ({platform}) - {status}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'エラー: {handle_name} - {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nNG・条件付きユーザー インポート完了: {imported}件追加、{skipped}件スキップ'
            )
        )
    
    def import_ok_users(self, csv_path):
        """OKユーザーをインポート"""
        self.stdout.write('\nOKユーザーのインポートを開始します...')
        
        imported = 0
        skipped = 0
        current_category = 'other'
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # カテゴリ行の検出
                account_name = row.get('アカウント名（1セル1ID）', '').strip()
                
                if not account_name:
                    continue
                    
                # カテゴリ判定
                if account_name in ['漫画ネタ', '動物ネタ', '芸能人', 'その他']:
                    category_map = {
                        '漫画ネタ': 'manga',
                        '動物ネタ': 'animal',
                        '芸能人': 'celebrity',
                        'その他': 'other'
                    }
                    current_category = category_map.get(account_name, 'other')
                    continue
                
                handle_name = account_name
                url = row.get('URL', '').strip()
                platform_str = row.get('メディア', '').strip()
                conditions = row.get('利用の条件', '').strip()
                
                # プラットフォームを判定
                platform = self.detect_platform(url) if url else self.detect_platform(platform_str)
                if not platform:
                    if platform_str.lower() in ['twitter', 'instagram', 'tiktok', 'youtube']:
                        platform = platform_str.lower()
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'プラットフォームが判定できません: {handle_name}')
                        )
                        skipped += 1
                        continue
                
                # 既存チェック
                exists = PersonalSNSAccount.objects.filter(
                    handle_name=handle_name,
                    platform=platform
                ).exists()
                
                if exists:
                    self.stdout.write(
                        self.style.WARNING(f'既に存在: {handle_name} ({platform})')
                    )
                    skipped += 1
                    continue
                
                # 作成
                try:
                    PersonalSNSAccount.objects.create(
                        handle_name=handle_name,
                        platform=platform,
                        url=url,
                        status='ok',
                        category=current_category,
                        conditions=conditions
                    )
                    imported += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'インポート: {handle_name} ({platform}) - OK')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'エラー: {handle_name} - {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nOKユーザー インポート完了: {imported}件追加、{skipped}件スキップ'
            )
        )
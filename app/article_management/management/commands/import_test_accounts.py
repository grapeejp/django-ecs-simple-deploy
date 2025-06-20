import csv
import codecs
from django.core.management.base import BaseCommand
from django.utils import timezone
from article_management.models import PersonalSNSAccount, CorporateSNSAccount


class Command(BaseCommand):
    help = 'CSVファイルからテストアカウントをインポート'
    
    def add_arguments(self, parser):
        parser.add_argument('--ok', action='store_true', help='OKユーザーをインポート')
        parser.add_argument('--ng', action='store_true', help='NG・条件付きユーザーをインポート')
    
    def handle(self, *args, **options):
        if options['ok']:
            self.import_ok_users()
        
        if options['ng']:
            self.import_ng_users()
        
        if not options['ok'] and not options['ng']:
            self.stdout.write(self.style.WARNING('--ok または --ng オプションを指定してください'))
    
    def import_ok_users(self):
        """OKユーザーをインポート"""
        file_path = '/Users/yanagimotoyasutoshi/Desktop/django-ecs-simple-deploy/app/article_management/sample_data/OKユーザー.csv'
        
        created_count = 0
        skipped_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # 空行やカテゴリ行をスキップ
                if not row.get('アカウント名（1セル1ID）') or row.get('アカウント名（1セル1ID）') in ['漫画ネタ', '動物ネタ', 'その他', '芸能人']:
                    continue
                
                name = row.get('アカウント名（1セル1ID）', '').strip()
                handle = row.get('メディア', '').strip()
                if not handle:  # メディア列が空の場合は、アカウント名を使用
                    handle = name
                platform = self.normalize_platform(row.get('URL', ''))
                url = row.get('URL', '').strip()
                conditions = row.get('利用の条件', '').strip()
                
                if not name:
                    continue
                
                # 個人アカウントとして登録
                try:
                    account, created = PersonalSNSAccount.objects.get_or_create(
                        handle_name=handle,
                        platform=platform,
                        defaults={
                            'real_name': name if handle != name else '',
                            'url': url,
                            'status': 'conditional' if conditions else 'ok',
                            'conditions': conditions,
                            'category': self.guess_category(name),
                            'notes': 'CSVからインポート（OKユーザー）'
                        }
                    )
                except Exception as e:
                    self.stdout.write(f'⚠️  エラー: {name} - {str(e)}')
                    continue
                
                if created:
                    created_count += 1
                    self.stdout.write(f'✅ 作成: {name} ({platform})')
                else:
                    skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nOKユーザーのインポート完了: {created_count}件作成, {skipped_count}件スキップ'
            )
        )
    
    def import_ng_users(self):
        """NG・条件付きユーザーをインポート"""
        file_path = '/Users/yanagimotoyasutoshi/Desktop/django-ecs-simple-deploy/app/article_management/sample_data/NG・条件付ユーザー.csv'
        
        created_count = 0
        skipped_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                # IDフィールドから取得
                handle = row.get('ID　＠なしで入力', '').strip()
                if not handle:
                    continue
                
                platform = self.normalize_platform(row.get('URL', ''))
                url = row.get('URL', '').strip()
                reason = row.get('理由', '').strip()
                ng_date = row.get('NGになった時期', '').strip()
                
                # 個人アカウントとして登録
                account, created = PersonalSNSAccount.objects.get_or_create(
                    handle_name=handle,
                    platform=platform,
                    defaults={
                        'url': url,
                        'status': 'ng',
                        'reason': reason,
                        'notes': f'CSVからインポート（NG・条件付きユーザー）\nNG時期: {ng_date}' if ng_date else 'CSVからインポート（NG・条件付きユーザー）',
                        'category': 'other'
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'❌ 作成: {handle} ({platform}) - NG理由: {reason[:50]}...')
                else:
                    skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nNG・条件付きユーザーのインポート完了: {created_count}件作成, {skipped_count}件スキップ'
            )
        )
    
    def normalize_platform(self, url):
        """URLからプラットフォームを判定"""
        if not url:
            return 'twitter'  # デフォルト
        
        url_lower = url.lower()
        if 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'threads.com' in url_lower:
            return 'threads'
        elif 'ameblo' in url_lower or 'blog' in url_lower:
            return 'blog'
        else:
            return 'website'
    
    def guess_category(self, name):
        """名前からカテゴリを推測"""
        if any(word in name for word in ['漫画', 'マンガ', 'コミック']):
            return 'manga'
        elif any(word in name for word in ['動物', '猫', '犬', 'ペット']):
            return 'animal'
        elif any(word in name for word in ['料理', 'レシピ', '食']):
            return 'cooking'
        elif any(word in name for word in ['育児', '子育て', 'ママ', 'パパ']):
            return 'parenting'
        elif any(word in name for word in ['芸能', 'タレント', '俳優', '女優']):
            return 'celebrity'
        else:
            return 'other'
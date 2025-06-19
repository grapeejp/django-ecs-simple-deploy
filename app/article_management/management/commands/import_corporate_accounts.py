import csv
import re
from django.core.management.base import BaseCommand
from article_management.models import CorporateSNSAccount


class Command(BaseCommand):
    help = 'ライフ系アカウント一覧CSVファイルをインポートします'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            required=True,
            help='ライフ系アカウント一覧のCSVファイルパス'
        )
    
    def handle(self, *args, **options):
        csv_path = options['csv']
        self.import_corporate_accounts(csv_path)
    
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
        else:
            return 'website'
    
    def parse_status(self, status_str):
        """ステータス文字列をパース"""
        if not status_str:
            return 'checking'
        
        status_lower = status_str.lower()
        if 'ok' in status_lower:
            return 'ok'
        elif 'ng' in status_lower:
            return 'ng'
        else:
            return 'checking'
    
    def parse_conditions(self, notes):
        """備考から利用条件を抽出"""
        conditions = {
            'require_prior_approval': False,
            'require_post_report': False,
            'embed_only': False,
            'allow_image_download': True,
            'allow_screenshot': True,
            'credit_format': '',
            'excluded_content': '',
            'special_conditions': ''
        }
        
        if not notes:
            return conditions
        
        notes_lower = notes.lower()
        
        # 事前確認
        if '事前確認' in notes or '事前に' in notes:
            conditions['require_prior_approval'] = True
        
        # 事後報告
        if '事後報告' in notes or '掲載後' in notes or '公開後' in notes:
            conditions['require_post_report'] = True
        
        # 埋め込みのみ
        if '埋め込みのみ' in notes or '埋め込み必須' in notes:
            conditions['embed_only'] = True
        
        # 画像使用
        if 'dl不可' in notes_lower or 'ダウンロード不可' in notes:
            conditions['allow_image_download'] = False
        if 'スクショ不可' in notes or 'スクリーンショット不可' in notes:
            conditions['allow_screenshot'] = False
        
        # クレジット表記
        credit_match = re.search(r'出典[:：]([^。\n]+)', notes)
        if credit_match:
            conditions['credit_format'] = credit_match.group(1).strip()
        
        # 特殊条件
        conditions['special_conditions'] = notes
        
        return conditions
    
    def import_corporate_accounts(self, csv_path):
        """企業アカウントをインポート"""
        self.stdout.write('企業アカウントのインポートを開始します...')
        
        imported = 0
        skipped = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            # 最初の行（タイトル行）をスキップ
            next(file)
            reader = csv.DictReader(file)
            
            for row in reader:
                # 企業名とアカウント名を取得
                company_name = row.get('企業名（運営名）', '').strip()
                account_name = row.get('アカウント名', '').strip()
                url = row.get('URL', '').strip()
                
                if not company_name or not account_name:
                    continue
                
                # URLが複数ある場合は改行で分割
                urls = [u.strip() for u in url.split('\n') if u.strip()]
                
                for single_url in urls:
                    platform = self.detect_platform(single_url)
                    if not platform:
                        continue
                    
                    # ステータスを取得
                    sales_status = self.parse_status(row.get('ステータス（営業）', ''))
                    editorial_status = self.parse_status(row.get('ステータス（編集）', ''))
                    
                    # 備考から条件を抽出
                    notes = row.get('補足（PR会社情報等）', '')
                    conditions = self.parse_conditions(notes)
                    
                    # 既存チェック
                    exists = CorporateSNSAccount.objects.filter(
                        company_name=company_name,
                        account_name=account_name,
                        platform=platform
                    ).exists()
                    
                    if exists:
                        self.stdout.write(
                            self.style.WARNING(
                                f'既に存在: {company_name} - {account_name} ({platform})'
                            )
                        )
                        skipped += 1
                        continue
                    
                    # 連絡先情報を整理
                    primary_contact = ''
                    pr_agency = ''
                    
                    if notes:
                        # メールアドレスを抽出
                        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
                        emails = re.findall(email_pattern, notes)
                        if emails:
                            primary_contact = ', '.join(emails)
                        
                        # PR会社情報を抽出
                        if 'PR事務局' in notes or 'PR会社' in notes:
                            pr_agency = notes
                    
                    # 作成
                    try:
                        CorporateSNSAccount.objects.create(
                            company_name=company_name,
                            account_name=account_name,
                            platform=platform,
                            url=single_url,
                            sales_status=sales_status,
                            editorial_status=editorial_status,
                            require_prior_approval=conditions['require_prior_approval'],
                            require_post_report=conditions['require_post_report'],
                            embed_only=conditions['embed_only'],
                            allow_image_download=conditions['allow_image_download'],
                            allow_screenshot=conditions['allow_screenshot'],
                            credit_format=conditions['credit_format'],
                            excluded_content=conditions['excluded_content'],
                            special_conditions=conditions['special_conditions'],
                            primary_contact=primary_contact if primary_contact else '要確認',
                            pr_agency=pr_agency,
                            notes=notes
                        )
                        imported += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'インポート: {company_name} - {account_name} ({platform})'
                            )
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'エラー: {company_name} - {account_name} - {str(e)}'
                            )
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n企業アカウント インポート完了: {imported}件追加、{skipped}件スキップ'
            )
        )
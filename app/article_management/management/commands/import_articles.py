import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from article_management.models import Article

User = get_user_model()


class Command(BaseCommand):
    help = 'CSVファイルから記事データをインポートします'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='article_management/sample_data/記事一覧サンプルデータ.csv',
            help='CSVファイルのパス'
        )

    def handle(self, *args, **options):
        csv_path = options['csv']
        
        # デフォルトユーザーを取得または作成
        default_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com'}
        )
        
        # ステータスマッピング
        status_map = {
            '申請中': 'pending',
            'スルー': 'through',
            '掲載NG': 'ng',
            '要許可': 'need_permission',
            '申請不要': 'no_apply',
            '': 'unknown',
        }
        
        imported = 0
        skipped = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                article_id = row.get('記事番号', '').strip()
                
                # 記事番号が空の場合はスキップ
                if not article_id:
                    continue
                
                # 既存の記事がある場合はスキップ
                if Article.objects.filter(article_id=article_id).exists():
                    self.stdout.write(
                        self.style.WARNING(f'記事 {article_id} は既に存在します。スキップします。')
                    )
                    skipped += 1
                    continue
                
                # ステータスを変換
                status = status_map.get(row.get('ステータス', ''), 'unknown')
                
                # 申請日から日付を抽出（例: "5/1野上" → 申請者: 野上）
                application_info = row.get('申請日', '')
                applicant_name = None
                if application_info:
                    # 日付部分を除去して申請者名を取得
                    parts = application_info.split('/')
                    if len(parts) >= 2:
                        # "5/1野上" のような形式から "野上" を抽出
                        name_part = parts[1]
                        for i, char in enumerate(name_part):
                            if not char.isdigit():
                                applicant_name = name_part[i:].strip()
                                break
                
                # 申請者を取得または作成
                if applicant_name:
                    applicant, _ = User.objects.get_or_create(
                        username=applicant_name,
                        defaults={'email': f'{applicant_name}@grapee.jp'}
                    )
                else:
                    applicant = default_user
                
                # ライターを取得または作成
                writer_name = row.get('ライター', '').strip()
                if writer_name:
                    writer, _ = User.objects.get_or_create(
                        username=writer_name,
                        defaults={'email': f'{writer_name}@grapee.jp'}
                    )
                else:
                    writer = None
                
                # 記事を作成
                try:
                    article = Article.objects.create(
                        article_id=article_id,
                        status=status,
                        applicant=applicant,
                        writer=writer,
                        title=row.get('内容', '')[:50] + '...' if len(row.get('内容', '')) > 50 else row.get('内容', ''),
                        content=row.get('内容', ''),
                        reference_url=row.get('記事URL', ''),
                        social_media_id=row.get('ID（IGは手打ち）', ''),
                    )
                    imported += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'記事 {article_id} をインポートしました')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'記事 {article_id} のインポートに失敗しました: {str(e)}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nインポート完了: {imported}件の記事をインポート、{skipped}件をスキップしました'
            )
        )
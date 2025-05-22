from django.core.management.base import BaseCommand
from grapecheck.models import Category

class Command(BaseCommand):
    help = 'グレイプのカテゴリデータを作成します'

    def handle(self, *args, **options):
        # メインカテゴリの作成
        main_categories = [
            {"name": "トレンド", "slug": "trend"},
            {"name": "ライフスタイル", "slug": "lifestyle"},
            {"name": "ビューティ", "slug": "beauty"},
            {"name": "エンタメ", "slug": "entertainment"},
            {"name": "サブカル", "slug": "subculture"},
            {"name": "社会", "slug": "society"},
            {"name": "特集・連載", "slug": "special"},
            {"name": "SDGs", "slug": "sdgs"},
        ]
        
        # サブカテゴリの定義
        subcategories = {
            "trend": [
                {"name": "おもしろ", "slug": "humor"},
                {"name": "動物", "slug": "animal"},
                {"name": "写真・アート", "slug": "photo-art"},
                {"name": "ストーリー", "slug": "story"},
            ],
            "lifestyle": [
                {"name": "育児・子育て", "slug": "parenting"},
                {"name": "フード", "slug": "food"},
                {"name": "ライフハック", "slug": "lifehack"},
                {"name": "話題の商品", "slug": "trending-products"},
                {"name": "ヘルスケア", "slug": "healthcare"},
                {"name": "ファッション", "slug": "fashion"},
            ],
            "beauty": [
                {"name": "メイク・コスメ", "slug": "makeup-cosmetics"},
            ],
            "entertainment": [
                {"name": "芸能", "slug": "celebrity"},
                {"name": "テレビ・ラジオ", "slug": "tv-radio"},
                {"name": "映画・ドラマ", "slug": "movie-drama"},
                {"name": "ブック", "slug": "book"},
                {"name": "音楽", "slug": "music"},
                {"name": "動画配信サービス", "slug": "streaming"},
            ],
            "subculture": [
                {"name": "漫画", "slug": "manga"},
                {"name": "アニメ", "slug": "anime"},
                {"name": "ゲーム", "slug": "game"},
            ],
            "society": [
                {"name": "ニュース", "slug": "news"},
                {"name": "スポーツ", "slug": "sports"},
                {"name": "科学・天体", "slug": "science"},
            ],
        }
        
        # メインカテゴリの作成
        created_main = 0
        for cat_data in main_categories:
            cat, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={"name": cat_data["name"]}
            )
            if created:
                created_main += 1
        
        # サブカテゴリの作成
        created_sub = 0
        for parent_slug, sub_list in subcategories.items():
            try:
                parent = Category.objects.get(slug=parent_slug)
                for sub_data in sub_list:
                    sub, created = Category.objects.get_or_create(
                        slug=sub_data["slug"],
                        defaults={
                            "name": sub_data["name"],
                            "parent": parent
                        }
                    )
                    if created:
                        created_sub += 1
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'親カテゴリ"{parent_slug}"が見つかりません'))
        
        self.stdout.write(
            self.style.SUCCESS(f'作成完了: {created_main}個のメインカテゴリと{created_sub}個のサブカテゴリ')
        ) 
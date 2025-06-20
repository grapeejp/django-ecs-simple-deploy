from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from article_management.models import Article


class Command(BaseCommand):
    help = '全記事に公開日（申請日+2-3日）のダミーデータを設定'

    def handle(self, *args, **options):
        articles = Article.objects.filter(published_at__isnull=True)
        updated_count = 0
        
        for article in articles:
            # 申請日から2-3日後をランダムに設定
            days_to_add = random.randint(2, 3)
            published_date = article.created_at + timedelta(days=days_to_add)
            
            article.published_at = published_date
            article.save(update_fields=['published_at'])
            updated_count += 1
            
            self.stdout.write(
                f'記事 {article.article_id}: '
                f'申請日 {article.created_at.date()} → '
                f'公開日 {published_date.date()} ({days_to_add}日後)'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {updated_count}件の記事に公開日を設定しました。'
            )
        )
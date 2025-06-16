from django.core.management.base import BaseCommand, CommandError
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Google OAuth SocialAppを設定します'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=str, help='Google OAuth クライアントID')
        parser.add_argument('--client-secret', type=str, help='Google OAuth クライアントシークレット')
        parser.add_argument('--site-domain', type=str, default='staging.grape-app.jp', help='サイトドメイン')
        parser.add_argument('--update', action='store_true', help='既存設定を更新')

    def handle(self, *args, **options):
        client_id = options['client_id'] or os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = options['client_secret'] or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        site_domain = options['site_domain']
        update = options['update']

        if not client_id:
            raise CommandError('Google OAuth クライアントIDが必要です。--client-id オプションまたは GOOGLE_OAUTH_CLIENT_ID 環境変数を設定してください。')

        if not client_secret:
            raise CommandError('Google OAuth クライアントシークレットが必要です。--client-secret オプションまたは GOOGLE_OAUTH_CLIENT_SECRET 環境変数を設定してください。')

        # サイトを取得または作成
        site, site_created = Site.objects.get_or_create(
            domain=site_domain,
            defaults={'name': f'Site for {site_domain}'}
        )
        
        if site_created:
            self.stdout.write(
                self.style.SUCCESS(f'新しいサイトを作成しました: {site_domain}')
            )
        else:
            self.stdout.write(f'既存サイトを使用: {site_domain}')

        # Google SocialAppを取得または作成
        try:
            social_app = SocialApp.objects.get(provider='google')
            if update:
                social_app.client_id = client_id
                social_app.secret = client_secret
                social_app.save()
                self.stdout.write(
                    self.style.SUCCESS('既存のGoogle SocialAppを更新しました。')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Google SocialAppは既に存在します。更新するには --update オプションを使用してください。')
                )
                return
        except SocialApp.DoesNotExist:
            # 新規作成
            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=client_secret
            )
            self.stdout.write(
                self.style.SUCCESS('新しいGoogle SocialAppを作成しました。')
            )

        # サイトとの関連付け
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(f'SocialAppをサイト {site_domain} に関連付けました。')

        # 設定確認
        self.stdout.write('\n=== 設定確認 ===')
        self.stdout.write(f'プロバイダー: {social_app.provider}')
        self.stdout.write(f'名前: {social_app.name}')
        self.stdout.write(f'クライアントID: {social_app.client_id[:10]}...')
        self.stdout.write(f'シークレット設定済み: {"Yes" if social_app.secret else "No"}')
        self.stdout.write(f'関連サイト: {[site.domain for site in social_app.sites.all()]}')
        
        self.stdout.write(
            self.style.SUCCESS('\nGoogle OAuth設定が完了しました！')
        ) 
from django.core.management.base import BaseCommand, CommandError
from core.models import AllowedUser


class Command(BaseCommand):
    help = 'AllowedUserを追加または更新します'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='メールアドレス')
        parser.add_argument('--full-name', type=str, required=True, help='フルネーム')
        parser.add_argument('--department', type=str, default='開発部', help='部署名')
        parser.add_argument('--permission-level', type=str, 
                          choices=['user', 'admin', 'superuser'], 
                          default='user', help='権限レベル')
        parser.add_argument('--active', action='store_true', default=True, help='アクティブ状態')
        parser.add_argument('--update', action='store_true', help='既存ユーザーを更新')

    def handle(self, *args, **options):
        email = options['email']
        full_name = options['full_name']
        department = options['department']
        permission_level = options['permission_level']
        is_active = options['active']
        update = options['update']

        # @grapee.co.jpドメインチェック
        if not email.endswith('@grapee.co.jp'):
            raise CommandError(f'メールアドレスは@grapee.co.jpドメインである必要があります: {email}')

        # 既存ユーザーチェック
        try:
            user = AllowedUser.objects.get(email=email)
            if update:
                user.full_name = full_name
                user.department = department
                user.permission_level = permission_level
                user.is_active = is_active
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'ユーザー {email} を更新しました。')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'ユーザー {email} は既に存在します。更新するには --update オプションを使用してください。')
                )
                return
        except AllowedUser.DoesNotExist:
            # 新規作成
            user = AllowedUser.objects.create(
                email=email,
                full_name=full_name,
                department=department,
                permission_level=permission_level,
                is_active=is_active
            )
            self.stdout.write(
                self.style.SUCCESS(f'ユーザー {email} を追加しました。')
            )

        # 結果表示
        self.stdout.write(f'設定: {user.full_name} - {user.permission_level} - Active: {user.is_active}')
        
        # 総数表示
        total_count = AllowedUser.objects.count()
        self.stdout.write(f'総AllowedUser数: {total_count}人') 
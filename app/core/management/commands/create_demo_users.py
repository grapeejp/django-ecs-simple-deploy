from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'デモユーザーを作成します'

    def handle(self, *args, **options):
        demo_users = [
            ('admin', 'admin@grapee.co.jp', 'grape2025admin', True, True),
            ('testuser', 'test@grapee.co.jp', 'grape2025test', True, False),
            ('demo1', 'demo1@grapee.co.jp', 'grape2025demo', False, False),
            ('demo2', 'demo2@grapee.co.jp', 'grape2025demo', False, False),
            ('demo3', 'demo3@grapee.co.jp', 'grape2025demo', False, False),
        ]
        
        for username, email, password, is_staff, is_superuser in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser
                }
            )
            user.set_password(password)
            user.save()
            
            status = "作成" if created else "更新"
            self.stdout.write(
                self.style.SUCCESS(f'{status}: {username} ({email})')
            )
        
        self.stdout.write(
            self.style.SUCCESS('デモユーザーの作成/更新が完了しました')
        ) 
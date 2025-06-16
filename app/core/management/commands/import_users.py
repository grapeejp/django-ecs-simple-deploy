import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from core.models import AllowedUser, UserImportLog


class Command(BaseCommand):
    help = 'CSVファイルからAllowedUserを一括インポート'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='インポートするCSVファイルのパス'
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            default='admin',
            help='インポート実行者のユーザー名（デフォルト: admin）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際にはインポートせず、結果のみ表示'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        admin_username = options['admin_user']
        dry_run = options['dry_run']

        # ファイル存在チェック
        if not os.path.exists(csv_file):
            raise CommandError(f'CSVファイルが見つかりません: {csv_file}')

        # 実行者ユーザーを取得
        try:
            admin_user = User.objects.get(username=admin_username)
        except User.DoesNotExist:
            raise CommandError(f'ユーザーが見つかりません: {admin_username}')

        self.stdout.write(f'CSVファイル: {csv_file}')
        self.stdout.write(f'実行者: {admin_user.username}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN モード - 実際にはインポートされません'))

        # CSVファイルを読み込み
        success_count = 0
        error_count = 0
        error_details = []
        total_records = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                # CSVの形式を自動検出
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(file, delimiter=delimiter)
                
                # 必要なカラムの確認
                required_columns = ['email', 'full_name']
                if not all(col in reader.fieldnames for col in required_columns):
                    raise CommandError(
                        f'CSVファイルに必要なカラムがありません。'
                        f'必要: {required_columns}, 存在: {reader.fieldnames}'
                    )

                self.stdout.write(f'検出されたカラム: {reader.fieldnames}')
                self.stdout.write('インポート開始...\n')

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):  # ヘッダー行を除く
                        total_records += 1
                        
                        try:
                            # 必須フィールドのチェック
                            email = row['email'].strip()
                            full_name = row['full_name'].strip()
                            
                            if not email or not full_name:
                                raise ValueError('emailまたはfull_nameが空です')

                            # @grapee.co.jpドメインチェック
                            if not email.endswith('@grapee.co.jp'):
                                raise ValueError(f'無効なドメイン: {email}')

                            # オプションフィールド
                            department = row.get('department', '').strip()
                            permission_level = row.get('permission_level', 'user').strip()
                            notes = row.get('notes', '').strip()

                            # permission_levelの検証
                            valid_permissions = ['user', 'admin', 'superuser']
                            if permission_level not in valid_permissions:
                                permission_level = 'user'

                            if not dry_run:
                                # AllowedUserの作成または更新
                                allowed_user, created = AllowedUser.objects.get_or_create(
                                    email=email,
                                    defaults={
                                        'full_name': full_name,
                                        'department': department,
                                        'permission_level': permission_level,
                                        'notes': notes,
                                        'is_active': True
                                    }
                                )

                                if not created:
                                    # 既存ユーザーの更新
                                    allowed_user.full_name = full_name
                                    allowed_user.department = department
                                    allowed_user.permission_level = permission_level
                                    allowed_user.notes = notes
                                    allowed_user.is_active = True
                                    allowed_user.save()

                                action = '作成' if created else '更新'
                                self.stdout.write(
                                    f'行{row_num}: {action} - {full_name} ({email})'
                                )
                            else:
                                self.stdout.write(
                                    f'行{row_num}: [DRY RUN] {full_name} ({email}) - {permission_level}'
                                )

                            success_count += 1

                        except Exception as e:
                            error_count += 1
                            error_msg = f'行{row_num}: {str(e)} - データ: {row}'
                            error_details.append(error_msg)
                            self.stdout.write(
                                self.style.ERROR(error_msg)
                            )

                    # dry_runの場合はロールバック
                    if dry_run:
                        transaction.set_rollback(True)

        except Exception as e:
            raise CommandError(f'CSVファイルの読み込みエラー: {str(e)}')

        # 結果の表示
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'インポート結果:')
        self.stdout.write(f'総レコード数: {total_records}')
        self.stdout.write(self.style.SUCCESS(f'成功: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'エラー: {error_count}'))

        # ログの記録（dry_runでない場合のみ）
        if not dry_run:
            UserImportLog.objects.create(
                imported_by=admin_user,
                file_name=os.path.basename(csv_file),
                total_records=total_records,
                success_count=success_count,
                error_count=error_count,
                error_details='\n'.join(error_details)
            )
            self.stdout.write(self.style.SUCCESS('インポートログを記録しました。'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN完了 - 実際のデータは変更されていません'))
        else:
            self.stdout.write(self.style.SUCCESS('インポート完了')) 
from django.core.management.base import BaseCommand
from django.utils import timezone
import random
from article_management.models import Article


class Command(BaseCommand):
    help = '全記事にFacebookテキストのダミーデータを設定'
    
    # 様々なパターンのFacebookテキストサンプル
    FACEBOOK_TEXTS = [
        # 1行パターン（24文字以内）
        "これは素敵な話ですね！",
        "感動しました✨",
        "みんなに知ってほしい話",
        "心温まるエピソード",
        "思わず笑ってしまいました",
        "考えさせられる内容です",
        "シェアさせていただきます",
        "素晴らしい発見！",
        "これは必見です👀",
        "今日の癒しはこれ💕",
        
        # 2行パターン（各行24文字以内）
        "可愛すぎて癒されます🐱\nみんなも見てください！",
        "今話題のアレを試してみた\n結果は記事をチェック！",
        "知らなかった裏技を発見\nこれは便利すぎる...！",
        "感動のストーリー\n涙が止まりません😭",
        "驚きの事実が判明！\n詳細は記事で確認を",
        "これは拡散希望です\n多くの人に届きますように",
        "素敵な人との出会い\n心が温かくなりました",
        "新しい発見がありました\nシェアさせていただきます",
        "笑いが止まらない🤣\nみんなも見て！",
        "考えさせられる内容でした\nぜひ読んでみてください",
        
        # 絵文字多めパターン
        "かわいい😍😍😍",
        "すごい！！！👏👏👏",
        "感動😭✨💕",
        "爆笑🤣🤣🤣",
        "素敵💖💖💖",
        
        # 質問形式パターン
        "みなさんはどう思いますか？",
        "これって知ってました？",
        "あなたならどうしますか？",
        
        # 呼びかけパターン
        "これは見てほしい！\nRT希望です🙏",
        "フォロワーさんに朗報\n詳細は記事をチェック",
        "お時間ある方はぜひ\n読んでみてください📖",
        
        # 感想パターン
        "読んで良かった記事\nおすすめです！",
        "久々に感動しました\n素敵な話をありがとう",
        "これは保存版！\nあとで見返そう",
        
        # 実用的パターン
        "知って得する情報\nメモメモ📝",
        "これは便利！\n早速試してみます",
        "なるほど！と思いました\n参考になります",
        
        # 季節感のあるパターン
        "春にぴったりの話題🌸\nほっこりします",
        "夏の思い出に☀️\n素敵なエピソード",
        "秋の夜長に読みたい🍂\nじっくり楽しめます",
        "冬に心温まる話⛄\nシェアします",
        
        # ニュース風パターン
        "【速報】衝撃の事実\n詳細は記事で",
        "【話題】今注目の\nトレンドをチェック",
        "【感動】涙なしには\n読めません",
        
        # カジュアルパターン
        "ちょっとこれ見て〜\nやばくない？",
        "今日イチの発見\nみんなにも教えたい",
        "これはアカン\n笑いすぎて腹痛い",
    ]
    
    def handle(self, *args, **options):
        # Facebookテキストが空の記事を取得
        articles = Article.objects.filter(facebook_text='')
        total_count = articles.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING('Facebookテキストが空の記事はありません。')
            )
            return
        
        self.stdout.write(
            f'Facebookテキストを設定する記事: {total_count}件'
        )
        
        updated_count = 0
        
        for article in articles:
            # ランダムにFacebookテキストを選択
            facebook_text = random.choice(self.FACEBOOK_TEXTS)
            
            article.facebook_text = facebook_text
            article.save(update_fields=['facebook_text'])
            updated_count += 1
            
            # 進捗表示
            if updated_count % 50 == 0:
                self.stdout.write(f'  {updated_count}/{total_count} 件完了...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ {updated_count}件の記事にFacebookテキストを設定しました。'
            )
        )
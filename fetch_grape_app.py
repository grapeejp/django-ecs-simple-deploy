import requests
from bs4 import BeautifulSoup
import os

# Basic認証情報
username = "grape_admin3"
password = "6Tjcc5306u!"

# リクエスト
url = "https://grape-app.jp/"
response = requests.get(url, auth=(username, password))

if response.status_code == 200:
    # HTMLの取得に成功
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # タイトルを表示
    print(f"タイトル: {soup.title.string if soup.title else 'タイトルなし'}")
    
    # HTMLを保存
    with open("grape_app_homepage.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"HTMLを保存しました: {os.path.abspath('grape_app_homepage.html')}")
    
    # 重要なHTML要素を抽出
    forms = soup.find_all('form')
    print(f"フォーム数: {len(forms)}")
    
    # メインコンテンツ部分を抽出
    main_content = soup.find('main') or soup.find('div', {'class': 'container'}) or soup.find('div', {'id': 'content'})
    if main_content:
        with open("grape_app_main_content.html", "w", encoding="utf-8") as f:
            f.write(str(main_content))
        print(f"メインコンテンツを保存しました: {os.path.abspath('grape_app_main_content.html')}")
else:
    print(f"エラー: ステータスコード {response.status_code}")
    print(response.text) 
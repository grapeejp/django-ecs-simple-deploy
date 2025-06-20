# 校正AI専用プロンプト

## 校正カテゴリー

### 🟣 言い回しアドバイス（expression）
- 連続した語尾の改善
- より自然で温かみのある表現への修正
- 文章のリズム向上

### 🔴 誤字修正（typo）
- 基本的な誤字脱字
- HTMLタグ名・属性名の誤字
- 変換ミス

### 🟡 社内辞書ルール（dictionary）
- 固有名詞の正しい表記（企業名、地名、商品名）
- 人名の正確な表記
- 統一表記ルール

### 🟠 矛盾チェック（contradiction）
- 番組と放送局の整合性
- 地理的・論理的矛盾
- 事実関係の不整合

## プロンプト本文

原文:
{原文}

置換後のテキストをHTML形式で出力してください。HTMLタグは絶対に変更せず、そのまま保持してください。
必ず文章全体を出力し、途中で切らないこと
テキストの内容のみを置換し、以下の形式で出力してください。先に置換したテキストを出してください。その後に修正箇所を出してください。：

✅修正箇所：
- 行番号: (変更前) -> (変更後): 理由 [カテゴリー: expression|typo|dictionary|contradiction]
- 行番号: (変更前) -> (変更後): 理由 [カテゴリー: expression|typo|dictionary|contradiction]
...

## 注意事項

- すべてのHTMLタグ（<div>, <p>, <span>など）は変更せず、そのまま出力してください。
- テキスト内容のみを置換し、タグの中身だけを変更してください。
- コメントタグ（<!-- -->）の内容も変更しないでください。
- 全角の数字は全角のままでいいです。置換しないでください。
- <div class="comment">や</div>や＼nなどhtmlだけの行数も1行としてカウントする。また空白行だけの何もない行も1行として最後まで必ずカウントしてください。
- 行番号は、置換後テキストのHTMLの行数に基づいて記載してください。空白の行も一行とカウントしてください。
- 置換後のテキストは必ず最後まで出力し、途中で切らないでください。
- 修正箇所には必ずカテゴリー（expression|typo|dictionary|contradiction）を明記してください。

## HTML処理ルール

1. 提供されたテキスト内のすべてのHTMLタグを保持してください。
2. タグの内容のみを校正の対象としてください。
3. タグ自体（例：<div>, <h2>, <p>など）は決して変更や削除しないでください。ただし、タグ名の明らかな誤字（例：<dv>→<div>）は修正してください。

## 指示

1. 提供されたHTML込みのテキストを読み、HTMLタグを保持しながら基本的な校正ルールに従って修正してください。
2. 高度校正ルール（連続語尾、固有名詞、番組・放送局、人名、HTMLタグ）も適用してください。
3. 置換ルールの辞書を参照し、HTMLタグの外側のテキストに対してのみ適切な置換を行ってください。
4. 校正後のテキストを、元のHTML構造を維持したまま提供してください。
5. 主な変更点を、行番号とカテゴリーとともに説明してください。その際、HTMLタグは説明から除外し、内容の変更のみに焦点を当ててください。

## 注意事項（詳細）

- HTML形式で書かれています。<div>や<h2>や<p>などタグは絶対に変更や削除しないでください。ただし、明らかなタグ名の誤字は修正してください。
- 置換を行う際は、文脈に応じて適切かどうかを判断してください。
- HTMLタグ内の属性（class, id, styleなど）も変更しないでください。ただし、属性名の明らかな誤字は修正してください。
- 校正に関する説明は、"✅修正箇所："というマーカーの後に記載してください。
- 修正箇所の説明は、次の形式で行ってください：
  `- 行番号: (変更前) -> (変更後): 理由 [カテゴリー: expression|typo|dictionary|contradiction]`

## 出力形式

1. 最初に校正後のHTML込みテキスト全文を出力してください。
2. その後に "✅修正箇所：" を記載し、修正箇所の説明を箇条書きで記載してください。 
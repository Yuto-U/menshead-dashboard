# メンズヘッドスパ 経営ダッシュボード

新宿・銀座・上野の3店舗を運営する高級メンズヘッドスパの経営状況を一画面で把握する Streamlit ダッシュボードです。

---

## 機能

| 画面 | 内容 |
|---|---|
| ホーム | 全社+3店舗売上ストリップ / 補助KPI / 当月着地見込み / 店舗別ランキング / 月次推移 / コース別構成 |
| 店舗別 | 店舗フィルタ + 月次推移 + コース別構成 |
| キャスト別 | TOP10 + ステータス分布 + 個別キャスト詳細 + 全キャスト表 |
| コース別 | コース別ランキング + 新規/リピート構成 + 月次推移 |
| 採用・研修 | 研修進捗ヒートマップ + 完了率 + 未着手一覧 + ステータス分布 |
| トレンド分析 | 全社/店舗別月次推移 + 前月比/前年同月比 + 曜日別ヒートマップ |
| 会議モード | 1画面サマリー（定例会議でそのまま投影可） |
| 管理 | Excelアップロード / DB状態確認 / リセット |

---

## ローカル起動

### 1. 依存関係のインストール

```bash
cd dashboard
pip install -r requirements.txt
```

### 2. パスワード設定（任意）

`.streamlit/secrets.toml` を作成（`.streamlit/secrets.toml.example` をコピー）：

```toml
auth_enabled = false   # true にするとパスワード入力フォームが表示される
password = "esthi2026"
```

### 3. 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開く。

---

## データ取り込み手順

1. アプリ起動後、サイドバーの **「管理」** ページへ
2. **「Excelをアップロードして取り込む」** に以下6ファイルをドラッグ＆ドロップ：
   - `ヘッド店舗KPI.xlsx`（日次×店舗の売上、コース別件数）
   - `aoスパニスト評価シート.xlsx`（キャスト×月の指名率・売上）
   - `ao合計日報{YYMM}.xlsx`（複数月可）
   - `ヘッドスパニスト一覧管理表.xlsx`（キャストマスタ）
   - `ヘッドホワイトボード{YYMM}.xlsx`（勤怠・出禁）
   - `ヘッド研修日程表.xlsx`（研修進捗）
3. **「🚀 取り込み実行」** をクリック
4. 各画面に集計結果が反映される

ファイル名で自動判定するため、ファイル名は変更しないこと。

---

## Streamlit Community Cloud へのデプロイ

### Phase A（無料・パスワード認証）

1. **GitHubリポジトリを作成**（コードのみ、データ・secretsは含めない）
   ```bash
   cd dashboard
   git init
   git add app.py components/ db/ etl/ pages/ utils/ requirements.txt .streamlit/config.toml .streamlit/secrets.toml.example assets/ .gitignore README.md
   git commit -m "Initial dashboard"
   git remote add origin https://github.com/<user>/<repo>.git
   git push -u origin main
   ```

2. **Streamlit Community Cloud** にログイン
   - https://share.streamlit.io/
   - GitHubアカウントで連携

3. **New app** で以下を設定：
   - Repository: 上記リポジトリ
   - Branch: `main`
   - Main file path: `app.py`

4. **Secrets を設定**（Settings → Secrets）：
   ```toml
   auth_enabled = true
   password = "<強力なパスワード>"
   ```

5. **Deploy** をクリック → 数分でURLが発行される

6. 発行されたURLとパスワードを社内の5人に配布

### データの取り扱い

- DuckDBファイル (`data/warehouse.duckdb`) は `.gitignore` 済み
- 各メンバーがアプリの **「管理」ページ** からExcelをアップロードして反映
- Streamlit Cloud上のDuckDBは一時的（再起動で消える）→ 定期的に再アップロードが必要

### Phase B（恒久化・Google Sheets API）

将来、Excelの根本ソースである Google Sheets（ID: `1dcIjEOhuq...`）から直接データを取得することで、芋蔓問題を完全解決：

1. Google Cloud Console で OAuth クライアントを作成
2. `gspread` または `google-api-python-client` を追加
3. ETL層に `load_from_gsheets` を実装
4. 定期更新を `streamlit_autorefresh` で自動化

---

## プロジェクト構造

```
dashboard/
├── app.py                     # エントリポイント / ホーム
├── pages/                     # マルチページ
│   ├── 2_🏪_店舗別.py
│   ├── 3_💆_キャスト別.py
│   ├── 4_🎯_コース別.py
│   ├── 5_📚_採用研修.py
│   ├── 6_📈_トレンド分析.py
│   ├── 7_📺_会議モード.py
│   └── 9_⚙️_管理.py
├── components/
│   ├── auth.py                # パスワード認証
│   ├── layout.py              # ヘッダ・サイドバー・KPIカード・rank_list・empty_state
│   ├── style.py               # グローバルCSS（CSS変数によるデザイントークン）
│   ├── theme.py               # カラーパレット・Plotlyテーマ
│   ├── charts.py              # 共通グラフ関数
│   └── icons.py               # SVGアイコン
├── etl/
│   ├── normalize.py           # 店舗名・キャスト名・電話番号ハッシュ化
│   ├── loaders.py             # 各Excelファイル別ローダー
│   └── pipeline.py            # ETLパイプライン
├── db/
│   └── warehouse.py           # DuckDBスキーマ・接続
├── utils/
│   ├── format.py              # yen / percent
│   └── kpi.py                 # KPI計算ロジック
├── assets/
│   ├── logo.png
│   └── logo_icon.png          # ファビコン
├── .streamlit/
│   ├── config.toml            # テーマ
│   ├── secrets.toml.example   # パスワード設定例
│   └── secrets.toml           # 本物（gitignore済み）
├── data/
│   └── warehouse.duckdb       # 取り込み済みデータ（gitignore済み）
├── requirements.txt
├── .gitignore
└── README.md
```

---

## デザイン原則

このダッシュボードは以下の8つの原則に従って設計されています：

1. **レイアウト統一**：max-w 1400px、余白30%基準、セクション縦余白統一
2. **カードフラット化**：影なし、ボーダー1px、角丸統一（`var(--radius-xl)`）
3. **セクションヘッダー定型**：kicker + title の2行構成
4. **数値表示**：英字フォント（Inter）、ExtraBold、上下ラベル付き
5. **グリッド構成**：情報優先度で4/3/2カラム
6. **デザイントークン化**：色・余白・角丸・フォントは全てCSS変数
7. **Empty State**：データ0件時の点線プレースホルダー
8. **NGリスト**：影禁止、カード毎の角丸変更禁止、余白バラバラ禁止、派手装飾禁止

### 5色ベース
1. ブロンズ（プライマリ・店舗・グラフ）
2. テキストグレー
3. 背景白系
4. 成功緑（増加・好調）
5. 警告赤（減少・要対応）

### フォント
- 日本語：Noto Sans JP（400/700）
- 英字・数値：Inter（400/700/800）

---

## トラブルシューティング

### Q. Streamlitが起動しない
```bash
pip install -r requirements.txt --upgrade
```

### Q. Excelアップロードでエラー
- ファイル名を変更していないか確認
- DuckDBをリセット（管理ページ → 🗑 全データを削除）→ 再アップロード

### Q. 「データがありません」と表示される
- 管理ページからExcelをアップロード
- 該当データがない月を選択していないか確認

### Q. Streamlit Cloud のDBデータが消える
- 仕様（一時ストレージ）。再起動時に管理ページから再アップロードが必要
- 恒久化する場合は Phase B（Google Sheets API連携）へ移行

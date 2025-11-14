#バーチャルオフィス
# ステップ0: 準備（ライブラリのインストールと日本語設定） bild用
# -----------------------------------------------------------------
# ローカル環境で実行する場合は、この行は不要です
# !pip install pandas matplotlib seaborn japanize-matplotlib
#*現在のロジックでは、主要なレンタルオフィスブランド（Regus, WeWorkなど）と主要なポータル（JustFitなど）以外は、地域特化/その他 に分類されています。
#この 地域特化/その他 の中には、以下の3つのタイプが混在しています。
#ビル公式サイト / 開発会社: 特定のビルディング（例: 六本木ヒルズ森タワー）やデベロッパーのドメイン。
#大手仲介・賃貸ポータル: 一般的なオフィス賃貸や会議室仲介を行う大手サイト（例: CBRE, HOME'S）。
#小規模な地域特化運営会社: その地域やビルに限定的に存在するサービス提供者。

import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib # 日本語表示を有効化

# グラフのスタイル設定
sns.set(style='whitegrid', font="YuGothic")


# ステップ1: データの読み込みと前処理
# -----------------------------------------------------------------
file_path = 'google_search_domains_bild_バーチャル_2.csv' # ご指定のローカルパス

try:
    df_raw = pd.read_csv(file_path, encoding='utf-8-sig')
    df_raw.columns = ['キーワード'] + [f'{i}位ドメイン' for i in range(1, len(df_raw.columns))]
    print(f"'{file_path}' の読み込みに成功しました。")
except FileNotFoundError:
    print(f"エラー: '{file_path}' が見つかりませんでした。")
    exit()

# CSVの元のキーワード順をここで保存します
original_keyword_order = df_raw['キーワード'].tolist()

# データを縦持ちに変換
df_long = df_raw.melt(id_vars=['キーワード'], var_name='順位', value_name='ドメイン').dropna(subset=['ドメイン'])
df_long['順位'] = df_long['順位'].str.extract(r'(\d+)').astype(int)


# --- ドメインからブランドを特定する関数（▼▼▼ ここを修正します ▼▼▼） ---
def extract_brand_and_type_from_domain(domain):
    domain = str(domain).lower()

    # I. 【大手・準大手】フレキシブルオフィス/バーチャルオフィス運営会社
    brand_domains = {
        'regus-office.jp': 'リージャス/OpenOffice', 
        'regus.com': 'リージャス/Regus Global', 
        'www.spacesworks.com': 'SPACES', 
        'executivecentre.com': 'エグゼクティブセンター', 
        'servcorp.co.jp': 'サーブコープ', 
        'justcoglobal.com': 'JustCo',
        'mf.workstyling.jp': 'ワークスタイリング (三菱地所)', 
        'entre-salon.com': 'アントレサロン (VO)',
        'moboff-shinjuku.jp': 'モバイルオフィス',
        'united-office.com': 'ユナイテッドオフィス (VO/RO)', # 新規追加: VO/RO両方で登場
        'www.v-office23.jp': 'V-Office/銀座バーチャル (VO)', # 新規追加: VO専門
        'virtualoffice1.jp': 'バーチャルオフィス1 (VO)', # 新規追加: VO専門
        'www.gmo-office.com': 'GMOオフィス (VO/RO)', # 新規追加: GMOグループのVO/RO
        'www.ginza-plus.net': '銀座プラス (VO)', # 新規追加: VO専門
        'www.1sbc.com': '1st PLACE/ワンストップ (VO)', # 新規追加: VO専門
        'virtual.businesscentre.jp': 'ビジネスセンター (VO)', # 新規追加: VOサービス
        'www.k-society.com': 'K-Society (VO/レンタルオフィス)', # 新規追加: 仙台などで確認されるVO
    }
    for d, name in brand_domains.items():
        if d in domain: return name, '運営会社/VO専門'
        
    # II. 【ポータル/メディア】レンタルオフィス/VO専門の仲介・検索サイト
    media_domains = {
        'justfitoffice.com': 'JUST FIT OFFICE', 
        'rentaloffice-search.jp': 'レンタルオフィス検索',
        'www.rental-o.com': 'レンタルオフィス.com', 
        'kariruoffice.com': 'カリルオフィス',
        'www.rental-office-search.jp': 'レンタルオフィスサーチ', 
        'hubspaces.jp': 'HubSpaces',
        'coworking-japan.org': 'Coworking Japan' ,
        'sohonavi.jp': 'SOHO Navi' # SOHOもVOと親和性が高いため移動
    }
    for d, name in media_domains.items():
        if d in domain: return name, 'ポータル/メディア'

    # III. 【知識/ツール系】登記や会計サービス
    if 'freee.co.jp' in domain:
        return 'freee (会計ツール)', '知識/ツール'
    if 'biz.moneyforward.com' in domain:
        return 'マネーフォワード (知識/ツール)', '知識/ツール'
    if 'nawabari.net' in domain:
        return 'ナワバリ (登記/住所サービス)', '知識/ツール'
    if 'kigyo.gmo' in domain:
        return 'GMO (起業サポート)', '知識/ツール'
    if 'xn--dckn0c3a4e6a4gwc5hz256bzg3a.jp' in domain:
        return 'バーチャルオフィスナビ', '知識/ツール' # ドメイン名が長いので分類

    # IV. 【ビル公式サイト/開発/不動産】
    if 'yokohama-sky.co.jp' in domain or 'elite-bldg.com' in domain or 'mbaypoint.com' in domain:
        return 'ビル公式サイト', 'ビル/不動産'
    if 'mec.co.jp' in domain or 'nissay-marunouchi.com' in domain or 'shizukuru.pref.shizuoka.jp' in domain:
        return 'デベロッパー/ビル管理', 'ビル/不動産'
    if 'office.yield-marketing.co.jp' in domain or 'bistation.jp' in domain or 'building-pc.cocolog-nifty.com' in domain:
        return '地域/不動産情報', 'ビル/不動産'
    if 'livex-inc.com' in domain:
        return 'LiveX (仲介)', 'ビル/不動産'

    # V. その他の公的・広報ドメイン
    if 'prtimes.jp' in domain: return 'PR Times', 'その他（広報）'
    if 'kensetsunews.com' in domain: return '建設ニュース', 'その他（広報）'
    if 'incu.metro.tokyo.lg.jp' in domain: return '公的機関（東京都）', '公的機関'
    if any(ext in domain for ext in ['.pref.', '.city.', '.lg.jp']): return '公的機関', '公的機関'
    
    # VI. その他の一般ドメイン
    return 'その他', 'その他'

# 以下のコードに、上記で定義した新しい関数を組み込んで実行してください。
# df_long[['ブランド名', 'サイト種別']] = df_long['ドメイン'].apply(lambda x: pd.Series(extract_brand_and_type_from_domain(x)))
# print("データの前処理が完了しました。グラフを描画します。")

df_long[['ブランド名', 'サイト種別']] = df_long['ドメイン'].apply(lambda x: pd.Series(extract_brand_and_type_from_domain(x)))
print("データの前処理が完了しました。グラフを描画します。")


# --- グラフ描画セクション ---

# グラフ1と3で使用する集計データ
brand_rank_crosstab = pd.crosstab(df_long['ブランド名'], df_long['順位'])
brand_rank_crosstab = brand_rank_crosstab.reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
brand_rank_crosstab['合計'] = brand_rank_crosstab.sum(axis=1)
threshold = 3
others = brand_rank_crosstab[brand_rank_crosstab['合計'] < threshold]
main_brands = brand_rank_crosstab[brand_rank_crosstab['合計'] >= threshold]
if not others.empty:
    others_sum = others.sum().rename('その他（小規模サイト）')
    main_brands = pd.concat([main_brands, pd.DataFrame(others_sum).T])

# グラフ1: ブランドシェア
brand_rank_crosstab_sorted = main_brands.sort_values('合計', ascending=False).drop('合計', axis=1)
brand_rank_crosstab_sorted.plot(
    kind='bar', stacked=True, figsize=(18, 9), cmap='viridis'
).set_title('ドメイン別 上位5位内掲載回数（順位別）', fontsize=18)
plt.xlabel('ブランド名 / メディア名', fontsize=14); plt.ylabel('掲載回数', fontsize=14)
plt.xticks(rotation=45, ha='right'); plt.legend(title='順位', bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout(); plt.show()

# グラフ3: サイト種別の割合
# ★★★ このグラフでは、凡例に「競合プラットフォーム」が自動的に追加され、より詳細な分析が可能になります ★★★
rank_type_crosstab_normalized = pd.crosstab(df_long['順位'], df_long['サイト種別'], normalize='index') * 100
rank_type_crosstab_normalized.plot(
    kind='bar', stacked=True, figsize=(12, 7), cmap='plasma'
).set_title('検索順位別 サイト種別の割合', fontsize=16)
plt.xlabel('検索順位', fontsize=12); plt.ylabel('割合 (%)', fontsize=12)
plt.xticks(rotation=0); plt.legend(title='サイト種別', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout(); plt.show()


# グラフ4: ヒートマップ
top_brands_for_heatmap = main_brands.sort_values('合計', ascending=False).head(15).index
heatmap_data = df_long[df_long['ブランド名'].isin(top_brands_for_heatmap)].pivot_table(
    index='キーワード', columns='ブランド名', values='順位', aggfunc='min'
)
# pivot_tableによってソートされたY軸を、CSVの元の順序に戻します
heatmap_data = heatmap_data.reindex(original_keyword_order)

# X軸（ブランド）を合計掲載回数順に並べ替え
heatmap_data = heatmap_data.reindex(columns=top_brands_for_heatmap)

plt.figure(figsize=(20, 30))
sns.heatmap(
    heatmap_data, annot=True, fmt='.0f', cmap='Reds_r',
    linewidths=.5, cbar_kws={'label': '検索順位'}, annot_kws={"size": 10}
)
plt.title('【上位15ブランド】検索キーワード vs ブランド別 検索順位ヒートマップ', fontsize=18, pad=20)
plt.xlabel('ブランド名 / メディア名', fontsize=14); plt.ylabel('検索キーワード', fontsize=14)
plt.xticks(rotation=45, ha='right'); plt.yticks(fontsize=10)
plt.savefig('heatmap_build_vo.png', dpi=300, bbox_inches='tight')
plt.tight_layout(); plt.show()
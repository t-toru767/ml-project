#ビル名＋バーチャル
import time
import random
import csv
import os
from urllib.parse import urlparse  # ★ドメイン解析のためにインポート
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth

def read_keywords_from_csv(input_csv_filename: str) -> list[str]:
    """
    CSVファイルからキーワードを読み込み、検索クエリのリストを生成する。
    """
    queries = []
    print(f"--- 「{input_csv_filename}」からキーワードを読み込み中 ---")
    try:
        with open(input_csv_filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # ヘッダー行をスキップ
            for row in reader:
                query = ' '.join(cell.strip() for cell in row if cell.strip())
                if query:
                    queries.append(query)
        print(f"--- {len(queries)}件のキーワードを読み込みました ---")
        return queries
    except FileNotFoundError:
        print(f"エラー: 「{input_csv_filename}」が見つかりませんでした。")
        return []
    except Exception as e:
        print(f"CSVファイルの読み込み中にエラーが発生しました: {e}")
        return []

def scrape_google_domains_to_csv(queries: list[str], output_csv_filename: str):
    """
    複数のGoogle検索キーワードについて検索を実行し、各キーワードの
    自然検索結果の上位5位までのドメインをCSVファイルに保存する。
    """
    # 1. Chromeのオプションを設定
    print("1. ブラウザのオプションを設定中...")
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        # 2. WebDriverを一度だけ初期化
        print("2. WebDriverを起動中...")
        driver = webdriver.Chrome(options=chrome_options)
        stealth(driver, languages=["ja-JP", "ja"], vendor="Google Inc.", platform="Win32",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
        driver.set_window_size(1280, 800)
        
        # 3. CSVファイルの準備
        file_exists = os.path.isfile(output_csv_filename)
        with open(output_csv_filename, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            if not file_exists:
                # ★ヘッダーをドメイン用に変更
                header = ['キーワード', '1位ドメイン', '2位ドメイン', '3位ドメイン', '4位ドメイン', '5位ドメイン']
                writer.writerow(header)
                print(f"3. 「{output_csv_filename}」を新規作成し、ヘッダーを書き込みました。")
            else:
                print(f"3. 既存の「{output_csv_filename}」に結果を追記します。")

        # 4. 各キーワードで検索をループ実行
        for i, query in enumerate(queries, 1):
            print(f"\n--- 検索中 ({i}/{len(queries)}): 「{query}」 ---")
            
            driver.get("https://www.google.com")
            time.sleep(random.uniform(2, 4))
            
            # ... (検索実行までの処理は前回と同じ)
            try:
                search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
            except TimeoutException:
                try:
                    consent_button = driver.find_element(By.XPATH, "//button[.//div[contains(text(), 'すべて同意')]] | //button[.//div[contains(text(), 'すべて受け入れる')]]")
                    consent_button.click()
                    print("   - Cookieの同意ボタンをクリックしました。")
                    time.sleep(random.uniform(1, 2))
                    search_box = driver.find_element(By.NAME, "q")
                except Exception as e:
                    print(f"   - Cookie同意画面の処理または検索ボックスの特定に失敗: {e}")
                    continue
            
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)

            print("   - 検索結果の読み込みを待機中...")
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "rcnt")))
            time.sleep(random.uniform(1, 2))

            # 5. ドメインを抽出 ★ここが変更の中核です★
            print("   - 検索結果からドメインを抽出中...")
            domains = []
            # 自然検索結果のリンク(aタグ)を取得
            link_elements = driver.find_elements(By.CSS_SELECTOR, "#search .yuRUbf a")
            
            for link in link_elements[:5]:  # 上位5件を処理
                url = link.get_attribute('href')
                if url:
                    try:
                        domain = urlparse(url).netloc
                        domains.append(domain)
                    except Exception:
                        domains.append('')  # URLのパースに失敗した場合
                else:
                    domains.append('')  # href属性が存在しない場合
            
            print(f"   - {len(domains)}件のドメインを取得しました。")

            # 6. CSVファイルに追記
            row_data = [query] + domains
            row_data.extend([''] * (6 - len(row_data)))
            
            with open(output_csv_filename, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            
            print(f"   - CSVファイルに保存しました。")

    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        if driver:
            driver.save_screenshot("/data/error_screenshot.png")
            with open("data/error_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("デバッグ用に error_screenshot.png と error_page.html を保存しました。")
    finally:
        if driver:
            print("\n--- 全ての処理が完了しました。5秒後にブラウザを終了します。 ---")
            time.sleep(5)
            driver.quit()
            print("WebDriverを終了しました。")

if __name__ == "__main__":
    # --- 設定 ---
    input_csv_file = "data/bild_バーチャル.csv"
    output_csv_file = "data/google_search_domains_bild_バーチャル_2.csv" # 出力ファイル名を変更
    
    # --- 実行 ---
    keywords_to_search = read_keywords_from_csv(input_csv_file)
    
    if keywords_to_search:
        scrape_google_domains_to_csv(keywords_to_search, output_csv_file)
    else:
        print("処理するキーワードがありませんでした。プログラムを終了します。")
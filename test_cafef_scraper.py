"""
Test script for CafeF scraper
"""
import requests
from bs4 import BeautifulSoup

# URL mapping for major Vietnamese stocks
CAFEF_URL_MAPPING = {
    'VNM': 'VNM-cong-ty-co-phan-sua-viet-nam',
    'PLX': 'PLX-tap-doan-xang-dau-viet-nam',
    'FPT': 'FPT-cong-ty-co-phan-fpt',
}

def test_cafef_scraper(ticker):
    """Test scraping P/E, EPS, ROE from cafef.vn"""
    print(f"\n{'='*60}")
    print(f"Testing CafeF scraper for {ticker}")
    print('='*60)

    try:
        if ticker not in CAFEF_URL_MAPPING:
            print(f"No URL mapping for {ticker}")
            return

        url_slug = CAFEF_URL_MAPPING[ticker]
        exchange = 'hose'
        cafef_url = f"https://s.cafef.vn/{exchange}/{url_slug}.chn"

        print(f"URL: {cafef_url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(cafef_url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the right table container with financial metrics
            right_table = soup.find('div', id='transaction-information-table-right')

            if right_table:
                print("\n[SUCCESS] Found transaction-information-table-right")

                # Debug: show the HTML structure
                print("\n--- HTML Structure ---")
                print(right_table.prettify()[:500])
                print("...")

                # Get all metric items
                metric_items = right_table.find_all('div', class_='table-right-item')
                print(f"\nFound {len(metric_items)} metric items with class='table-right-item'")

                # Try alternative selectors
                all_divs = right_table.find_all('div')
                print(f"Total divs in container: {len(all_divs)}")

                if len(metric_items) >= 3:
                    # Extract EPS (position 0)
                    print("\n--- EPS (Position 0) ---")
                    eps_element = metric_items[0].find_all('p')
                    print(f"Number of <p> tags: {len(eps_element)}")
                    for i, p in enumerate(eps_element):
                        print(f"  p[{i}]: {p.get_text(strip=True)}")

                    if len(eps_element) >= 2:
                        eps_text = eps_element[1].get_text(strip=True)
                        eps_text = eps_text.replace(',', '').replace(' ', '')
                        if eps_text and eps_text != '-':
                            eps = float(eps_text)
                            print(f"✓ EPS: {eps:,.0f} VND")

                    # Extract P/E (position 1)
                    print("\n--- P/E (Position 1) ---")
                    pe_element = metric_items[1].find_all('p')
                    print(f"Number of <p> tags: {len(pe_element)}")
                    for i, p in enumerate(pe_element):
                        print(f"  p[{i}]: {p.get_text(strip=True)}")

                    if len(pe_element) >= 2:
                        pe_text = pe_element[1].get_text(strip=True)
                        pe_text = pe_text.replace(',', '').replace(' ', '')
                        if pe_text and pe_text != '-':
                            pe_ratio = float(pe_text)
                            print(f"✓ P/E: {pe_ratio:.2f}x")

                    # Extract ROE (position 2)
                    print("\n--- ROE (Position 2) ---")
                    roe_element = metric_items[2].find_all('p')
                    print(f"Number of <p> tags: {len(roe_element)}")
                    for i, p in enumerate(roe_element):
                        print(f"  p[{i}]: {p.get_text(strip=True)}")

                    if len(roe_element) >= 2:
                        roe_text = roe_element[1].get_text(strip=True)
                        roe_text = roe_text.replace('%', '').replace(',', '').replace(' ', '')
                        if roe_text and roe_text != '-':
                            roe = float(roe_text) / 100
                            print(f"✓ ROE: {roe*100:.1f}%")
                else:
                    print(f"[ERROR] Not enough metric items (found {len(metric_items)}, need >= 3)")
            else:
                print("[ERROR] Could not find div#transaction-information-table-right")

                # Debug: show what IDs are available
                print("\nAvailable div IDs:")
                all_divs_with_id = soup.find_all('div', id=True)
                for div in all_divs_with_id[:10]:  # Show first 10
                    print(f"  - {div.get('id')}")
        else:
            print(f"[ERROR] HTTP {response.status_code}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Test with VNM
    test_cafef_scraper('VNM')

    # Test with PLX
    test_cafef_scraper('PLX')

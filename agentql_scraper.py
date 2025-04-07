import agentql
from playwright.sync_api import sync_playwright
import pdfplumber
import requests
import time
from io import BytesIO

def scrape_pdf(url):
    """
    Scrape konten dari file PDF menggunakan pdfplumber.
    
    Args:
        url (str): URL file PDF yang akan di-scrape.
    
    Returns:
        str: Teks yang diambil dari PDF, atau None jika gagal.
    """
    print(f"Deteksi file PDF: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": url
    }
    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Cek apakah request berhasil
            pdf_data = BytesIO(response.content)  # Ubah ke BytesIO biar seekable
            with pdfplumber.open(pdf_data) as pdf:
                pdf_text = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
                return pdf_text.strip() if pdf_text else "Gagal membaca konten dari PDF."
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} gagal: {e}")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(2)
        except Exception as e:
            print(f"Error membaca PDF: {e}")
            return None

def scrape_website(url):
    """
    Scrape website atau file PDF menggunakan AgentQL atau pdfplumber.
    
    Args:
        url (str): URL website atau file PDF yang akan di-scrape.
    
    Returns:
        str: Teks yang di-scrape dari website atau PDF, atau None jika gagal.
    """
    try:
        # Cek apakah URL adalah file PDF
        if url.lower().endswith(".pdf"):
            return scrape_pdf(url)

        # Scrape website pake Playwright dan AgentQL
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            wrapped_page = agentql.wrap(page)

            MAX_RETRIES = 2
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"Attempt {attempt + 1} buat scrape {url}...")
                    wrapped_page.goto(url, timeout=120000)  # Timeout 120 detik
                    wrapped_page.wait_for_load_state("load", timeout=120000)  # Ganti ke "load"
                    print("Halaman berhasil dimuat.")
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} gagal: {e}")
                    if attempt == MAX_RETRIES - 1:
                        return None
                    time.sleep(2)

            # Coba cari link PDF di halaman
            pdf_links = wrapped_page.eval_on_selector_all("a[href$='.pdf']", "elements => elements.map(e => e.href)")
            if pdf_links:
                print(f"Link PDF ditemukan: {pdf_links[0]}")
                pdf_text = scrape_pdf(pdf_links[0])
                if pdf_text:
                    return pdf_text
                else:
                    print("Gagal scrape PDF, mencoba scrape konten halaman.")

            # Scrape konten web sebagai fallback
            pertanyaan = """
            {
                div(id="bodycontent") {
                    content_div(class="mw-parser-output") {
                        paragraphs[]
                    }
                }
            }
            """
            response = wrapped_page.query_elements(pertanyaan)
            if response:
                div = getattr(response, 'div', None)
                if div:
                    content_div = getattr(div, 'content_div', None)
                    if content_div:
                        paragraphs = getattr(content_div, 'paragraphs', [])
                        all_paragraph_text = "\n\n".join(getattr(p, 'text_content', lambda: "")() for p in paragraphs)
                        return all_paragraph_text.strip() if all_paragraph_text else None
            return None

    except Exception as e:
        print(f"Error saat scraping {url}: {e}")
        return None

def summarize_webpages(urls):
    """
    Scrape dan gabungkan konten dari beberapa website atau file PDF.
    
    Args:
        urls (list): Daftar URL website atau PDF yang akan di-scrape.
    
    Returns:
        str: Teks gabungan dari semua URL, atau pesan error jika gagal.
    """
    combined_text = ""
    for url in urls:
        print(f"Scraping website: {url}...")
        try:
            website_text = scrape_website(url)
            if website_text:
                combined_text += website_text + "\n\n"
            else:
                print(f"Gagal scrape: {url}, lanjut ke URL berikutnya.")
        except Exception as e:
            print(f"Error saat scraping {url}: {e}")
            continue

    if not combined_text:
        return "Gak ada teks yang di-scrape bro."
    return combined_text.strip()

if __name__ == "__main__":
    urls = [
        "https://id.wikipedia.org/wiki/Joko_Widodo",
        "https://finance.detik.com/",
        "https://example.com/document.pdf"
    ]
    summary = summarize_webpages(urls)
    if summary:
        print("\n--- Teks Hasil Scraping ---")
        print(summary[:500] + "..." if len(summary) > 500 else summary)
    else:
        print("Scraping gagal atau gak ada teks ditemukan.")
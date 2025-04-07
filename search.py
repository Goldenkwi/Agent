import requests
import sys

key_api = "AIzaSyCLInGodWFy5X2lKSnmeR4yYMRSq1uoAgk"
search_id = "9413609139d30463c"

class Search:
    def get_user_query(self):
        """
        Ambil input query dari user.
        
        Returns:
            str: Query yang dimasukkan user. Keluar dari program kalo input 'exit'.
        """
        query = input("> user: ")
        if query.lower() == "exit":
            sys.exit()
        return query

    def google_search(self, query):
        """
        Cari di Google pake Custom Search API dan kembalikan daftar link.
        
        Args:
            query (str): Kata kunci yang mau dicari.
        
        Returns:
            list: Daftar URL dari hasil pencarian, atau kosong kalo gagal.
        """
        query = f"{query} berita penjelasan"
        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": key_api,
            "num": 10,
            "cx": search_id,
            "cr": "countryID"
        }
        
        try:
            print(f"Request URL: {url}")
            print(f"Params: {params}")
            response = requests.get(url=url, params=params)
            response.raise_for_status()
            result = response.json()
            if "items" in result:
                links = [item["link"] for item in result["items"]]
                return links
            else:
                print("Gak ada hasil bro.")
                return []
        except Exception as e:
            print(f"Error nyanyi: {e}")
            return []

if __name__ == "__main__":
    search = Search()
    query = search.get_user_query()
    links = search.google_search(query)
    print("Links:", links)
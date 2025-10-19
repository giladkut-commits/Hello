import scrapy
from scrapy.crawler import CrawlerProcess
from urllib.parse import urljoin, urlparse, parse_qs, unquote

class DuckDuckGoCrawler(scrapy.Spider):
    name = "duckduckgo_social"
    def __init__(self, name_to_search, max_pages=30, *args, **kwargs):
        super(DuckDuckGoCrawler, self).__init__(*args, **kwargs)
        self.name_to_search = name_to_search.replace(" ", "+")
        self.max_pages = max_pages
        self.sources = {
            "DuckDuckGo": f"https://duckduckgo.com/html/?q={self.name_to_search}",
            "Facebook": f"https://duckduckgo.com/html/?q=site:facebook.com+{self.name_to_search}",
            "Instagram": f"https://duckduckgo.com/html/?q=site:instagram.com+{self.name_to_search}",
            "LinkedIn": f"https://duckduckgo.com/html/?q=site:linkedin.com/in+{self.name_to_search}",
            "YouTube": f"https://duckduckgo.com/html/?q=site:youtube.com+{self.name_to_search}",
        }
        self.start_urls = list(self.sources.values())
        self.results = []
        self.seen = set()
        self.current_page = {url: 1 for url in self.start_urls}

    def parse(self, response, **kwargs):

        source_label = response.meta.get('source_label')

        if not source_label:
            source_label = "Unknown"
            for name, url in self.sources.items():
                base_url = url.split('?')[0]
                if base_url in response.url:
                    source_label = name
                    break

        for result in response.css("a.result__a"):
            title = ' '.join(result.css("*::text").getall()).strip()
            link = result.attrib.get("href")
            if not link or link in self.seen:
                continue

            parsed = urlparse(link)
            query = parse_qs(parsed.query)
            link_clean = unquote(query.get("uddg", [link])[0])

            if source_label == "LinkedIn" and "/in/" not in link_clean and "/posts/" not in link_clean:
                continue
            if source_label == "YouTube" and not (
                    "/channel/" in link_clean or "/user/" in link_clean or "/watch?" in link_clean
            ):
                continue
            if source_label == "Facebook" and not (
                    "/profile.php" in link_clean or "/pages/" in link_clean or "/posts/" in link_clean or "/videos/" in link_clean
            ):
                continue
            if source_label == "Instagram" and not (
                    "/p/" in link_clean or "/tv/" in link_clean or "/reel/" in link_clean
            ):
                continue

            if self.name_to_search.replace("+", " ") not in title:
                continue

            self.seen.add(link_clean)
            self.results.append((source_label, title, link_clean))
            print(f"[{source_label}] {title}\n{link_clean}\n")

        next_page = response.css("a.result--more__btn::attr(href)").get()
        if next_page and self.current_page.get(response.url, 1) < self.max_pages:
            self.current_page[response.url] = self.current_page.get(response.url, 1) + 1
            next_page_url = urljoin(response.url, next_page)
            yield response.follow(
                next_page_url,
                callback=self.parse,
                meta={'source_label': source_label}
            )
            
NAME = input("Enter search serch: ")
process = CrawlerProcess(settings={"LOG_LEVEL": "ERROR"})
process.crawl(DuckDuckGoCrawler, name_to_search=NAME, max_pages=3)
process.start()
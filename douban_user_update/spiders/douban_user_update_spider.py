import re
from logging import getLogger

from douban_user_update.items import DoubanUser

from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import scrapy

log = getLogger(__name__)


class DoubanUserUpdateSpider(CrawlSpider):
    name = "douban_user_update_spider"
    allowed_domains = ["douban.com"]
    items_id = set()
    start_urls = [
        'https://www.douban.com/people/windbo/',
        'https://movie.douban.com/review/best/?start=0'
    ]

    rules = (
        Rule(LinkExtractor(allow=(r'https://movie.douban.com/review/best/?start=\d+',)),callback="parse_contacts_from_best_reviews"),
        Rule(LinkExtractor(allow=(r'https://www.douban.com/people/\w+/')), callback='parse_contacts')
    )

    TOP_PERCENTAGE = 0.10
    TOP_LIMIT = 200
    DOUBAN_MOVIE_ITEM_PER_PAGE = 15

    def parse_contacts_from_best_reviews(self, response):
        log.info('parsing contacts from best reviews: {}'.format(response.url))
        selector = Selector(response)

        contacts_urls = selector.xpath('//*[@id="content"]/div/div[1]/div[4]/ul/li[3]/span/span[1]/a/@href').extract()
        contacts = [re.match(r'^https\:\/\/www\.douban\.com\/people\/(?P<user_id>[\w\-\_]+)\/$', contact_url).group('user_id') for
                    contact_url in contacts_urls]

        for contact in contacts:
            movie_url = 'https://movie.douban.com/people/{}/collect?sort=rating&start=\d+&mode=grid&tags_sort=count'.format(contact)
            yield scrapy.Request(movie_url, callback=self.parse_user_movies, meta={'user_id': contact})

    def parse_contacts(self, response):
        log.info('parsing contacts: {}'.format(response.url))

        selector = Selector(response)

        contacts_urls = selector.xpath('//*[@id="friend"]/dl/dd/a/@href').extract()
        contacts = [re.match(r'^https\:\/\/www\.douban\.com\/people\/(?P<user_id>[\w\-\_]+)\/$', contact_url).group('user_id') for
                    contact_url in contacts_urls]

        for contact in contacts:
            movie_url = 'https://movie.douban.com/people/{}/collect?sort=rating&start=\d+&mode=grid&tags_sort=count'.format(contact)
            yield scrapy.Request(movie_url, callback=self.parse_user_movies, meta={'user_id': contact})

    def parse_user_movies(self, response):
        log.info("start parsing user movies {}".format(response.url))

        user_id = response.meta['user_id']
        selector = Selector(response)
        item = DoubanUser()

        item['user_id'] = user_id

        # watched total
        total_string = selector.xpath('//*[@id="db-usr-profile"]/div[2]/h1/text()').extract_first()
        watched_total = re.search(r'\((?P<watched_total>\d+)\)$', total_string)
        if watched_total:
            item['watched_total'] = int(watched_total.group('watched_total'))
        else:
            item['watched_total'] = 0
            item['top_movies'] = []
            yield item

        movies = self.parse_movies(selector)

        # now crawl for movie rankings
        number_of_top_movies_to_crawl = int(item['watched_total'] * self.TOP_PERCENTAGE)
        for page_start in range(15, number_of_top_movies_to_crawl, self.DOUBAN_MOVIE_ITEM_PER_PAGE):
            page_url = 'https://movie.douban.com/people/{}/collect?sort=rating&start={}&mode=grid&tags_sort=count'.format(user_id, page_start)
            movies.extend(scrapy.Request(page_url, callback=self.parse_top_movies))

        item['top_movies'] = movies
        yield item

    def parse_top_movies(self, response):
        log.info("start parsing user movies {}".format(response.url))
        selector = Selector(response)
        return self.parse_movies(selector)

    @staticmethod
    def parse_movies(selector):
        movie_urls = selector.xpath('//*[@id="content"]/div[2]/div[1]/div[2]/div/div[2]/ul/li[1]/a/@href').extract()
        return [re.match(r'^https\:\/\/movie\.douban\.com\/subject\/(?P<movie_id>\d+)\/$', movie_url).group('movie_id')
                for movie_url in movie_urls]
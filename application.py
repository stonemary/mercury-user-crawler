# mimics application.py but is really a script

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())

# name of spider
process.crawl('douban_user_update_spider')
process.start() # the script will block here until the crawling is finished
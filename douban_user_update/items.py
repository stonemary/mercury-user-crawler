# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanUser(scrapy.Item):
    # define the fields for your item here like:
    user_id = scrapy.Field()
    watched_total = scrapy.Field()
    top_movies = scrapy.Field()
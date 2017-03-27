# -*- coding: utf-8 -*-
from RISJbot.spiders.basespiders import NewsRSSFeedSpider
from RISJbot.loaders import NewsLoader
# Note: mutate_selector_del_xpath is somewhat naughty. Read its docstring.
from RISJbot.utils import mutate_selector_del_xpath
from RISJbot.utils import split_multiple_byline_string
from scrapy.loader.processors import Identity, TakeFirst
from scrapy.loader.processors import Join, Compose, MapCompose
import re

class DailyMailSpider(NewsRSSFeedSpider):
    name = 'dailymail'
    # allowed_domains = ['dailymail.co.uk']
    start_urls = ['http://www.dailymail.co.uk/articles.rss']

    # RSSFeedSpider parses the RSS feed and calls parse_page(response) as a
    # callback for each page it finds in the feed.
    def parse_page(self, response):
        """@url http://www.dailymail.co.uk/news/article-4242322/Milo-Yiannopoulos-BANNED-CPAC-conference.html?ITO=1490
        @returns items 1
        @scrapes bodytext bylines fetchtime firstpubtime modtime headline
        @scrapes keywords section source summary url
        """

        s = response.selector
        # Remove some content from the tree before passing it to the loader.
        # There aren't native scrapy loader/selector methods for this.        
#        self.logger.debug("before mutate_selector: %s" % str(s.xpath('//div[contains(@class, "related-carousel")]')))
        mutate_selector_del_xpath(s, '//script')
        mutate_selector_del_xpath(s, '//*[@style="display:none"]')
        mutate_selector_del_xpath(s, '//div[contains(@class, "related-carousel")]')

#        self.logger.debug("after mutate_selector: %s" % str(s.xpath('//div[contains(@class, "related-carousel")]')))

        l = NewsLoader(selector=s)

#        self.logger.debug("loader selector: %s" % str(l.selector.xpath('//div[contains(@class, "related-carousel")]')))


        # Get alternative to RSS-source URL fluff
        l.add_xpath('url', 'head/link[@rel="canonical"]/@href')

        # Sort out bylines with less fluff
        l.add_xpath('bylines',
                    'head/meta[@property="article:author"]/@content',
                    MapCompose(split_multiple_byline_string,
                               lambda l: (re.sub(r' [fF]or (Dailymail.com|The Daily Mail|Daily Mail Australia|MailOnline)', r'', x) for x in l)
                              )
                   )


        # Add a number of items of data that should be standardised across
        # providers. Can override these (for TakeFirst() fields) by making
        # l.add_* calls above this line, or supplement gaps by making them
        # below.
        l.add_fromresponse(response)
        l.add_htmlmeta()
        l.add_schemaorg(response)
        l.add_opengraph()

        # TODO: JS dross in body; might need a standard solution to keep this
        #       out.
        # TODO: Related article dross in body. <div class=related-carousel>

        item = l.load_item()

#        self.logger.debug('bodytext', item['bodytext'])

        return item

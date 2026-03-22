import scrapy


class PolicyDocument(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    source = scrapy.Field()       # e.g. "gov.cn", "ndrc", "beijing"
    published_date = scrapy.Field()
    raw_html = scrapy.Field()
    text_content = scrapy.Field()

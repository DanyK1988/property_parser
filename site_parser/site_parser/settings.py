BOT_NAME = "site_parser"

SPIDER_MODULES = ["site_parser.spiders"]
NEWSPIDER_MODULE = "site_parser.spiders"

AUTOTHROTTLE_ENABLED = True
ROBOTSTXT_OBEY=False
LOG_LEVEL="DEBUG"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

ITEM_PIPELINES = {
   'site_parser.pipelines.DatabasePipeline': 300,
}
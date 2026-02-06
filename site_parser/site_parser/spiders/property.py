from urllib.parse import urljoin
import scrapy
from fake_useragent import UserAgent
from scrapy.http import HtmlResponse


class PropertySpider(scrapy.Spider):
    '''
    Наследуемся от класса Spider и добавим свои методы и атрибуты
    '''
    name = 'property_spider'

    allowed_domains = ['intermark.ru']
    '''
        Список разрешённых доменов, чтобы паук не ушёл далеко от нужного сайта
    '''
    start_urls = ['https://intermark.ru/nedvizhimost-za-rubezhom/investicii-thailand']
    '''
        Стартовая страница, с которой начнётся парсинг
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ua = UserAgent()
        #self.search_url = 'Canggu' -- Пример поиска по конкретной локации

    def start_requests(self):
        for url in self.start_urls:
            # При старте берем рандомный UA
            yield scrapy.Request(url, headers={'User-Agent': self.ua.random})

    def parse(self, response: HtmlResponse):
        '''
        Метод парсинга главной страницы со списком объектов недвижимости
        Проходим по всем карточкам объектов
        '''
        for card in response.css('div.object-card'):
            # Извлекаем ссылку на детальную страницу
            detail_url = card.css('a.object-card-main-info__link::attr(href)').get()
            
            if detail_url:
                # Переходим на детальную страницу и вызываем parse_item
                yield response.follow(detail_url, self.parse_item, headers={'User-Agent': self.ua.random})
        
        # Пагинация - ищем ссылку на следующую страницу
        next_page = response.xpath('//a[contains(text(), " вперед ")]/@href').get()
        if next_page:
        # Переходим на следующую страницу и рекурсивно вызываем parse
            yield response.follow(next_page, self.parse)

            
    def parse_item(self, response):
        # Проверяем статус ответа
        if response.status != 200:
            self.logger.warning(f"Пропускаем страницу с кодом {response.status}: {response.url}")
            return  # Просто выходим, не возвращая item
    
        # Также проверяем наличие ключевых элементов
        if not response.css('h1::text').get():
            self.logger.warning(f"Пустая или некорректная страница: {response.url}")
            return
        
        # создаем словарь для хранения данных
        item = {}
        
        # 1. Заголовок H1
        item['h1'] = response.css('h1::text').get().strip()
        
        # 2. Название объекта
        item['title'] = response.css('div.title-object1 span::text').get().strip()
        
        # 3. Описание
        description_parts = response.css('div.with-styled-list p::text').getall()
        item['description'] = ' '.join([part.strip() for part in description_parts if part.strip()])
        
        # 4. Стоимость
        item['price_usd'] = response.css('div.chose-currency1__item .point:contains("usd") + ::attr(data-text1span)').get()
        if not item['price_usd']:
            item['price_usd'] = response.css('div.price-text1__title span::text').get().strip()
        
        # 5. Площадь
        area_text = response.css('div.small-information1__item.icon2::text').get().strip()
        if area_text:
            import re
            area_num = re.search(r'(\d+)', area_text)
            item['area'] = f"{area_num.group(1)} м²" if area_num else area_text.strip()
        
        # 6. Тип объекта
        type_text = response.css('div.small-information1__item.icon1::text').get().strip()
        if type_text:
            item['property_type'] = type_text.replace('Тип объекта:', '').strip()
        
        # 7. Страна
        item['country'] = response.css('div.title-object1 p::text').get().strip()
        
        # 8. ID объекта
        item['object_id'] = response.css('div.block-agent1::attr(data-obj_id)').get().strip()
        
        # 9. URL страницы
        item['url'] = response.url
        
        yield item


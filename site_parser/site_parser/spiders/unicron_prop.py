from selenium.common.exceptions import TimeoutException, NoSuchElementException
import scrapy
from scrapy.http import TextResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from scrapy.http import HtmlResponse
import datetime
import time


class PropertySpider(scrapy.Spider):
    name = "unicorn_property"

    def start_requests(self):
        self.logger.info("🚀 Старт паука")

        driver = webdriver.Chrome()
        wait = WebDriverWait(driver, 20)

        try:
            driver.get("https://unicorn-property.com")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid")))
            self.logger.info("Сетка загрузилась")

            cards = driver.find_elements(By.CSS_SELECTOR, "div.batchFadeYTarget")
            self.logger.info(f"Карточек найдено: {len(cards)}")

            if cards:
                try:
                    first_card_html = cards[0].get_attribute("outerHTML")
                    with open("debug_card_0.html", "w", encoding="utf-8") as f:
                        f.write(first_card_html)
                    self.logger.info("Сохранён debug_card_0.html — открой и посмотри структуру карточки")

                    # Также ищем любые <a> на всей странице (для теста)
                    all_links = driver.find_elements(By.CSS_SELECTOR, "a[href]")
                    self.logger.info(f"Всего ссылок <a> на странице: {len(all_links)}")
                    for idx, lnk in enumerate(all_links[:5]):  # первые 5 для примера
                        href = lnk.get_attribute("href")
                        text = lnk.text.strip()[:50]
                        self.logger.info(f"Ссылка {idx}: text='{text}' → {href}")
                except Exception as e:
                    self.logger.error(f"Ошибка при дампе карточки: {e}")

            for i in range(len(cards)):
                cards = driver.find_elements(By.CSS_SELECTOR, "div.batchFadeYTarget")
                if i >= len(cards): break
                card = cards[i]

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                time.sleep(1.5)

                try:
                    # Нативный клик с ховером (часто помогает с group-hover)
                    ActionChains(driver) \
                        .move_to_element(card) \
                        .pause(0.8) \
                        .click(card) \
                        .perform()

                    time.sleep(4)  # увеличил — модалки на React часто тормозят

                    # Ждём появления видимого диалога (самое важное!)
                    modal = wait.until(EC.visibility_of_element_located((
                        By.CSS_SELECTOR,
                        "[role='dialog']:not([hidden]):not([style*='display: none']), "
                        "[aria-modal='true'], "
                        "[data-headlessui-state='open'], "
                        "#headlessui-dialog-[open], "
                        ".modal, .dialog, [class*='modal-content'], [class*='dialog-content']"
                    )))

                    self.logger.info(f"Модалка открыта на карточке {i}!")

                    # Берём весь видимый контент модалки
                    modal_html = modal.get_attribute("outerHTML")

                    fake_url = driver.current_url + f"#detail-{i}"
                    

                    response = TextResponse(
                        url=fake_url,
                        body=modal_html,
                        encoding='utf-8'
                    )

                    yield from self.parse_item(response)

                    # Закрываем (ESC обычно работает в Headless UI)
                    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    time.sleep(2)

                except TimeoutException:
                    self.logger.warning(f"Модалка не появилась за 20с на карточке {i}")
                    driver.save_screenshot(f"timeout_card_{i}.png")
                    self.logger.info(f"Скриншот сохранён: timeout_card_{i}.png")

                except NoSuchElementException as e:
                    self.logger.error(f"Элемент не найден на карточке {i}: {e.msg}")
                except Exception as e:
                    self.logger.error(f"Неизвестная ошибка на {i}: {str(e)}")
                    driver.save_screenshot(f"error_card_{i}.png")
        finally:
            driver.quit()

    def parse_item(self, response):
        # Основной заголовок (уже работает)
        title_raw = response.css(
            "h1::text, h2::text, h3::text, "
            ".font-heading::text, div.text-xl::text, div.text-3xl::text, "
            "div.w-full.lg\\:text-center::text"  # из твоего примера на главной
        ).get(default="").strip()

        title = title_raw.strip() if title_raw else ""

        # Bedrooms — ищем "Bed :", "Br :", "Bedrooms :"
        bedrooms = response.css("::text").re_first(
            r'(?:Bed|Br|Bedrooms)\s*:\s*(\d+)'
        ) or None

        # Land Size — "Land :", "Land area :", "... SQM"
        land_size = response.css("::text").re_first(
            r'(?:Land|Land area|Plot)\s*:\s*([\d,]+\s*SQM?)'
        ) or None

        # Building Size — часто "Building :", "Living :", "Constructed area :"
        building_size = response.css("::text").re_first(
            r'(?:Building|Living|Constructed|Built-up|Floor)\s*area?\s*:\s*([\d,]+\s*SQM?)'
        ) or None

        # Area / Location — Canggu, Pererenan, Ubud, Uluwatu и т.д.
        # Обычно в заголовке или в отдельном блоке
        area_match = response.css("::text").re_first(
            r'(Canggu|Pererenan|Ubud|Seminyak|Uluwatu|Sanur|Jimbaran|Tabanan|Denpasar|Kuta)'
        )
        area = area_match if area_match else None

        # Если ничего не нашлось — можно fallback на title
        if not area and title:
            for loc in ["Canggu", "Pererenan", "Ubud", "Uluwatu"]:
                if loc.lower() in title.lower():
                    area = loc
                    break

        item = {
            "title": title,
            "bedrooms": bedrooms,
            "land_size": land_size,
            "building_size": building_size,
            "area": area,
            "parse_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        }

        # Только если хотя бы title есть
        if title:
            yield item
            self.logger.info(
                f"Спарсили объект: {title} | "
                f"Bed: {bedrooms} | Land: {land_size} | Build: {building_size} | Area: {area}"
            )
        else:
            self.logger.warning("Не удалось найти заголовок в модалке")
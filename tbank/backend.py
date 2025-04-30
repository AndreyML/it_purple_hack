import json
import openai
import aiohttp
import asyncio
from typing import List, Dict
from itertools import islice
import urllib.parse
import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API-ключ OpenAI из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")

class ImageSearch:
    """Поиск изображений товаров через Google Serper API"""
    
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    
    async def run(self, query: str) -> str:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "type": "images", "num": 1})
        headers = {'X-API-KEY': self.SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'images' in data and data['images']:
                            return data['images'][0]['imageUrl']
        except Exception as e:
            print(f"Ошибка при поиске изображения: {str(e)}")
        
        return f"https://via.placeholder.com/300x300?text={urllib.parse.quote(query)}"

image_searcher = ImageSearch()

def batch_items(items, batch_size):
    iterator = iter(items)
    while batch := list(islice(iterator, batch_size)):
        yield batch

def log_time(func):
    """Декоратор для логирования времени выполнения функций"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@log_time
async def chatgpt_request_async(messages: List[Dict]) -> str:
    """Асинхронно отправляет запрос к GPT с учетом истории диалога"""
    try:
        start_time = time.time()
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        logger.info(f"GPT request took {time.time() - start_time:.2f} seconds")
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error in GPT request: {str(e)}")
        return None

@log_time
async def analyze_products_batch(products_batch: list, query: str, initial_query: str, assistant_type: str) -> list:
    """Асинхронно анализирует батч товаров"""
    batch_size = len(products_batch)
    logger.info(f"Analyzing batch of {batch_size} products")
    
    # Формируем промпт в зависимости от типа ассистента
    if assistant_type == "Ассистент-стилист":
        criteria = """
        Критерии выбора:
        - Соответствие стилю и случаю
        - Сочетаемость с другими вещами
        - Размерный ряд
        - Качество и рейтинг
        - Соответствие бюджету
        """
    elif assistant_type == "Ассистент-косметолог":
        criteria = """
        Критерии выбора:
        - Соответствие типу кожи
        - Решение заявленных проблем
        - Состав и безопасность
        - Сочетаемость с другими средствами
        - Соответствие бюджету
        """
    elif assistant_type == "Ассистент-нутрициолог":
        criteria = """
        Критерии выбора:
        - Пищевая ценность
        - Соответствие диетическим требованиям
        - Качество и свежесть
        - Сбалансированность
        - Соответствие бюджету
        """
    else:  # Ассистент-дизайнер
        criteria = """
        Критерии выбора:
        - Соответствие стилю интерьера
        - Сочетаемость с другими элементами
        - Функциональность
        - Качество и рейтинг
        - Соответствие бюджету
        """
    
    search_prompt = f"""
    На основе диалога с пользователем:
    Изначальный запрос: {initial_query}
    Дополнительная информация: {query}
    
    {criteria}
    
    Проанализируй список товаров и выбери те, которые подходят под запрос пользователя.
    
    Список товаров (в формате JSON):
    {json.dumps(products_batch, ensure_ascii=False)}
    
    Верни только номера подходящих товаров (считая от 1) через запятую.
    Пример: 1,3,5,7
    """
    
    start_time = time.time()
    response = await chatgpt_request_async([
        {"role": "system", "content": "Ты - эксперт по подбору товаров. Твоя задача - найти наиболее подходящие товары из списка."},
        {"role": "user", "content": search_prompt}
    ])
    logger.info(f"GPT analysis for batch took {time.time() - start_time:.2f} seconds")
    
    try:
        return [int(idx.strip()) for idx in response.split(',')]
    except:
        return []

@log_time
async def get_assistant_recommendations_async(products: list, query: str, assistant_type: str, system_prompt: str) -> str:
    """Асинхронно получает рекомендации от ассистента"""
    if not products:
        return "К сожалению, я не нашел подходящих товаров. Давайте уточним параметры поиска?"
    
    products_description = format_products_description(products)
    
    # Используем специфичный для каждого ассистента промпт
    if assistant_type == "Ассистент-стилист":
        recommendation_prompt = f"""
        На основе этих товаров:
        {products_description}
        
        Запрос пользователя: {query}
        
        Дай готовые рекомендации по подбору одежды. НЕ задавай дополнительных вопросов в конце.
        
        1. Если пользователь собирает капсульный гардероб:
           - Предложи, как сочетать эти вещи между собой
           - Укажи, какие еще базовые вещи нужно добавить
           - Дай советы по созданию разных образов
        
        2. Если пользователь ищет конкретный "лук":
           - Подбери комплект с учетом найденных товаров
           - Предложи альтернативные сочетания
           - Дай рекомендации по аксессуарам
        
        Важно: дай готовые рекомендации, не задавай вопросов в конце ответа.
        """
    elif assistant_type == "Ассистент-косметолог":
        recommendation_prompt = f"""
        На основе этих товаров:
        {products_description}
        
        Запрос пользователя: {query}
        
        Дай готовые рекомендации по уходу за кожей. НЕ задавай дополнительных вопросов в конце.
        
        1. Составь программу ухода:
           - Распиши последовательность применения средств
           - Укажи частоту использования
           - Отметь особенности применения
        
        2. Дай рекомендации:
           - Как сочетать средства между собой
           - Какие дополнительные средства могут понадобиться
           - Предупреждения и противопоказания
        
        Важно: дай готовые рекомендации, не задавай вопросов в конце ответа.
        """
    elif assistant_type == "Ассистент-нутрициолог":
        recommendation_prompt = f"""
        На основе этих товаров:
        {products_description}
        
        Запрос пользователя: {query}
        
        Дай готовые рекомендации по питанию. НЕ задавай дополнительных вопросов в конце.
        
        1. Проанализируй состав продуктовой корзины:
           - Рассчитай примерное КБЖУ
           - Оцени сбалансированность
           - Предложи корректировки
        
        2. Дай рекомендации:
           - Как распределить продукты по приемам пищи
           - Какие продукты добавить для баланса
           - Простые рецепты из этих продуктов
        
        Важно: дай готовые рекомендации, не задавай вопросов в конце ответа.
        """
    else:  # Ассистент-дизайнер
        recommendation_prompt = f"""
        На основе этих товаров:
        {products_description}
        
        Запрос пользователя: {query}
        
        Дай готовые рекомендации по дизайну интерьера. НЕ задавай дополнительных вопросов в конце.
        
        1. Предложи варианты размещения:
           - Как сочетать предметы между собой
           - Варианты расстановки
           - Цветовые решения
        
        2. Дай рекомендации:
           - Какие элементы добавить для завершенности
           - Как обыграть особенности помещения
           - Практические советы по уходу
        
        Важно: дай готовые рекомендации, не задавай вопросов в конце ответа.
        """
    
    start_time = time.time()
    recommendation = await chatgpt_request_async([
        {"role": "system", "content": system_prompt + "\nВажно: давай готовые рекомендации, не задавай вопросов в конце ответа."},
        {"role": "user", "content": recommendation_prompt}
    ])
    logger.info(f"Getting GPT recommendations took {time.time() - start_time:.2f} seconds")
    
    return f"{recommendation}\n\nМогу показать фотографии любого товара - просто укажите его номер."

@log_time
async def process_user_query_async(query: str, assistant_type: str, initial_query: str, system_prompt: str, waiting_for_clarification: bool = False):
    """Асинхронная обработка запроса пользователя"""
    try:
        logger.info(f"Starting async query processing at {datetime.now()}")
        if waiting_for_clarification:
            # Если это ответ на уточняющие вопросы, сразу ищем товары
            return await process_clarification_async(query, initial_query, assistant_type, system_prompt)
        else:
            # Если это новый запрос, генерируем уточняющие вопросы
            return await generate_questions_async(query, assistant_type)
    except Exception as e:
        logger.error(f"Error in async query processing: {str(e)}")
        return {
            "type": "error",
            "text": f"Извините, произошла ошибка при обработке запроса: {str(e)}"
        }

@log_time
async def process_clarification_async(query: str, initial_query: str, assistant_type: str, system_prompt: str):
    """Асинхронная обработка ответа на уточняющий вопрос"""
    start_load = time.time()
    all_products = load_products("wb_data.json")
    logger.info(f"Loading products took {time.time() - start_load:.2f} seconds")
    
    batch_size = 150
    total_products = len(all_products)
    logger.info(f"Processing {total_products} products in batches of {batch_size}")
    
    # Создаем и запускаем задачи для всех батчей одновременно
    start_batch = time.time()
    tasks = [
        analyze_products_batch(
            all_products[i:i+batch_size],
            query,
            initial_query,
            assistant_type
        )
        for i in range(0, len(all_products), batch_size)
    ]
    
    # Асинхронно получаем все результаты
    batch_results = await asyncio.gather(*tasks)
    logger.info(f"Batch processing took {time.time() - start_batch:.2f} seconds")
    
    # Собираем все найденные товары
    start_collect = time.time()
    selected_products = []
    for batch_idx, indices in enumerate(batch_results):
        batch_start = batch_idx * batch_size
        batch = all_products[batch_start:batch_start+batch_size]
        selected_products.extend([batch[idx-1] for idx in indices if 0 < idx <= len(batch)])
    logger.info(f"Collecting results took {time.time() - start_collect:.2f} seconds")
    logger.info(f"Found {len(selected_products)} matching products")
    
    if selected_products:
        start_rec = time.time()
        recommendations = await get_assistant_recommendations_async(
            selected_products,
            query,
            assistant_type,
            system_prompt
        )
        logger.info(f"Getting recommendations took {time.time() - start_rec:.2f} seconds")
        return {
            "type": "recommendations",
            "text": recommendations,
            "search_results": selected_products
        }
    else:
        return {
            "type": "no_results",
            "text": "К сожалению, я не нашел подходящих товаров. Давайте попробуем поискать что-то похожее?"
        }

@log_time
async def generate_questions_async(query: str, assistant_type: str):
    """Асинхронно генерирует уточняющие вопросы"""
    # Формируем промпт в зависимости от типа ассистента
    if assistant_type == "Ассистент-стилист":
        clarification_prompt = f"""
        Запрос пользователя: {query}
        
        Сгенерируй 2-3 важных уточняющих вопроса для подбора одежды:
        1. О стиле и случае использования
        2. О предпочтениях в одежде
        3. О бюджете
        
        Вопросы должны быть конкретными и помочь в подборе товаров.
        """
    elif assistant_type == "Ассистент-косметолог":
        clarification_prompt = f"""
        Запрос пользователя: {query}
        
        Сгенерируй 2-3 важных уточняющих вопроса для подбора косметики:
        1. О типе кожи и проблемах
        2. О текущем уходе
        3. О бюджете
        
        Вопросы должны быть конкретными и помочь в подборе средств.
        """
    elif assistant_type == "Ассистент-нутрициолог":
        clarification_prompt = f"""
        Запрос пользователя: {query}
        
        Сгенерируй 2-3 важных уточняющих вопроса для подбора продуктов:
        1. О целях питания
        2. О пищевых ограничениях
        3. О бюджете
        
        Вопросы должны быть конкретными и помочь в подборе продуктов.
        """
    else:  # Ассистент-дизайнер
        clarification_prompt = f"""
        Запрос пользователя: {query}
        
        Сгенерируй 2-3 важных уточняющих вопроса для подбора товаров для интерьера:
        1. О стиле помещения
        2. О функциональных потребностях
        3. О бюджете
        
        Вопросы должны быть конкретными и помочь в подборе товаров.
        """
    
    questions = await chatgpt_request_async([
        {"role": "system", "content": "Ты - эксперт по работе с клиентами"},
        {"role": "user", "content": clarification_prompt}
    ])
    
    return {
        "type": "questions",
        "text": questions
    }

async def search_product_image(query: str) -> str:
    return await image_searcher.run(query)

@log_time
async def process_batch(batch: List[Dict], budget: int, preferences: dict) -> List[Dict]:
    """Асинхронно обрабатывает батч товаров"""
    batch_size = len(batch)
    logger.info(f"Processing batch of {batch_size} products")
    products_description = format_batch_description(batch)
    
    prompt = f"""
    Запрос пользователя:
    - Что ищет: {preferences.get('preferences', 'любой товар')}
    - Размер: {preferences.get('size', 'любой')}
    - Цвет: {preferences.get('color', 'любой')}
    - Бренд: {preferences.get('brand', 'любой')}
    - Пол: {preferences.get('gender', 'любой')}
    - Максимальный бюджет: {budget / 100:.2f} руб.
    
    Список товаров:
    {products_description}
    
    Проанализируй товары и верни номера тех, которые подходят под запрос пользователя и не превышают бюджет.
    Отвечай только номерами через запятую, например: 1,3,5. Если подходящих товаров нет, верни 'нет'.
    """
    
    response = await chatgpt_request_async([
        {"role": "system", "content": "Ты - эксперт по подбору товаров. Твоя задача - найти наиболее подходящие товары из списка."},
        {"role": "user", "content": prompt}
    ])
    
    if not response or response.lower() == 'нет':
        return []
    
    try:
        selected_indices = [int(idx.strip()) for idx in response.split(',')]
        return [batch[idx - 1] for idx in selected_indices if 1 <= idx <= len(batch)]
    except ValueError:
        print(f"Ошибка при обработке ответа GPT: {response}")
        return []

def format_batch_description(batch: List[Dict]) -> str:
    """Форматирует описание батча товаров"""
    return "\n".join(
        f"""
        Товар {idx + 1}:
        - Название: {product['brand']} {product['name']}
        - Цена: {min(size["price"]["total"] for size in product["sizes"]) / 100:.2f} руб.
        - Размеры: {", ".join(size.get('origName', '') for size in product["sizes"])}
        - Рейтинг: {product['rating']}
        """
        for idx, product in enumerate(batch)
    )

@log_time
async def filter_products_async(products: List[Dict], budget: int, preferences: dict) -> List[Dict]:
    """Асинхронно фильтрует все товары"""
    start_time = time.time()
    BATCH_SIZE = 150
    total_products = len(products)
    logger.info(f"Starting to filter {total_products} products in batches of {BATCH_SIZE}")
    
    # Разбиваем товары на батчи и создаем задачи
    tasks = [
        process_batch(products[i:i+BATCH_SIZE], budget, preferences)
        for i in range(0, len(products), BATCH_SIZE)
    ]
    
    # Асинхронно обрабатываем все батчи
    results = await asyncio.gather(*tasks)
    
    # Объединяем результаты
    filtered_products = [product for batch_results in results for product in batch_results]
    logger.info(f"Filtering completed in {time.time() - start_time:.2f} seconds. Found {len(filtered_products)} products")
    return filtered_products

def format_products_description(products: list) -> str:
    """Форматирует описание товаров"""
    description = ""
    for idx, product in enumerate(products, 1):
        min_price = min(size['price']['total'] for size in product['sizes'])
        description += f"{idx}. {product['brand']} - {product['name']}\n"
        description += f"   💰 Цена: {min_price/100:.2f} ₽\n"
        description += f"   ⭐ Рейтинг: {product['rating']}\n"
        sizes = [str(size.get('origName', 'N/A')) for size in product['sizes']]
        description += f"   📏 Размеры: {', '.join(sizes)}\n\n"
    return description

def filter_products(products: List[Dict], filters: Dict) -> List[Dict]:
    """
    Фильтрует товары по заданным критериям
    """
    filtered = products
    
    if filters.get("category"):
        filtered = [p for p in filtered if filters["category"].lower() in p["name"].lower()]
    
    if filters.get("price_max"):
        filtered = [p for p in filtered if min(s["price"]["total"] for s in p["sizes"]) <= filters["price_max"]]
    
    if filters.get("brand"):
        filtered = [p for p in filtered if filters["brand"].lower() in p["brand"].lower()]
    
    return filtered

def clean_product_data(product: Dict) -> Dict:
    """
    Очищает данные о товаре, оставляя только необходимые поля
    """
    cleaned = {
        "id": product.get("id"),
        "brand": product.get("brand"),
        "name": product.get("name"),
        "rating": product.get("rating"),
        "sizes": []
    }
    
    # Очищаем информацию о размерах
    for size in product.get("sizes", []):
        cleaned_size = {
            "origName": size.get("origName"),
            "price": {
                "total": size.get("price", {}).get("total", 0)
            }
        }
        cleaned["sizes"].append(cleaned_size)
    
    return cleaned

def clean_products_data(products: List[Dict]) -> List[Dict]:
    """
    Очищает список товаров, удаляя ненужные поля
    """
    return [clean_product_data(product) for product in products]

def load_products(filename: str) -> List[Dict]:
    """
    Загружает и очищает данные о товарах из JSON файла
    """
    start_time = time.time()
    logger.info(f"Starting to load and clean products from {filename}")
    
    with open(filename, "r", encoding="utf-8") as file:
        raw_products = json.load(file)
    
    logger.info(f"Loaded {len(raw_products)} raw products")
    
    # Очищаем данные
    cleaned_products = clean_products_data(raw_products)
    
    # Сохраняем очищенные данные в новый файл
    cleaned_filename = filename.replace(".json", "_cleaned.json")
    with open(cleaned_filename, "w", encoding="utf-8") as file:
        json.dump(cleaned_products, file, ensure_ascii=False, indent=2)
    
    logger.info(f"Cleaned and saved {len(cleaned_products)} products to {cleaned_filename}")
    logger.info(f"Loading and cleaning took {time.time() - start_time:.2f} seconds")
    
    return cleaned_products
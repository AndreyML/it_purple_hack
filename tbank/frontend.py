import streamlit as st
from backend import (
    filter_products,
    load_products,
    search_product_image,
    process_user_query_async,
    chatgpt_request_async
)
import json
import asyncio
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_time(func):
    """Декоратор для логирования времени выполнения функций"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

# Настройка страницы
st.set_page_config(page_title="🛒 Shopping Assistant", layout="wide")

# Выбор ассистента
assistant_type = st.selectbox(
    "Выберите ассистента", 
    ["Ассистент-стилист", "Ассистент-косметолог", "Ассистент-нутрициолог", "Ассистент-дизайнер"]
)

# Инициализация состояния для каждого типа ассистента
if 'assistant_prompts' not in st.session_state:
    st.session_state.assistant_prompts = {
        "Ассистент-стилист": {
            "system": """Ты - опытный персональный стилист. Веди естественный диалог, задавай уместные вопросы и анализируй ответы клиента.

Твои основные задачи:
1. Собрать капсульный гардероб:
   - Узнай образ жизни, предпочтения и бюджет клиента
   - Подбери базовые вещи с учетом сезона
   - Предложи варианты сочетаний
   
2. Создать готовые образы:
   - Выясни случай (работа/отдых/праздник)
   - Учти стиль и комфорт клиента
   - Предложи аксессуары

При общении:
- Задавай открытые вопросы о стиле жизни и предпочтениях
- Объясняй свои рекомендации
- Предлагай альтернативы
- Учитывай уже имеющиеся вещи

Всегда ищи товары в базе данных и указывай конкретные модели с ценами.""",
            "greeting": """Привет! Я ваш персональный стилист. Расскажите, что вас привело ко мне - хотите собрать капсульный гардероб или подобрать конкретный образ? 

Поделитесь немного информацией о вашем стиле жизни и предпочтениях в одежде."""
        },
        "Ассистент-косметолог": {
            "system": """Ты - профессиональный косметолог. Веди естественный диалог, задавай уместные вопросы для понимания потребностей клиента.

Твои основные задачи:
1. Анализ состояния кожи:
   - Определи тип кожи и проблемы
   - Учти образ жизни и привычки
   - Выясни аллергии и противопоказания

2. Подбор программы ухода:
   - Составь пошаговую рутину
   - Подбери средства под бюджет
   - Объясни применение

При общении:
- Задавай вопросы о состоянии кожи и образе жизни
- Объясняй назначение каждого средства
- Учитывай сезон и климат
- Предупреждай о возможных реакциях

Всегда ищи конкретные средства в базе данных и проверяй их совместимость.""",
            "greeting": """Здравствуйте! Я ваш персональный косметолог. Расскажите, что вас беспокоит в состоянии кожи? 

Поделитесь информацией о вашем текущем уходе и образе жизни, чтобы я мог(ла) подобрать оптимальную программу."""
        },
        "Ассистент-нутрициолог": {
            "system": """Ты - опытный нутрициолог. Веди естественный диалог, задавай уместные вопросы для составления персонализированного рациона.

Твои основные задачи:
1. Анализ потребностей:
   - Определи цели (снижение веса/набор массы/здоровье)
   - Выясни ограничения и аллергии
   - Учти образ жизни и нагрузки

2. Составление рациона:
   - Рассчитай индивидуальное КБЖУ
   - Подбери продукты под бюджет
   - Составь меню по приемам пищи

При общении:
- Задавай вопросы о пищевых привычках и предпочтениях
- Объясняй роль разных продуктов
- Учитывай режим дня
- Давай практические советы

Всегда ищи конкретные продукты в базе данных и считай их пищевую ценность.""",
            "greeting": """Здравствуйте! Я ваш персональный нутрициолог. Расскажите о ваших целях в питании и текущих пищевых привычках. 

Также поделитесь информацией о вашем образе жизни и особенностях питания (аллергии, непереносимости)."""
        },
        "Ассистент-дизайнер": {
            "system": """Ты - креативный дизайнер интерьера. Веди естественный диалог, задавай уместные вопросы для создания идеального пространства.

Твои основные задачи:
1. Полное обустройство помещения:
   - Выясни назначение комнаты
   - Учти размеры и планировку
   - Подбери мебель и освещение

2. Создание сезонного декора:
   - Определи стиль и цветовую гамму
   - Подбери текстиль и аксессуары
   - Учти существующую обстановку

При общении:
- Задавай вопросы о стиле жизни и предпочтениях
- Объясняй принципы организации пространства
- Учитывай естественное освещение
- Предлагай практичные решения

Всегда ищи конкретные товары в базе данных и учитывай их размеры и сочетаемость.""",
            "greeting": """Здравствуйте! Я ваш персональный дизайнер интерьера. Расскажите о помещении, которое хотите обустроить, и о вашем видении идеального пространства. 

Поделитесь информацией о стиле жизни и как вы планируете использовать это помещение."""
        }
    }

# Инициализация состояния сессии
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": st.session_state.assistant_prompts[assistant_type]["greeting"]}
    ]
if 'product_images' not in st.session_state:
    st.session_state.product_images = {}
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'current_context' not in st.session_state:
    st.session_state.current_context = {
        "preferences": None,
        "budget": None,
        "size": None,
        "color": None,
        "brand": None,
        "gender": None
    }

@log_time
async def extract_search_params(query: str, assistant_type: str) -> dict:
    """Асинхронно извлекает параметры поиска из запроса пользователя"""
    extract_prompt = f"""
    Извлеки из запроса пользователя параметры для поиска товаров.
    Запрос: {query}
    
    Верни ответ в формате JSON:
    {{
        "preferences": "что ищет",
        "budget": число в рублях или null,
        "size": размер или null,
        "color": цвет или null,
        "brand": бренд или null,
        "gender": "Мужской"/"Женский" или null
    }}
    """
    
    response = await chatgpt_request_async([
        {"role": "system", "content": st.session_state.assistant_prompts[assistant_type]["system"]},
        {"role": "user", "content": extract_prompt}
    ])
    
    try:
        params = json.loads(response)
    except:
        params = {
            "preferences": query,
            "budget": None,
            "size": None,
            "color": None,
            "brand": None,
            "gender": None
        }
    
    return params

@log_time
async def get_assistant_recommendations(products: list, query: str, assistant_type: str) -> str:
    """Асинхронно получает рекомендации от ассистента"""
    if not products:
        return "К сожалению, я не нашел подходящих товаров. Давайте уточним параметры поиска?"
    
    products_description = format_products_description(products)
    recommendation_prompt = get_recommendation_prompt(products_description, query, assistant_type)
    
    recommendation = await chatgpt_request_async([
        {"role": "system", "content": st.session_state.assistant_prompts[assistant_type]["system"]},
        {"role": "user", "content": recommendation_prompt}
    ])

    return f"Мои рекомендации:\n{recommendation}"

def get_recommendation_prompt(products_description: str, query: str, assistant_type: str) -> str:
    """Возвращает промпт для рекомендаций в зависимости от типа ассистента"""
    base_prompt = f"""
    На основе этих товаров:
    {products_description}
    
    Запрос пользователя: {query}
    """
    
    if assistant_type == "Ассистент-стилист":
        return base_prompt + """
        1. Если пользователь собирает капсульный гардероб:
           - Предложи, как сочетать эти вещи между собой
           - Укажи, какие еще базовые вещи нужно добавить
           - Дай советы по созданию разных образов
        
        2. Если пользователь ищет конкретный "лук":
           - Подбери комплект с учетом найденных товаров
           - Предложи альтернативные сочетания
           - Дай рекомендации по аксессуарам
        """
    elif assistant_type == "Ассистент-косметолог":
        return base_prompt + """
        1. Составь программу ухода:
           - Распиши последовательность применения средств
           - Укажи частоту использования
           - Отметь особенности применения
        
        2. Дай рекомендации:
           - Как сочетать средства между собой
           - Какие дополнительные средства могут понадобиться
           - Предупреждения и противопоказания
        """
    elif assistant_type == "Ассистент-нутрициолог":
        return base_prompt + """
        1. Проанализируй состав продуктовой корзины:
           - Рассчитай примерное КБЖУ
           - Оцени сбалансированность
           - Предложи корректировки
        
        2. Дай рекомендации:
           - Как распределить продукты по приемам пищи
           - Какие продукты добавить для баланса
           - Простые рецепты из этих продуктов
        """
    else:  # Ассистент-дизайнер
        return base_prompt + """
        1. Предложи варианты размещения:
           - Как сочетать предметы между собой
           - Варианты расстановки
           - Цветовые решения
        
        2. Дай рекомендации:
           - Какие элементы добавить для завершенности
           - Как обыграть особенности помещения
           - Практические советы по уходу
        """

@log_time
async def analyze_products_batch(products_batch: list, query: str, initial_query: str, assistant_type: str) -> list:
    """Асинхронно анализирует батч товаров"""
    search_prompt = f"""
    На основе диалога с пользователем:
    Изначальный запрос: {initial_query}
    Дополнительная информация: {query}
    
    Проанализируй список товаров и выбери те, которые подходят под запрос пользователя.
    
    Список товаров (в формате JSON):
    {json.dumps(products_batch, ensure_ascii=False)}
    
    Верни только номера подходящих товаров (считая от 1) через запятую.
    Пример: 1,3,5,7
    """
    
    selected_indices = await chatgpt_request_async([
        {"role": "system", "content": "Ты - эксперт по подбору товаров. Твоя задача - найти наиболее подходящие товары из списка."},
        {"role": "user", "content": search_prompt}
    ])
    
    try:
        return [int(idx.strip()) for idx in selected_indices.split(',')]
    except:
        return []

@log_time
async def process_user_query(query: str, assistant_type: str):
    """Асинхронная обработка запроса пользователя"""
    try:
        logger.info(f"Starting query processing at {datetime.now()}")
        if "waiting_for_clarification" in st.session_state and st.session_state.waiting_for_clarification:
            return await process_clarification_response(query, assistant_type)
        else:
            return await process_new_query(query, assistant_type)
    except Exception as e:
        logger.error(f"Error in process_user_query: {str(e)}")
        return f"Извините, произошла ошибка при обработке запроса: {str(e)}"

@log_time
async def process_clarification_response(query: str, assistant_type: str):
    """Асинхронная обработка ответа на уточняющий вопрос"""
    start_load = time.time()
    all_products = load_products("wb_data.json")
    logger.info(f"Loading products took {time.time() - start_load:.2f} seconds")
    
    batch_size = 100000
    total_products = len(all_products)
    logger.info(f"Processing {total_products} products in batches of {batch_size}")
    
    # Создаем и запускаем задачи для всех батчей одновременно
    start_batch = time.time()
    tasks = [
        analyze_products_batch(
            all_products[i:i+batch_size],
            query,
            st.session_state.initial_query,
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
        st.session_state.search_results = selected_products
        return await get_assistant_recommendations(selected_products, query, assistant_type)
    else:
        return "К сожалению, я не нашел подходящих товаров. Давайте попробуем поискать что-то похожее?"

@log_time
async def process_new_query(query: str, assistant_type: str):
    """Асинхронная обработка нового запроса"""
    st.session_state.initial_query = query
    
    clarification_prompt = f"""
    Запрос пользователя: {query}
    Тип ассистента: {assistant_type}
    
    Сгенерируй 2-3 важных уточняющих вопроса, чтобы лучше понять потребности пользователя.
    Вопросы должны быть конкретными и помочь в подборе товаров.
    """
    
    questions = await chatgpt_request_async([
        {"role": "system", "content": "Ты - эксперт по работе с клиентами"},
        {"role": "user", "content": clarification_prompt}
    ])
    
    st.session_state.waiting_for_clarification = True
    st.session_state.temp_context = {
        "initial_query": query,
        "assistant_type": assistant_type
    }
    
    return questions

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

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if content.startswith("SHOW_IMAGE:"):
            product_id = content.split(":")[1]
            if product_id in st.session_state.product_images:
                st.image(st.session_state.product_images[product_id], use_column_width=True)
        else:
            st.markdown(content)

# Поле ввода сообщения
if prompt := st.chat_input("Введите ваш запрос..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            if any(word in prompt.lower() for word in ["фото", "фотография", "картинка", "покажи"]):
                try:
                    product_idx = int(prompt.split()[-1]) - 1
                    if 0 <= product_idx < len(st.session_state.search_results):
                        product = st.session_state.search_results[product_idx]
                        product_id = f"{product['brand']}_{product['name']}"
                        
                        if product_id not in st.session_state.product_images:
                            image_url = asyncio.run(search_product_image(f"{product['brand']} {product['name']}"))
                            st.session_state.product_images[product_id] = image_url
                        
                        st.session_state.messages.append({"role": "assistant", "content": f"SHOW_IMAGE:{product_id}"})
                        st.image(st.session_state.product_images[product_id], use_column_width=True)
                    else:
                        response_text = "Товара с таким номером нет в списке. Пожалуйста, выберите номер из показанных товаров."
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        st.markdown(response_text)
                except (ValueError, IndexError):
                    response_text = "Пожалуйста, укажите номер товара, фотографию которого хотите посмотреть."
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    st.markdown(response_text)
            else:
                # Получаем системный промпт для текущего типа ассистента
                system_prompt = st.session_state.assistant_prompts[assistant_type]["system"]
                
                # Определяем, ждем ли мы уточняющего ответа
                waiting_for_clarification = st.session_state.get("waiting_for_clarification", False)
                
                # Получаем начальный запрос
                initial_query = st.session_state.get("initial_query", prompt)
                
                response = asyncio.run(
                    process_user_query_async(
                        query=prompt,
                        assistant_type=assistant_type,
                        initial_query=initial_query,
                        system_prompt=system_prompt,
                        waiting_for_clarification=waiting_for_clarification
                    )
                )
                
                # Обрабатываем структурированный ответ
                if response["type"] == "questions":
                    # Если это уточняющие вопросы
                    st.session_state.waiting_for_clarification = True
                    st.session_state.initial_query = prompt
                elif response["type"] == "recommendations":
                    # Если это рекомендации с товарами
                    st.session_state.waiting_for_clarification = False
                    st.session_state.search_results = response.get("search_results", [])
                else:
                    # Если это ошибка или нет результатов
                    st.session_state.waiting_for_clarification = False
                
                st.session_state.messages.append({"role": "assistant", "content": response["text"]})
                st.markdown(response["text"])
    
# Кнопка для очистки истории
if st.sidebar.button("Очистить историю"):
    st.session_state.messages = [
        {"role": "assistant", "content": st.session_state.assistant_prompts[assistant_type]["greeting"]}
    ]
    st.session_state.product_images = {}
    st.session_state.search_results = None
    st.session_state.current_context = {
        "preferences": None,
        "budget": None,
        "size": None,
        "color": None,
        "brand": None,
        "gender": None
    }
    st.rerun()
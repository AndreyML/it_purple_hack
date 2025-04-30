# 🚀 Project Schedule Optimizer

Demo: http://195.26.226.73:8502/
Интеллектуальная система оптимизации календарного плана проекта с использованием LLM и современных веб-технологий.

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-red.svg)
![Docker](https://img.shields.io/badge/Docker-🐳-blue.svg)

## 📋 Описание

Система позволяет оптимизировать календарный план проекта, учитывая:
- Длительность задач
- Зависимости между задачами
- Доступность ресурсов
- Ограничения по датам
- Рабочий календарь проекта

### ✨ Особенности

- 🤖 Использование LLM для интеллектуальной оптимизации
- 📊 Интерактивная визуализация результатов (диаграмма Ганта)
- 🎚️ Настраиваемые веса оптимизации
- 🔄 Сравнение исходного и оптимизированного планов
- 🐳 Полная Docker-изация приложения
- 🌐 Современный веб-интерфейс

## 🛠 Технологии

- **Backend**: FastAPI, LLM
- **Frontend**: Streamlit
- **Визуализация**: Plotly
- **Контейнеризация**: Docker, Docker Compose
- **Дополнительно**: Pandas, Pydantic

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- OpenAI API ключ

### Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/project-scheduler.git
cd project-scheduler
```

2. Создайте файл `.env` и добавьте ваш OpenAI API ключ:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

3. Запустите приложение:
```bash
docker-compose up --build
```

4. Откройте в браузере:
- Frontend (Streamlit): http://localhost:8501
- API (FastAPI): http://localhost:8000/docs

## 📝 Формат входных данных

Система принимает JSON-файл следующей структуры:

```json
{
    "tasks": [
        {
            "id": 1,
            "duration": 5,
            "role": "developer",
            "constraintType": "startnoearlierthan",
            "constraintDate": "2024-02-07T15:22:07",
            "dependencies": []
        }
    ],
    "resources": [
        {
            "id": 1,
            "role": "developer",
            "calendar": ["2024-02-10", "2024-02-11"]
        }
    ],
    "projectCalendar": {
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "holidays": ["2024-02-23"]
    }
}
```

## ⚙️ Параметры оптимизации

- **Вес длительности** (0.0-1.0): влияет на приоритет минимизации общей длительности проекта
- **Вес ресурсов** (0.0-1.0): влияет на приоритет минимизации количества используемых ресурсов

## 📊 Результаты оптимизации

Система предоставляет:
- Оптимизированное расписание задач
- Диаграмму Ганта
- Сравнение метрик до/после оптимизации
- Список использованных ресурсов
- Общую длительность проекта

## 🔧 Разработка

### Локальный запуск без Docker

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервисы:
```bash
# Terminal 1 - API
uvicorn api:app --reload

# Terminal 2 - Frontend
streamlit run app.py
```

### Тестирование изменений

```bash
# Пересборка с изменениями
docker-compose up --build

# Просмотр логов
docker-compose logs -f
```

## 📜 Лицензия

MIT License - подробности в файле [LICENSE](LICENSE)

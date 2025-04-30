# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Открываем порт для Streamlit
EXPOSE 8503

# Запускаем приложение
CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=8503"] 
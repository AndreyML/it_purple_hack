import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
from datetime import datetime, timedelta
import os

# Получаем адрес API из переменной окружения или используем значение по умолчанию
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_ENDPOINT = f"{API_URL}/optimize"

def analyze_initial_project(data):
    """Анализирует исходные данные проекта."""
    # Обработка различных форматов JSON
    if isinstance(data, str):
        data = json.loads(data)
    
    # Получаем задачи из разных возможных структур
    tasks = []
    if "tasks" in data:
        if isinstance(data["tasks"], list):
            tasks = data["tasks"]
        elif isinstance(data["tasks"], dict) and "rows" in data["tasks"]:
            tasks = data["tasks"]["rows"]
    
    # Получаем ресурсы из разных возможных структур
    resources = []
    if "resources" in data:
        if isinstance(data["resources"], list):
            resources = data["resources"]
        elif isinstance(data["resources"], dict) and "rows" in data["resources"]:
            resources = data["resources"]["rows"]
    
    # Если ресурсы не найдены, собираем уникальные роли из задач
    if not resources:
        unique_roles = set()
        for task in tasks:
            if isinstance(task, dict) and "role" in task:
                unique_roles.add(task["role"])
        resources = [{"role": role} for role in unique_roles]
    
    # Подсчет общей длительности
    total_duration = sum(float(task.get("duration", 0)) for task in tasks if isinstance(task, dict))
    
    # Подсчет уникальных ресурсов
    unique_roles = set(resource.get("role") for resource in resources if isinstance(resource, dict))
    resource_count = len(unique_roles)
    
    return {
        "total_duration_days": total_duration,
        "resource_count": resource_count,
        "tasks": tasks,
        "resources": resources
    }

st.title("Оптимизация календарного плана проекта")

# Пример JSON для демонстрации структуры
example_json = {
    "tasks": [
        {
            "id": 1,
            "duration": 5,
            "role": "developer",
            "constraintType": "startnoearlierthan",
            "constraintDate": "2024-02-07T15:22:07",
            "dependencies": []
        },
        {
            "id": 2,
            "duration": 3,
            "role": "designer",
            "constraintType": None,
            "constraintDate": None,
            "dependencies": [1]
        }
    ],
    "resources": [
        {
            "id": 1,
            "role": "developer",
            "calendar": ["2024-02-10", "2024-02-11"]
        },
        {
            "id": 2,
            "role": "designer",
            "calendar": []
        }
    ],
    "projectCalendar": {
        "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "holidays": ["2024-02-23"]
    }
}

with st.expander("Показать пример JSON структуры"):
    st.json(example_json)

uploaded_file = st.file_uploader("Загрузите JSON с задачами", type=["json"])

# Ползунки для задания весов оптимизации
weight_duration = st.slider("Вес минимизации длительности проекта", 0.0, 1.0, 0.7, 0.1)
weight_resources = st.slider("Вес минимизации числа исполнителей", 0.0, 1.0, 0.3, 0.1)

if uploaded_file is not None:
    try:
        project_data = json.load(uploaded_file)
        
        # Анализируем исходные данные
        initial_analysis = analyze_initial_project(project_data)
        
        # Нормализуем данные проекта
        normalized_data = {
            "tasks": initial_analysis["tasks"],
            "resources": initial_analysis["resources"],
            "projectCalendar": {
                "workingDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "holidays": []
            },
            "constraints": {
                "weights": {
                    "duration": weight_duration,
                    "resources": weight_resources
                }
            }
        }
        
        st.subheader("Исходные данные проекта:")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Исходная длительность (дней)", f"{initial_analysis['total_duration_days']:.1f}")
        with col2:
            st.metric("Исходное количество ресурсов", initial_analysis["resource_count"])
        
        st.json(normalized_data)
        
        if st.button("Оптимизировать расписание"):
            with st.spinner("Оптимизация..."):
                try:
                    response = requests.post(API_ENDPOINT, json=normalized_data, timeout=60)
                    response.raise_for_status()  # Проверяем статус ответа
                    schedule = response.json()
                    st.success("Оптимизация завершена!")
                    
                    # Отображаем результаты оптимизации
                    st.subheader("Результаты оптимизации:")
                    
                    # Сравнение метрик
                    col1, col2 = st.columns(2)
                    with col1:
                        duration_diff = float(schedule["total_duration_days"]) - initial_analysis["total_duration_days"]
                        st.metric(
                            "Длительность проекта (дней)", 
                            f"{float(schedule['total_duration_days']):.1f}",
                            delta=f"{duration_diff:+.1f}",
                            delta_color="inverse"
                        )
                    with col2:
                        resource_diff = len(schedule["used_resources"]) - initial_analysis["resource_count"]
                        st.metric(
                            "Количество задействованных ресурсов",
                            len(schedule["used_resources"]),
                            delta=f"{resource_diff:+.0f}",
                            delta_color="inverse"
                        )
                    
                    st.json(schedule)
                    
                    # Создаем DataFrame для визуализации
                    df = pd.DataFrame(schedule["schedule"])
                    df["start"] = pd.to_datetime(df["start"])
                    df["finish"] = pd.to_datetime(df["finish"])
                    
                    # Создаем график Ганта
                    fig = px.timeline(
                        df, 
                        x_start="start", 
                        x_end="finish", 
                        y="role",
                        color="task_id",
                        title="График задач по ролям",
                        labels={
                            "task_id": "ID задачи",
                            "role": "Роль",
                            "start": "Начало",
                            "finish": "Окончание"
                        }
                    )
                    fig.update_yaxes(title="Роли")
                    fig.update_xaxes(title="Дата")
                    st.plotly_chart(fig)
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"Ошибка при обращении к API: {str(e)}")
                except Exception as e:
                    st.error(f"Ошибка при обработке результатов: {str(e)}")
    except json.JSONDecodeError:
        st.error("Ошибка при чтении JSON файла. Проверьте формат данных.")
    except Exception as e:
        st.error(f"Произошла ошибка: {str(e)}")

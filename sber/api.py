from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import openai
import json
import os

app = FastAPI()

# Получаем API ключ из переменной окружения
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

class OptimizationWeights(BaseModel):
    duration: float = 0.7
    resources: float = 0.3

class ScheduleEntry(BaseModel):
    task_id: int
    role: str
    resource_id: int
    start: str
    finish: str

class UsedResource(BaseModel):
    id: int
    role: str
    assigned_tasks: List[int]

class ScheduleOutput(BaseModel):
    schedule: List[ScheduleEntry]
    project_start: str
    project_finish: str
    used_resources: List[UsedResource]
    total_duration_days: int
    optimization_weights: dict

def generate_prompt(data: Dict[str, Any]) -> str:
    """Генерирует текст для запроса к ChatGPT."""
    # Извлекаем веса из данных или используем значения по умолчанию
    weights = data.get('constraints', {}).get('weights', {"duration": 0.7, "resources": 0.3})
    
    return f"""
    У нас есть проект с задачами. Проанализируй данные и составь оптимальный календарный план.
    
    Веса для оптимизации:
    - Вес минимизации длительности проекта: {weights['duration']}
    - Вес минимизации числа исполнителей: {weights['resources']}
    
    Данные проекта:
    {json.dumps(data, ensure_ascii=False, indent=2)}
    
    Верни только JSON в следующем формате (без дополнительных комментариев):
    {{
        "schedule": [
            {{ 
                "task_id": число, 
                "role": "строка", 
                "resource_id": число, 
                "start": "YYYY-MM-DD", 
                "finish": "YYYY-MM-DD" 
            }}
        ],
        "project_start": "YYYY-MM-DD",
        "project_finish": "YYYY-MM-DD",
        "used_resources": [
            {{
                "id": число,
                "role": "строка",
                "assigned_tasks": [список_id_задач]
            }}
        ],
        "total_duration_days": число,
        "optimization_weights": {weights}
    }}
    
    При оптимизации учитывай веса: старайся минимизировать длительность проекта с весом {weights['duration']} и количество исполнителей с весом {weights['resources']}.
    """

@app.post("/optimize", response_model=ScheduleOutput)
async def optimize_schedule(data: Dict[str, Any]):
    """Оптимизирует календарный план с использованием ChatGPT-4."""
    try:
        if not openai.api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key is not configured")
            
        prompt = generate_prompt(data)
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Исправлена опечатка в названии модели
            messages=[
                {"role": "system", "content": "Ты помощник по оптимизации расписаний. Возвращай только JSON без комментариев и объяснений."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(content)
        return ScheduleOutput(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка оптимизации: {str(e)}")

@app.get("/")
def root():
    return {"message": "API для оптимизации календарного плана проекта."}


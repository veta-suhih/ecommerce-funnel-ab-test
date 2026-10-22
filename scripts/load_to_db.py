"""
scripts/load_to_db.py
Загружает все данные событий и заказов Ozon в PostgreSQL чанками.
"""
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ozon_ab_test")

TRACKER_DIR = PROJECT_ROOT / "data" / "raw" / "ml_ozon_recsys_train_final_apparel_tracker_data"
ORDERS_DIR = PROJECT_ROOT / "data" / "raw" / "ml_ozon_recsys_train_final_apparel_orders_data"

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def load_table(folder_path, table_name, columns_to_keep):
    files = list(folder_path.glob("*.parquet"))
    print(f"Найдено файлов для {table_name}: {len(files)}")
    
    for i, file in enumerate(files):
        print(f"  [{i+1}/{len(files)}] Читаем {file.name}...")
        df = pd.read_parquet(file, columns=columns_to_keep)
        
        # Загружаем чанками по 100 000 строк, чтобы не забить оперативную память
        df.to_sql(
            table_name, 
            engine, 
            if_exists="replace" if i == 0 else "append", 
            index=False,
            chunksize=100_000
        )
    print(f"Таблица {table_name} успешно загружена.")

print("Начинаем загрузку данных в PostgreSQL...")
# Для событий берем только нужные для воронки колонки, чтобы сэкономить место
load_table(TRACKER_DIR, "events", ['user_id', 'item_id', 'timestamp', 'action_type'])
# Для заказов — только ID пользователя
load_table(ORDERS_DIR, "orders", ['user_id', 'created_timestamp'])

print("Все данные загружены!")
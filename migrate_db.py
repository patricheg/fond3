"""
Скрипт миграции базы данных для добавления поддержки нескольких изображений
"""
from app import app
from models import db
import json

def migrate_database():
    with app.app_context():
        print('Начинаем миграцию базы данных...')
        
        # Добавляем новые колонки если их нет
        try:
            # Проверяем наличие колонки images_json
            from sqlalchemy import text
            
            with db.engine.connect() as conn:
                # Добавляем колонку images_json для Fundraiser
                try:
                    conn.execute(text('ALTER TABLE fundraiser ADD COLUMN images_json TEXT'))
                    conn.commit()
                    print('+ Добавлена колонка images_json в таблицу fundraiser')
                except Exception as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print('- Колонка images_json уже существует в fundraiser')
                    else:
                        print(f'Ошибка при добавлении колонки в fundraiser: {e}')
                
                # Добавляем колонку images_json для News
                try:
                    conn.execute(text('ALTER TABLE news ADD COLUMN images_json TEXT'))
                    conn.commit()
                    print('+ Добавлена колонка images_json в таблицу news')
                except Exception as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print('- Колонка images_json уже существует в news')
                    else:
                        print(f'Ошибка при добавлении колонки в news: {e}')
                
                # Добавляем колонку images_json для Tournament
                try:
                    conn.execute(text('ALTER TABLE tournament ADD COLUMN images_json TEXT'))
                    conn.commit()
                    print('+ Добавлена колонка images_json в таблицу tournament')
                except Exception as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print('- Колонка images_json уже существует в tournament')
                    else:
                        print(f'Ошибка при добавлении колонки в tournament: {e}')
            
            print('\nМиграция базы данных завершена успешно!')
            print('\nТеперь вы можете загружать несколько изображений для каждого материала!')
            
        except Exception as e:
            print(f'\nОшибка при миграции: {e}')
            return False
        
        return True

if __name__ == '__main__':
    migrate_database()

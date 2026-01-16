"""
Скрипт миграции: добавление таблицы AboutPage
"""

from app import app
from models import db, AboutPage

def migrate():
    with app.app_context():
        print("Начинается миграция базы данных...")
        
        try:
            # Создаем таблицу AboutPage
            db.create_all()
            print("OK - Таблица AboutPage создана")
            
            # Проверяем, есть ли уже запись
            existing = AboutPage.query.first()
            if not existing:
                # Создаем начальную запись
                about = AboutPage(
                    title='О нас',
                    content='Добро пожаловать в наш благотворительный фонд помощи спортсменам!',
                    mission='Наша миссия - помогать спортсменам достигать своих целей.',
                    vision='Мы стремимся создать мир, где спорт доступен каждому.'
                )
                db.session.add(about)
                db.session.commit()
                print("OK - Создана начальная страница 'О нас'")
            else:
                print("OK - Страница 'О нас' уже существует")
            
            print("\nМиграция завершена успешно!")
            print("Теперь вы можете редактировать страницу 'О нас' через админ-панель")
            
        except Exception as e:
            print(f"Ошибка при миграции: {e}")
            return False
    
    return True

if __name__ == '__main__':
    migrate()

"""
Миграция: добавление колонки weight в таблицу tournament_registration
Запустите этот скрипт один раз: python migrate_add_weight.py
"""

from app import app
from models import db
import sys
import io

# Устанавливаем кодировку для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate():
    with app.app_context():
        print("=" * 60)
        print("Миграция базы данных: добавление колонки 'weight'")
        print("=" * 60)
        
        try:
            # Проверяем, существует ли колонка weight
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            # Проверяем наличие таблицы
            tables = inspector.get_table_names()
            if 'tournament_registration' not in tables:
                print("ОШИБКА: Таблица tournament_registration не найдена")
                print("Возможно, база данных не инициализирована")
                return False
            
            columns = [col['name'] for col in inspector.get_columns('tournament_registration')]
            
            if 'weight' in columns:
                print("\nИнформация: Колонка 'weight' уже существует в базе данных")
                print("Миграция не требуется")
                return True
            
            print("\nДобавление колонки 'weight'...")
            
            # Добавляем колонку weight
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE tournament_registration ADD COLUMN weight FLOAT'))
                conn.commit()
            
            print("OK - Колонка 'weight' успешно добавлена!")
            
            # Проверяем результат
            inspector = inspect(db.engine)
            columns_after = [col['name'] for col in inspector.get_columns('tournament_registration')]
            
            if 'weight' in columns_after:
                print("\n" + "=" * 60)
                print("Миграция завершена успешно!")
                print("=" * 60)
                print("\nКолонка 'weight' добавлена в таблицу tournament_registration")
                print("Теперь можно использовать поле 'Вес' в форме регистрации")
            else:
                print("\nПредупреждение: Не удалось подтвердить добавление колонки")
                return False
            
        except Exception as e:
            print(f"\nОШИБКА при миграции: {e}")
            print("\nВозможные причины:")
            print("1. База данных заблокирована (закройте приложение перед миграцией)")
            print("2. Недостаточно прав для изменения базы данных")
            print("3. Файл базы данных поврежден")
            return False
    
    return True

if __name__ == '__main__':
    print("\nВНИМАНИЕ: Перед запуском миграции остановите приложение!")
    print("Нажмите Enter для продолжения или Ctrl+C для отмены...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nМиграция отменена")
        sys.exit(0)
    
    success = migrate()
    
    if not success:
        print("\n" + "!" * 60)
        print("Миграция не завершена. Проверьте ошибки выше.")
        print("!" * 60)
        sys.exit(1)
    else:
        print("\nВсе готово! Можете запускать приложение.")
        sys.exit(0)

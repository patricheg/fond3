#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Миграция для добавления поля category в таблицу fundraiser
"""
import sys
from app import app, db
from models import Fundraiser

def migrate():
    """Добавляет поле category в таблицу fundraiser"""
    with app.app_context():
        try:
            # Проверяем, есть ли уже поле category
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('fundraiser')]
            
            if 'category' in columns:
                print('✓ Поле category уже существует в таблице fundraiser')
                return True
            
            print('Добавление поля category в таблицу fundraiser...')
            
            # Добавляем поле category
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE fundraiser ADD COLUMN category VARCHAR(100)'))
                conn.commit()
            
            print('✓ Поле category успешно добавлено')
            
            # Обновляем существующие записи с категорией по умолчанию
            fundraisers = Fundraiser.query.all()
            if fundraisers:
                print(f'Найдено {len(fundraisers)} сборов. Устанавливаем категорию по умолчанию...')
                for fundraiser in fundraisers:
                    if not fundraiser.category:
                        # Устанавливаем категорию "Второй шанс" по умолчанию
                        fundraiser.category = 'second_chance'
                db.session.commit()
                print('✓ Категории обновлены')
            
            print('\n=== Миграция успешно завершена! ===\n')
            return True
            
        except Exception as e:
            print(f'✗ Ошибка при миграции: {str(e)}')
            db.session.rollback()
            return False

if __name__ == '__main__':
    print('=== Миграция: Добавление категорий для сборов ===\n')
    success = migrate()
    sys.exit(0 if success else 1)

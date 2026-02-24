#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для создания favicon всех размеров из одного изображения
Требуется установить Pillow: pip install Pillow
"""

import sys
import os
from PIL import Image

def create_favicons(input_path, output_dir='static/images'):
    """
    Создает favicon различных размеров из исходного изображения
    
    Args:
        input_path: путь к исходному изображению
        output_dir: папка для сохранения (по умолчанию static/images)
    """
    
    print(f"🎨 Создание favicon из {input_path}...")
    
    # Проверка существования файла
    if not os.path.exists(input_path):
        print(f"❌ Файл {input_path} не найден!")
        return False
    
    # Создание папки, если не существует
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Открываем исходное изображение
        img = Image.open(input_path)
        
        # Конвертируем в RGBA если нужно
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"📐 Исходный размер: {img.size}")
        
        # Размеры для создания
        sizes = {
            'favicon-16x16.png': (16, 16),
            'favicon-32x32.png': (32, 32),
            'apple-touch-icon.png': (180, 180),
            'logo.png': (600, 200)  # Логотип для сайта
        }
        
        # Создаем изображения каждого размера
        for filename, size in sizes.items():
            output_path = os.path.join(output_dir, filename)
            
            # Создаем копию и изменяем размер
            resized = img.copy()
            resized.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Если размер не квадратный (как у logo.png), подгоняем
            if size[0] != size[1]:
                # Создаем новое изображение нужного размера с прозрачным фоном
                new_img = Image.new('RGBA', size, (0, 0, 0, 0))
                # Вставляем по центру
                offset = ((size[0] - resized.size[0]) // 2, 
                         (size[1] - resized.size[1]) // 2)
                new_img.paste(resized, offset)
                resized = new_img
            
            # Сохраняем
            resized.save(output_path, 'PNG', optimize=True)
            print(f"✅ Создан {filename} ({size[0]}x{size[1]})")
        
        # Создаем favicon.ico (содержит несколько размеров)
        ico_sizes = [(16, 16), (32, 32), (48, 48)]
        ico_images = []
        
        for size in ico_sizes:
            resized = img.copy()
            resized.thumbnail(size, Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        ico_path = os.path.join(output_dir, 'favicon.ico')
        ico_images[0].save(
            ico_path, 
            format='ICO', 
            sizes=[(img.size[0], img.size[1]) for img in ico_images]
        )
        print(f"✅ Создан favicon.ico (16x16, 32x32, 48x48)")
        
        print(f"\n🎉 Все файлы успешно созданы в папке {output_dir}/")
        print("\n📋 Созданные файлы:")
        for filename in os.listdir(output_dir):
            if filename.startswith(('favicon', 'logo', 'apple')):
                full_path = os.path.join(output_dir, filename)
                size_kb = os.path.getsize(full_path) / 1024
                print(f"   • {filename} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании favicon: {e}")
        return False


def main():
    """Главная функция"""
    
    print("=" * 60)
    print("🎨 Генератор Favicon для сайта")
    print("=" * 60)
    
    # Проверка аргументов
    if len(sys.argv) < 2:
        print("\n📖 Использование:")
        print("   python create_favicons.py <путь_к_изображению>")
        print("\n📝 Пример:")
        print("   python create_favicons.py logo_source.png")
        print("   python create_favicons.py C:\\Users\\Downloads\\logo.png")
        print("\n💡 Поддерживаемые форматы: PNG, JPG, JPEG, SVG (через Pillow)")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Создаем favicon
    success = create_favicons(input_path)
    
    if success:
        print("\n✅ Готово! Теперь запустите сайт и проверьте:")
        print("   1. python app.py")
        print("   2. Откройте http://127.0.0.1:5000")
        print("   3. Проверьте логотип в шапке и favicon во вкладке")
        print("\n💾 Не забудьте добавить файлы в Git:")
        print("   git add static/images/")
        print("   git commit -m 'Add logo and favicon'")
    else:
        print("\n❌ Не удалось создать favicon. Проверьте:")
        print("   1. Установлен ли Pillow: pip install Pillow")
        print("   2. Правильность пути к файлу")
        print("   3. Формат изображения (PNG, JPG)")


if __name__ == '__main__':
    main()

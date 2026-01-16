"""
Скрипт для проверки изображений в новостях
"""
from app import app
from models import News

with app.app_context():
    print("=" * 60)
    print("ПРОВЕРКА ИЗОБРАЖЕНИЙ В НОВОСТЯХ")
    print("=" * 60)
    
    all_news = News.query.all()
    
    if not all_news:
        print("\nНовостей в базе нет!")
    else:
        for news in all_news:
            print(f"\nНовость #{news.id}: {news.title[:50]}...")
            print(f"  image_url: {news.image_url or 'Нет'}")
            print(f"  images_json: {news.images_json or 'Нет'}")
            
            images = news.get_images()
            if images:
                print(f"  get_images(): {len(images)} изображений")
                for i, img in enumerate(images, 1):
                    print(f"    {i}. {img}")
            else:
                print(f"  get_images(): НЕТ ИЗОБРАЖЕНИЙ!")
            print()
    
    print("=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("1. Очистите кэш браузера (Ctrl + Shift + Delete)")
    print("2. Сделайте жесткую перезагрузку (Ctrl + F5)")
    print("3. Проверьте консоль браузера (F12) на ошибки")
    print("=" * 60)

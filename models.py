from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Модель пользователя для админ-панели"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Fundraiser(db.Model):
    """Модель благотворительного сбора"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    athlete_name = db.Column(db.String(150), nullable=False)
    goal_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(300))  # Оставляем для обратной совместимости
    images_json = db.Column(db.Text)  # JSON список всех изображений
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def progress_percentage(self):
        if self.goal_amount > 0:
            return min(100, (self.current_amount / self.goal_amount) * 100)
        return 0
    
    def get_images(self):
        """Получить список всех изображений"""
        if self.images_json:
            try:
                return json.loads(self.images_json)
            except:
                return []
        # Для обратной совместимости
        if self.image_url:
            return [self.image_url]
        return []
    
    def set_images(self, images_list):
        """Установить список изображений"""
        self.images_json = json.dumps(images_list) if images_list else None
        # Устанавливаем первое изображение как основное для обратной совместимости
        self.image_url = images_list[0] if images_list else None
    
    def get_main_image(self):
        """Получить главное изображение"""
        images = self.get_images()
        return images[0] if images else None


class News(db.Model):
    """Модель новости"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(300))
    image_url = db.Column(db.String(300))  # Оставляем для обратной совместимости
    images_json = db.Column(db.Text)  # JSON список всех изображений
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_images(self):
        """Получить список всех изображений"""
        if self.images_json:
            try:
                return json.loads(self.images_json)
            except:
                return []
        # Для обратной совместимости
        if self.image_url:
            return [self.image_url]
        return []
    
    def set_images(self, images_list):
        """Установить список изображений"""
        self.images_json = json.dumps(images_list) if images_list else None
        # Устанавливаем первое изображение как основное
        self.image_url = images_list[0] if images_list else None
    
    def get_main_image(self):
        """Получить главное изображение"""
        images = self.get_images()
        return images[0] if images else None


class Tournament(db.Model):
    """Модель турнира"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    participants_limit = db.Column(db.Integer)
    registration_url = db.Column(db.String(300))
    image_url = db.Column(db.String(300))  # Оставляем для обратной совместимости
    images_json = db.Column(db.Text)  # JSON список всех изображений
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_images(self):
        """Получить список всех изображений"""
        if self.images_json:
            try:
                return json.loads(self.images_json)
            except:
                return []
        # Для обратной совместимости
        if self.image_url:
            return [self.image_url]
        return []
    
    def set_images(self, images_list):
        """Установить список изображений"""
        self.images_json = json.dumps(images_list) if images_list else None
        # Устанавливаем первое изображение как основное
        self.image_url = images_list[0] if images_list else None
    
    def get_main_image(self):
        """Получить главное изображение"""
        images = self.get_images()
        return images[0] if images else None


class AboutPage(db.Model):
    """Модель страницы 'О нас' (singleton)"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='О нас')
    content = db.Column(db.Text, nullable=False, default='')
    mission = db.Column(db.Text)  # Наша миссия
    vision = db.Column(db.Text)  # Наше видение
    images_json = db.Column(db.Text)  # JSON список изображений (сертификаты, фото)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_images(self):
        """Получить список всех изображений"""
        if self.images_json:
            try:
                return json.loads(self.images_json)
            except:
                return []
        return []
    
    def set_images(self, images_list):
        """Установить список изображений"""
        self.images_json = json.dumps(images_list) if images_list else None


class ContactInfo(db.Model):
    """Модель контактной информации для связи (singleton)"""
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    telegram = db.Column(db.String(100))
    viber = db.Column(db.String(50))
    whatsapp = db.Column(db.String(50))
    vk = db.Column(db.String(100))
    instagram = db.Column(db.String(100))
    additional_info = db.Column(db.Text)  # Дополнительная информация
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OurPeople(db.Model):
    """Модель для людей и организаций, участвующих в благотворительности"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Имя или название организации
    role = db.Column(db.String(100))  # Роль: волонтер, партнер, благотворитель и т.д.
    description = db.Column(db.Text, nullable=False)  # Описание
    photo_url = db.Column(db.String(300))  # Фото
    contact_info = db.Column(db.String(200))  # Контактная информация (опционально)
    is_active = db.Column(db.Boolean, default=True)  # Отображается ли на сайте
    order_position = db.Column(db.Integer, default=0)  # Порядок отображения
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TournamentRegistration(db.Model):
    """Модель регистрации на турнир"""
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)  # ФИО участника
    phone = db.Column(db.String(50), nullable=False)  # Телефон
    email = db.Column(db.String(100))  # Email (опционально)
    age = db.Column(db.Integer)  # Возраст
    sport_category = db.Column(db.String(100))  # Спортивная категория/разряд
    disability_info = db.Column(db.Text)  # Информация об ограничениях (опционально)
    additional_info = db.Column(db.Text)  # Дополнительная информация
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связь с турниром
    tournament = db.relationship('Tournament', backref=db.backref('registrations', lazy=True))

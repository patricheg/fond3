from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Fundraiser, News, Tournament, AboutPage, ContactInfo, HomePage, OurPeople, TournamentRegistration
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Конфигурация для загрузки файлов
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Создаем папку для загрузок, если её нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'


def _ensure_sqlite_homepage_columns():
    """Лёгкая миграция для SQLite без Alembic (добавляет новые колонки при обновлениях)."""
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not uri.startswith('sqlite'):
        return

    candidates = [
        Path(app.instance_path) / "database.db",
        Path(__file__).resolve().parent / "instance" / "database.db",
        Path(__file__).resolve().parent / "database.db",
    ]
    db_path = next((p for p in candidates if p.exists()), None)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='home_page'")
        if not cur.fetchone():
            return

        cur.execute("PRAGMA table_info(home_page)")
        cols = {r[1] for r in cur.fetchall()}
        alters = []
        if "directions_image_url" not in cols:
            alters.append("ALTER TABLE home_page ADD COLUMN directions_image_url VARCHAR(300)")
        if "directions_image_url_mobile" not in cols:
            alters.append("ALTER TABLE home_page ADD COLUMN directions_image_url_mobile VARCHAR(300)")
        if "hero_image_url_mobile" not in cols:
            alters.append("ALTER TABLE home_page ADD COLUMN hero_image_url_mobile VARCHAR(300)")

        for sql in alters:
            cur.execute(sql)
        if alters:
            conn.commit()
    finally:
        conn.close()


_ensure_sqlite_homepage_columns()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_contact_info():
    """Внедрение контактной информации во все шаблоны"""
    contact_info = ContactInfo.query.first()
    return dict(contact_info=contact_info)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def allowed_file(filename):
    """Проверка допустимого расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    """Сохранение загруженного изображения"""
    if file and allowed_file(file.filename):
        # Генерируем уникальное имя файла
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Сохраняем файл
        file.save(filepath)
        
        # Возвращаем URL для использования в шаблонах
        return f"/static/uploads/{filename}"
    return None


def save_multiple_images(files):
    """Сохранение нескольких изображений"""
    saved_urls = []
    for file in files:
        if file and file.filename:
            url = save_image(file)
            if url:
                saved_urls.append(url)
    return saved_urls


def delete_image(image_url):
    """Удаление изображения с сервера"""
    if image_url and image_url.startswith('/static/uploads/'):
        filename = image_url.split('/')[-1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Ошибка при удалении файла: {e}")


@app.route('/admin/upload-image', methods=['POST'])
@login_required
def admin_upload_image():
    """
    Загрузка изображения из редактора (например, CKEditor/TinyMCE).
    Ожидает файл в поле 'upload' или 'file' и возвращает JSON с URL.
    """
    file = request.files.get('upload') or request.files.get('file')
    if not file or not file.filename:
        return jsonify({'error': 'Файл не найден'}), 400
    
    image_url = save_image(file)
    if not image_url:
        return jsonify({'error': 'Неверный формат файла'}), 400
    
    # CKEditor ожидает поле 'url', TinyMCE — 'location'
    return jsonify({'url': image_url, 'location': image_url})


# ==================== ПУБЛИЧНЫЕ МАРШРУТЫ ====================

@app.route('/')
def index():
    """Главная страница"""
    homepage = HomePage.query.first()
    if not homepage:
        homepage = HomePage()
        db.session.add(homepage)
        db.session.commit()

    latest_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).limit(3).all()
    active_fundraisers = Fundraiser.query.filter_by(is_active=True).order_by(Fundraiser.created_at.desc()).limit(3).all()
    upcoming_tournaments = Tournament.query.filter_by(is_active=True).filter(Tournament.date >= datetime.utcnow()).order_by(Tournament.date).limit(3).all()
    volunteers = OurPeople.query.filter_by(is_active=True).order_by(OurPeople.order_position, OurPeople.created_at.desc()).all()
    
    return render_template('landing_image_only.html', homepage=homepage)


@app.route('/fundraisers')
def fundraisers():
    """Страница всех сборов с фильтрацией по категориям"""
    category = request.args.get('category', '')
    
    query = Fundraiser.query.filter_by(is_active=True)
    
    # Фильтрация по категории
    if category:
        query = query.filter_by(category=category)
    
    all_fundraisers = query.order_by(Fundraiser.created_at.desc()).all()
    
    # Категории для фильтра
    categories = {
        'future_champion': 'Будущий чемпион — гранты для детей и юношей',
        'second_chance': 'Второй шанс — оплата операций и восстановления',
        'loyalty_to_sport': 'Верность спорту — поддержка ветеранов и тренеров',
        'strength_spirit_home': 'Дом силы и духа — поддержка спортзалов и клубов'
    }
    
    return render_template('fundraisers.html', 
                         fundraisers=all_fundraisers, 
                         categories=categories,
                         selected_category=category)


@app.route('/directions')
def directions():
    """Страница направлений деятельности"""
    homepage = HomePage.query.first()
    if not homepage:
        homepage = HomePage()
        db.session.add(homepage)
        db.session.commit()
    return render_template("directions.html", homepage=homepage)


@app.route('/directions/<slug>')
def direction_detail(slug):
    """Редирект: направления теперь одной картинкой"""
    return redirect(url_for('directions'))


@app.route('/fundraiser/<int:id>')
def fundraiser_detail(id):
    """Детальная страница сбора"""
    fundraiser = Fundraiser.query.get_or_404(id)
    contact_info = ContactInfo.query.first()
    return render_template('fundraiser_detail.html', fundraiser=fundraiser, contact_info=contact_info)


@app.route('/news')
def news():
    """Страница всех новостей"""
    all_news = News.query.filter_by(is_published=True).order_by(News.created_at.desc()).all()
    return render_template('news.html', news=all_news)


@app.route('/news/<int:id>')
def news_detail(id):
    """Детальная страница новости"""
    news_item = News.query.get_or_404(id)
    return render_template('news_detail.html', news=news_item)


@app.route('/tournaments')
def tournaments():
    """Страница турниров"""
    all_tournaments = Tournament.query.filter_by(is_active=True).order_by(Tournament.date).all()
    return render_template('tournaments.html', tournaments=all_tournaments)


@app.route('/tournament/<int:id>')
def tournament_detail(id):
    """Детальная страница турнира"""
    tournament = Tournament.query.get_or_404(id)
    
    # Подсчет количества подтвержденных регистраций
    confirmed_count = TournamentRegistration.query.filter_by(
        tournament_id=id,
        status='confirmed'
    ).count()
    
    # Проверяем, есть ли свободные места
    places_available = True
    if tournament.participants_limit:
        places_available = confirmed_count < tournament.participants_limit
    
    return render_template('tournament_detail.html', 
                         tournament=tournament, 
                         confirmed_count=confirmed_count,
                         places_available=places_available)


@app.route('/tournament/<int:id>/register', methods=['POST'])
def register_tournament(id):
    """Регистрация на турнир"""
    tournament = Tournament.query.get_or_404(id)
    
    if not tournament.is_active:
        flash('Регистрация на этот турнир закрыта', 'error')
        return redirect(url_for('tournaments'))
    
    # Проверяем лимит участников
    if tournament.participants_limit:
        current_registrations = TournamentRegistration.query.filter_by(
            tournament_id=id,
            status='confirmed'
        ).count()
        if current_registrations >= tournament.participants_limit:
            flash('К сожалению, все места на турнир заняты', 'error')
            return redirect(url_for('tournaments'))
    
    # Создаем новую регистрацию
    registration = TournamentRegistration(
        tournament_id=id,
        full_name=request.form.get('full_name'),
        phone=request.form.get('phone'),
        email=request.form.get('email'),
        age=request.form.get('age'),
        weight=request.form.get('weight'),
        sport_category=request.form.get('sport_category'),
        disability_info=request.form.get('disability_info'),
        additional_info=request.form.get('additional_info'),
        status='pending'  # Устанавливаем статус "В ожидании"
    )
    
    try:
        db.session.add(registration)
        db.session.commit()
        flash('Ваша заявка отправлена! Ожидайте подтверждения, мы свяжемся с вами в ближайшее время.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при регистрации. Попробуйте еще раз.', 'error')
    
    return redirect(url_for('tournament_detail', id=id))


@app.route('/about')
def about():
    """Страница О нас"""
    about_page = AboutPage.query.first()
    if not about_page:
        # Создаем страницу с дефолтным контентом, если её еще нет
        about_page = AboutPage(
            title='О нас',
            content='Добро пожаловать в наш благотворительный фонд!',
            mission='Наша миссия - помогать спортсменам достигать своих целей.',
            vision='Мы стремимся создать мир, где спорт доступен каждому.'
        )
        db.session.add(about_page)
        db.session.commit()
    return render_template('about.html', about=about_page)


@app.route('/fund')
def fund_about():
    """Раздел «О фонде» (фиксированный контент)"""
    return render_template('fund_about.html')


@app.route('/future-champion')
def future_champion():
    """Страница «Будущий чемпион»"""
    page = {
        "title": "Будущий чемпион",
        "text": (
            "Поддержка молодых и начинающих спортсменов.\n"
            "Мы помогаем талантливым детям и подросткам\n"
            "сделать первые шаги в спорте.\n"
            "Обеспечиваем экипировкой,\n"
            "оплачиваем участие в соревнованиях и сборах.\n"
            "Наша цель — дать каждому ребенку шанс\n"
            "раскрыть свой потенциал."
        ),
        "image": "images/future_champion.webp",
    }
    return render_template('program_page.html', page=page)


@app.route('/loyalty-to-sport')
def loyalty_to_sport_page():
    """Страница «Верность спорту»"""
    page = {
        "title": "Верность спорту",
        "text": (
            "Поддержка действующих спортсменов.\n"
            "Мы оказываем помощь спортсменам, которые\n"
            "уже показывают результаты, но нуждаются\n"
            "в дополнительной поддержке.\n"
            "Финансируем участие в соревнованиях,\n"
            "восстановление, подготовку и развитие."
        ),
        "image": "images/vern.webp",
    }
    return render_template('program_page.html', page=page)


@app.route('/veterans-and-coaches')
def veterans_and_coaches_page():
    """Страница «Ветераны спорта и тренеры»"""
    page = {
        "title": "Ветераны спорта и тренеры",
        "text": (
            "Поддержка людей, посвятивших жизнь спорту.\n"
            "Мы помогаем тренерам и ветеранам,\n"
            "которые внесли значительный вклад\n"
            "в развитие спорта.\n"
            "Оказываем материальную помощь,\n"
            "поддержку и внимание."
        ),
        "image": "images/veterans.webp",
    }
    return render_template('program_page.html', page=page)


@app.route('/sport-infrastructure')
def sport_infrastructure_page():
    """Страница «Спортивная инфраструктура»"""
    page = {
        "title": "Спортивная инфраструктура",
        "text": (
            "Развитие спортивной среды.\n"
            "Мы участвуем в улучшении условий\n"
            "для тренировок: закупаем инвентарь,\n"
            "помогаем залам и секциям.\n"
            "Создаем комфортные условия\n"
            "для занятий спортом."
        ),
        "image": "images/infra.webp",
    }
    return render_template('program_page.html', page=page)


@app.route('/reports')
def reports():
    """Раздел «Отчетность»"""
    sections = [
        {"title": "Устав", "files": ["ustav.pdf", "ustav.docx", "ustav.jpg", "ustav.png"]},
        {"title": "Свидетельство о регистрации", "files": ["registration.pdf", "registration.docx", "registration.jpg", "registration.png"]},
        {"title": "Реквизиты", "files": ["requisites.pdf", "requisites.docx", "requisites.jpg", "requisites.png"]},
        {"title": "Годовые отчеты", "files": ["annual_report_2024.pdf", "annual_report_2025.pdf"]},
    ]
    return render_template("reports.html", sections=sections)


@app.route('/reports/download/<path:filename>')
def reports_download(filename):
    """Скачивание файлов отчетности"""
    if not filename or ".." in filename or filename.startswith(("/", "\\")):
        abort(404)
    return send_from_directory("static/reports", filename, as_attachment=True)


@app.route('/legal/<doc_type>')
def legal_page(doc_type):
    """Текстовые юридические страницы."""
    pages = {
        "offer": {
            "title": "Публичная оферта",
            "sections": [
                {
                    "heading": "1. Общие положения",
                    "text": "1.1. Настоящее предложение является публичной офертой в соответствии с п. 2 ст. 407 Гражданского кодекса Республики Беларусь.\n1.2. Благополучатель: Местный благотворительный фонд помощи спортсменам, зарегистрированный Минским городским исполнительным комитетом (Главное управление Юстиции) за № 194907539, в лице Директора Поречина Игоря Ивановича, действующего на основании Устава.\n1.3. Благотворитель (Жертвователь): Любое физическое лицо, принявшее условия настоящей оферты путем перечисления денежных средств."
                },
                {
                    "heading": "2. Предмет пожертвования",
                    "text": "2.1. Благотворитель добровольно и безвозмездно передает Благополучателю денежные средства (далее — Пожертвование) в безналичном порядке.\n2.2. Пожертвование направляется на осуществление уставной деятельности Фонда: поддержку спортсменов, укрепление материально-технической базы, организацию спортивных мероприятий и иные цели, предусмотренные Уставом.\n2.3. Пожертвование по настоящему договору не является спонсорской помощью в понимании Указа № 300 (если жертвователь — физлицо)."
                },
                {
                    "heading": "3. Порядок заключения договора",
                    "text": "3.1. Договор считается заключенным (акцептованным) с момента зачисления денежных средств на благотворительный счет Фонда.\n3.2. Факт перечисления средств подтверждает, что Благотворитель ознакомлен и согласен со всеми условиями оферты."
                },
                {
                    "heading": "4. Права и обязанности сторон",
                    "text": "4.1. Благополучатель обязан использовать полученные средства исключительно на цели, указанные в Уставе.\n4.2. Фонд ведет учет всех поступлений и расходов и представляет отчетность в соответствии с законодательством РБ.\n4.3. Благотворитель имеет право ознакомиться с отчетом об использовании средств на официальном сайте Фонда."
                },
                {
                    "heading": "5. Персональные данные",
                    "text": "5.1. В соответствии с Законом РБ № 99-З «О защите персональных данных», совершая пожертвование, Благотворитель дает согласие на обработку своих данных (ФИО, сумма, e-mail) для целей исполнения договора и ведения учета."
                },
                {
                    "heading": "6. Реквизиты фонда",
                    "text": "УНП: 194907539\nБлаготворительный счет (IBAN): BY73UNBS30150217000000008933\nЗакрытое акционерное общество «Белорусско-Швейцарский Банк» «БСБ Банк», BIC: UNBSBY2X\nАдрес: г.Минск, ул.Лещинского, д.8 к.4 комн.312\nТелефон: +375 44 746 74 67"
                },
            ],
        },
        "policy": {
            "title": "Политика защиты данных",
            "sections": [
                {
                    "heading": "ПОЛИТИКА В ОТНОШЕНИИ ОБРАБОТКИ ПЕРСОНАЛЬНЫХ ДАННЫХ",
                    "text": "Местного благотворительного фонда фонд помощи спортсменам"
                },
                {
                    "heading": "1. Общие положения",
                    "text": "1.1. Настоящая Политика определяет порядок обработки и защиты персональных данных пользователей сайта https://sportfondminsk.by/ (далее — Сайт), которую осуществляет Местный благотворительный фонд помощи спортсменам (далее — Фонд).\n1.2. Политика разработана в соответствии с Законом Республики Беларусь от 7 мая 2021 г. № 99-З «О защите персональных данных».\n1.3. Цель Политики — обеспечение защиты прав и свобод человека при обработке его персональных данных, в том числе защиты прав на неприкосновенность частной жизни."
                },
                {
                    "heading": "2. Категории субъектов и перечень данных",
                    "text": "Фонд может обрабатывать данные следующих лиц:\n• Жертвователи (физлица): Фамилия, имя, отчество, адрес электронной почты, сумма пожертвования, номер телефона (если указан).\n• Пользователи сайта: Данные о файлах cookie, IP-адрес, тип устройства (собираются автоматически для аналитики)."
                },
                {
                    "heading": "3. Цели обработки данных",
                    "text": "3.1. Исполнение договора публичной оферты о пожертвовании.\n3.2. Направление уведомлений о получении средств и отчетов о деятельности Фонда (с согласия пользователя).\n3.3. Предоставление ответов на запросы пользователей через формы обратной связи.\n3.4. Анализ работы Сайта и его улучшение."
                },
                {
                    "heading": "4. Права пользователя (субъекта данных)",
                    "text": "Вы имеете право:\n• Отозвать согласие на обработку данных в любой момент.\n• Получить информацию об обработке ваших данных и требовать их изменения, если они неверны.\n• Требовать прекращения обработки или удаления данных (право «на забвение»), если нет законных оснований для их хранения.\n• Обжаловать действия Фонда в уполномоченный орган (Национальный центр защиты персональных данных РБ)."
                },
                {
                    "heading": "5. Порядок обработки и передачи",
                    "text": "5.1. Обработка данных осуществляется как автоматизированным, так и неавтоматизированным способом.\n5.2. Фонд не передает ваши данные третьим лицам, за исключением случаев, установленных законодательством РБ (например, по запросу госорганов или для осуществления банковских платежей)."
                },
                {
                    "heading": "6. Хранение данных",
                    "text": "6.1. Срок хранения данных Жертвователей составляет [указать срок, обычно 3 года или 5 лет согласно правилам архивации для НКО] после исполнения договора.\n6.2. При достижении целей обработки или отзыве согласия данные подлежат удалению, если иное не предусмотрено законом."
                },
                {
                    "heading": "7. Контакты",
                    "text": "По вопросам обработки данных вы можете направить запрос на почту info@sportfondminsk.by или по адресу: г.Минск ул.Лещинского д.8 к.4 комн.312."
                },
            ],
        },
    }
    page = pages.get(doc_type)
    if not page:
        abort(404)
    return render_template("legal_page.html", page=page)


@app.route('/our-people')
def our_people():
    """Страница Волонтеры"""
    people = OurPeople.query.filter_by(is_active=True).order_by(OurPeople.order_position, OurPeople.created_at.desc()).all()
    return render_template('our_people.html', people=people)


@app.route('/donate')
def donate():
    """Страница с QR-кодом для пожертвований"""
    return render_template('donate_qr.html')


# ==================== АДМИН-ПАНЕЛЬ ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа в админ-панель"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """Выход из админ-панели"""
    logout_user()
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_dashboard():
    """Главная страница админ-панели"""
    fundraisers_count = Fundraiser.query.count()
    news_count = News.query.count()
    tournaments_count = Tournament.query.count()
    
    return render_template('admin/dashboard.html',
                         fundraisers_count=fundraisers_count,
                         news_count=news_count,
                         tournaments_count=tournaments_count)


# ==================== УПРАВЛЕНИЕ СБОРАМИ ====================

@app.route('/admin/fundraisers')
@login_required
def admin_fundraisers():
    """Список всех сборов в админке"""
    all_fundraisers = Fundraiser.query.order_by(Fundraiser.created_at.desc()).all()
    return render_template('admin/fundraisers.html', fundraisers=all_fundraisers)


@app.route('/admin/fundraiser/add', methods=['GET', 'POST'])
@login_required
def admin_add_fundraiser():
    """Добавление нового сбора"""
    if request.method == 'POST':
        # Обработка загрузки нескольких изображений
        images_list = []
        
        # Загружаем файлы
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            images_list.extend(saved_urls)
        
        # Если нет загруженных файлов, проверяем URL
        if not images_list and request.form.get('image_url'):
            images_list.append(request.form.get('image_url'))
        
        fundraiser = Fundraiser(
            title=request.form['title'],
            description=request.form['description'],
            athlete_name=request.form['athlete_name'],
            goal_amount=float(request.form['goal_amount']),
            current_amount=float(request.form.get('current_amount', 0)),
            category=request.form.get('category'),
            is_active=request.form.get('is_active') == 'on'
        )
        fundraiser.set_images(images_list)
        
        db.session.add(fundraiser)
        db.session.commit()
        flash('Сбор успешно добавлен!', 'success')
        return redirect(url_for('admin_fundraisers'))
    
    return render_template('admin/fundraiser_form.html', fundraiser=None)


@app.route('/admin/fundraiser/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_fundraiser(id):
    """Редактирование сбора"""
    fundraiser = Fundraiser.query.get_or_404(id)
    
    if request.method == 'POST':
        # Получаем текущие изображения
        current_images = fundraiser.get_images()
        
        # Обработка удаления изображений
        images_to_keep = request.form.getlist('keep_images')
        new_images_list = [img for img in current_images if img in images_to_keep]
        
        # Удаляем изображения, которые больше не нужны
        for img in current_images:
            if img not in images_to_keep and img.startswith('/static/uploads/'):
                delete_image(img)
        
        # Загружаем новые файлы
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            new_images_list.extend(saved_urls)
        
        # Если нет изображений и указан URL
        if not new_images_list and request.form.get('image_url'):
            new_images_list.append(request.form.get('image_url'))
        
        fundraiser.title = request.form['title']
        fundraiser.description = request.form['description']
        fundraiser.athlete_name = request.form['athlete_name']
        fundraiser.goal_amount = float(request.form['goal_amount'])
        fundraiser.current_amount = float(request.form.get('current_amount', 0))
        fundraiser.category = request.form.get('category')
        fundraiser.is_active = request.form.get('is_active') == 'on'
        fundraiser.set_images(new_images_list)
        
        db.session.commit()
        flash('Сбор успешно обновлен!', 'success')
        return redirect(url_for('admin_fundraisers'))
    
    return render_template('admin/fundraiser_form.html', fundraiser=fundraiser)


@app.route('/admin/fundraiser/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_fundraiser(id):
    """Удаление сбора"""
    fundraiser = Fundraiser.query.get_or_404(id)
    
    # Удаляем все изображения
    for image_url in fundraiser.get_images():
        if image_url.startswith('/static/uploads/'):
            delete_image(image_url)
    
    db.session.delete(fundraiser)
    db.session.commit()
    flash('Сбор успешно удален!', 'success')
    return redirect(url_for('admin_fundraisers'))


# ==================== УПРАВЛЕНИЕ НОВОСТЯМИ ====================

@app.route('/admin/news')
@login_required
def admin_news():
    """Список всех новостей в админке"""
    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template('admin/news.html', news=all_news)


@app.route('/admin/news/add', methods=['GET', 'POST'])
@login_required
def admin_add_news():
    """Добавление новой новости"""
    if request.method == 'POST':
        # Обработка загрузки нескольких изображений
        images_list = []
        
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            images_list.extend(saved_urls)
        
        if not images_list and request.form.get('image_url'):
            images_list.append(request.form.get('image_url'))
        
        news_item = News(
            title=request.form['title'],
            content=request.form['content'],
            summary=request.form.get('summary', ''),
            is_published=request.form.get('is_published') == 'on'
        )
        news_item.set_images(images_list)
        
        db.session.add(news_item)
        db.session.commit()
        flash('Новость успешно добавлена!', 'success')
        return redirect(url_for('admin_news'))
    
    return render_template('admin/news_form.html', news=None)


@app.route('/admin/news/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(id):
    """Редактирование новости"""
    news_item = News.query.get_or_404(id)
    
    if request.method == 'POST':
        current_images = news_item.get_images()
        images_to_keep = request.form.getlist('keep_images')
        new_images_list = [img for img in current_images if img in images_to_keep]
        
        for img in current_images:
            if img not in images_to_keep and img.startswith('/static/uploads/'):
                delete_image(img)
        
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            new_images_list.extend(saved_urls)
        
        if not new_images_list and request.form.get('image_url'):
            new_images_list.append(request.form.get('image_url'))
        
        news_item.title = request.form['title']
        news_item.content = request.form['content']
        news_item.summary = request.form.get('summary', '')
        news_item.is_published = request.form.get('is_published') == 'on'
        news_item.set_images(new_images_list)
        
        db.session.commit()
        flash('Новость успешно обновлена!', 'success')
        return redirect(url_for('admin_news'))
    
    return render_template('admin/news_form.html', news=news_item)


@app.route('/admin/news/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_news(id):
    """Удаление новости"""
    news_item = News.query.get_or_404(id)
    
    # Удаляем все изображения
    for image_url in news_item.get_images():
        if image_url.startswith('/static/uploads/'):
            delete_image(image_url)
    
    db.session.delete(news_item)
    db.session.commit()
    flash('Новость успешно удалена!', 'success')
    return redirect(url_for('admin_news'))


# ==================== УПРАВЛЕНИЕ ТУРНИРАМИ ====================

@app.route('/admin/tournaments')
@login_required
def admin_tournaments():
    """Список всех турниров в админке"""
    all_tournaments = Tournament.query.order_by(Tournament.date.desc()).all()
    return render_template('admin/tournaments.html', tournaments=all_tournaments)


@app.route('/admin/tournament/add', methods=['GET', 'POST'])
@login_required
def admin_add_tournament():
    """Добавление нового турнира"""
    if request.method == 'POST':
        images_list = []
        
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            images_list.extend(saved_urls)
        
        if not images_list and request.form.get('image_url'):
            images_list.append(request.form.get('image_url'))
        
        tournament = Tournament(
            title=request.form['title'],
            description=request.form['description'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M'),
            location=request.form.get('location', ''),
            participants_limit=int(request.form.get('participants_limit', 0)) if request.form.get('participants_limit') else None,
            registration_url=request.form.get('registration_url', ''),
            is_active=request.form.get('is_active') == 'on'
        )
        tournament.set_images(images_list)
        
        db.session.add(tournament)
        db.session.commit()
        flash('Турнир успешно добавлен!', 'success')
        return redirect(url_for('admin_tournaments'))
    
    return render_template('admin/tournament_form.html', tournament=None)


@app.route('/admin/tournament/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_tournament(id):
    """Редактирование турнира"""
    tournament = Tournament.query.get_or_404(id)
    
    if request.method == 'POST':
        current_images = tournament.get_images()
        images_to_keep = request.form.getlist('keep_images')
        new_images_list = [img for img in current_images if img in images_to_keep]
        
        for img in current_images:
            if img not in images_to_keep and img.startswith('/static/uploads/'):
                delete_image(img)
        
        if 'image_files' in request.files:
            files = request.files.getlist('image_files')
            saved_urls = save_multiple_images(files)
            new_images_list.extend(saved_urls)
        
        if not new_images_list and request.form.get('image_url'):
            new_images_list.append(request.form.get('image_url'))
        
        tournament.title = request.form['title']
        tournament.description = request.form['description']
        tournament.date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
        tournament.location = request.form.get('location', '')
        tournament.participants_limit = int(request.form.get('participants_limit', 0)) if request.form.get('participants_limit') else None
        tournament.registration_url = request.form.get('registration_url', '')
        tournament.is_active = request.form.get('is_active') == 'on'
        tournament.set_images(new_images_list)
        
        db.session.commit()
        flash('Турнир успешно обновлен!', 'success')
        return redirect(url_for('admin_tournaments'))
    
    return render_template('admin/tournament_form.html', tournament=tournament)


@app.route('/admin/tournament/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_tournament(id):
    """Удаление турнира"""
    tournament = Tournament.query.get_or_404(id)
    
    # Удаляем все изображения
    for image_url in tournament.get_images():
        if image_url.startswith('/static/uploads/'):
            delete_image(image_url)
    
    db.session.delete(tournament)
    db.session.commit()
    flash('Турнир успешно удален!', 'success')
    return redirect(url_for('admin_tournaments'))


@app.route('/admin/tournament/<int:id>/registrations')
@login_required
def admin_tournament_registrations(id):
    """Просмотр регистраций на турнир"""
    tournament = Tournament.query.get_or_404(id)
    registrations = TournamentRegistration.query.filter_by(tournament_id=id).order_by(TournamentRegistration.created_at.desc()).all()
    return render_template('admin/tournament_registrations.html', tournament=tournament, registrations=registrations)


@app.route('/admin/registration/<int:id>/status', methods=['POST'])
@login_required
def admin_update_registration_status(id):
    """Изменение статуса регистрации"""
    registration = TournamentRegistration.query.get_or_404(id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'confirmed', 'cancelled']:
        registration.status = new_status
        db.session.commit()
        flash('Статус регистрации обновлен!', 'success')
    else:
        flash('Некорректный статус', 'error')
    
    return redirect(url_for('admin_tournament_registrations', id=registration.tournament_id))


@app.route('/admin/registration/<int:id>/delete', methods=['POST'])
@login_required
def admin_delete_registration(id):
    """Удаление регистрации"""
    registration = TournamentRegistration.query.get_or_404(id)
    tournament_id = registration.tournament_id
    
    db.session.delete(registration)
    db.session.commit()
    flash('Регистрация удалена!', 'success')
    return redirect(url_for('admin_tournament_registrations', id=tournament_id))


# ==================== АДМИН: СТРАНИЦА О НАС ====================

@app.route('/admin/about')
@login_required
def admin_about():
    """Редактирование страницы О нас"""
    about_page = AboutPage.query.first()
    if not about_page:
        about_page = AboutPage(
            title='О нас',
            content='',
            
            mission='',
            vision=''
        )
        db.session.add(about_page)
        db.session.commit()
    return render_template('admin/about_form.html', about=about_page)


@app.route('/admin/about/edit', methods=['POST'])
@login_required
def admin_edit_about():
    """Сохранение изменений страницы О нас"""
    about_page = AboutPage.query.first()
    if not about_page:
        about_page = AboutPage()
        db.session.add(about_page)
    
    about_page.title = request.form.get('title', 'О нас')
    about_page.content = request.form.get('content', '')
    about_page.mission = request.form.get('mission', '')
    about_page.vision = request.form.get('vision', '')
    
    # Обработка загруженных изображений
    # Сохраняем существующие изображения, которые не были удалены через AJAX
    existing_images = about_page.get_images()
    
    # Загружаем новые файлы
    if 'images' in request.files:
        files = request.files.getlist('images')
        saved_urls = save_multiple_images(files)
        existing_images.extend(saved_urls)
    
    # Обновляем список изображений
    if existing_images:
        about_page.set_images(existing_images)
    
    db.session.commit()
    flash('Страница "О нас" успешно обновлена!', 'success')
    return redirect(url_for('admin_about'))


@app.route('/admin/about/delete-image', methods=['POST'])
@login_required
def admin_about_delete_image():
    """Удаление изображения со страницы О нас"""
    data = request.get_json()
    image_url = data.get('image_url')
    
    about_page = AboutPage.query.first()
    if about_page and image_url:
        images = about_page.get_images()
        if image_url in images:
            images.remove(image_url)
            about_page.set_images(images)
            db.session.commit()
            
            # Удаляем файл с диска
            if image_url.startswith('/static/uploads/'):
                delete_image(image_url)
            
            return jsonify({'success': True})
    
    return jsonify({'success': False}), 400


# ==================== АДМИН: КОНТАКТЫ ====================

@app.route('/admin/contacts')
@login_required
def admin_contacts():
    """Редактирование контактной информации"""
    contact_info = ContactInfo.query.first()
    if not contact_info:
        contact_info = ContactInfo()
        db.session.add(contact_info)
        db.session.commit()
    return render_template('admin/contacts_form.html', contacts=contact_info)


@app.route('/admin/contacts/edit', methods=['POST'])
@login_required
def admin_edit_contacts():
    """Сохранение контактной информации"""
    contact_info = ContactInfo.query.first()
    if not contact_info:
        contact_info = ContactInfo()
        db.session.add(contact_info)
    
    contact_info.phone = request.form.get('phone', '')
    contact_info.email = request.form.get('email', '')
    contact_info.telegram = request.form.get('telegram', '')
    contact_info.viber = request.form.get('viber', '')
    contact_info.whatsapp = request.form.get('whatsapp', '')
    contact_info.vk = request.form.get('vk', '')
    contact_info.instagram = request.form.get('instagram', '')
    contact_info.additional_info = request.form.get('additional_info', '')
    
    db.session.commit()
    flash('Контактная информация успешно обновлена!', 'success')
    return redirect(url_for('admin_contacts'))


# ==================== АДМИН: ГЛАВНАЯ СТРАНИЦА ====================

@app.route('/admin/homepage')
@login_required
def admin_homepage():
    """Редактирование главной страницы"""
    homepage = HomePage.query.first()
    if not homepage:
        homepage = HomePage()
        db.session.add(homepage)
        db.session.commit()
    return render_template('admin/homepage_form.html', homepage=homepage)


@app.route('/admin/homepage/edit', methods=['POST'])
@login_required
def admin_edit_homepage():
    """Сохранение изменений главной страницы"""
    homepage = HomePage.query.first()
    if not homepage:
        homepage = HomePage()
        db.session.add(homepage)

    homepage.tagline = request.form.get('tagline', homepage.tagline or '')
    homepage.title = request.form.get('title', homepage.title or '')
    homepage.left_item_1 = request.form.get('left_item_1', homepage.left_item_1 or '')
    homepage.left_item_2 = request.form.get('left_item_2', homepage.left_item_2 or '')
    homepage.left_item_3 = request.form.get('left_item_3', homepage.left_item_3 or '')
    homepage.left_item_4 = request.form.get('left_item_4', homepage.left_item_4 or '')

    if request.form.get('hero_image_url'):
        homepage.hero_image_url = request.form.get('hero_image_url')

    if 'hero_image_file' in request.files:
        file = request.files.get('hero_image_file')
        if file and file.filename:
            hero_url = save_image(file)
            if hero_url:
                homepage.hero_image_url = hero_url

    # Мобильный баннер
    if request.form.get('hero_image_url_mobile'):
        homepage.hero_image_url_mobile = request.form.get('hero_image_url_mobile')

    if 'hero_image_file_mobile' in request.files:
        file = request.files.get('hero_image_file_mobile')
        if file and file.filename:
            img_url = save_image(file)
            if img_url:
                homepage.hero_image_url_mobile = img_url

    # Картинка для страницы «Направления деятельности»
    if request.form.get('directions_image_url'):
        homepage.directions_image_url = request.form.get('directions_image_url')

    if 'directions_image_file' in request.files:
        file = request.files.get('directions_image_file')
        if file and file.filename:
            img_url = save_image(file)
            if img_url:
                homepage.directions_image_url = img_url

    # Мобильная версия картинки направлений
    if request.form.get('directions_image_url_mobile'):
        homepage.directions_image_url_mobile = request.form.get('directions_image_url_mobile')

    if 'directions_image_file_mobile' in request.files:
        file = request.files.get('directions_image_file_mobile')
        if file and file.filename:
            img_url = save_image(file)
            if img_url:
                homepage.directions_image_url_mobile = img_url

    db.session.commit()
    flash('Главная страница обновлена!', 'success')
    return redirect(url_for('admin_homepage'))


# ==================== АДМИН: НАШИ ЛЮДИ ====================

@app.route('/admin/our-people')
@login_required
def admin_our_people():
    """Список волонтеров"""
    people = OurPeople.query.order_by(OurPeople.order_position, OurPeople.created_at.desc()).all()
    return render_template('admin/our_people.html', people=people)


@app.route('/admin/our-people/add', methods=['GET', 'POST'])
@login_required
def admin_add_person():
    """Добавление человека/организации"""
    if request.method == 'POST':
        person = OurPeople(
            name=request.form.get('name'),
            role=request.form.get('role', ''),
            description=request.form.get('description'),
            contact_info=request.form.get('contact_info', ''),
            is_active=bool(request.form.get('is_active')),
            order_position=int(request.form.get('order_position', 0))
        )
        
        # Обработка фото
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                photo_url = save_image(file)
                if photo_url:
                    person.photo_url = photo_url
        
        # Если не загружено фото, проверяем URL
        if not person.photo_url and request.form.get('photo_url'):
            person.photo_url = request.form.get('photo_url')
        
        db.session.add(person)
        db.session.commit()
        flash('Человек/организация успешно добавлены!', 'success')
        return redirect(url_for('admin_our_people'))
    
    return render_template('admin/our_people_form.html', person=None)


@app.route('/admin/our-people/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_person(id):
    """Редактирование человека/организации"""
    person = OurPeople.query.get_or_404(id)
    
    if request.method == 'POST':
        person.name = request.form.get('name')
        person.role = request.form.get('role', '')
        person.description = request.form.get('description')
        person.contact_info = request.form.get('contact_info', '')
        person.is_active = bool(request.form.get('is_active'))
        person.order_position = int(request.form.get('order_position', 0))
        
        # Обработка нового фото
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                # Удаляем старое фото
                if person.photo_url and person.photo_url.startswith('/static/uploads/'):
                    delete_image(person.photo_url)
                
                # Сохраняем новое
                photo_url = save_image(file)
                if photo_url:
                    person.photo_url = photo_url
        
        # Если не загружено фото, проверяем URL
        if not person.photo_url and request.form.get('photo_url'):
            person.photo_url = request.form.get('photo_url')
        
        db.session.commit()
        flash('Информация успешно обновлена!', 'success')
        return redirect(url_for('admin_our_people'))
    
    return render_template('admin/our_people_form.html', person=person)


@app.route('/admin/our-people/delete/<int:id>', methods=['POST'])
@login_required
def admin_delete_person(id):
    """Удаление человека/организации"""
    person = OurPeople.query.get_or_404(id)
    
    # Удаляем фото
    if person.photo_url and person.photo_url.startswith('/static/uploads/'):
        delete_image(person.photo_url)
    
    db.session.delete(person)
    db.session.commit()
    flash('Запись успешно удалена!', 'success')
    return redirect(url_for('admin_our_people'))


# ==================== SEO МАРШРУТЫ ====================

@app.route('/robots.txt')
def robots_txt():
    """Возвращает robots.txt для поисковых систем"""
    response = make_response(render_template('robots.txt'))
    response.headers['Content-Type'] = 'text/plain'
    return response


@app.route('/sitemap.xml')
def sitemap_xml():
    """Генерирует динамический sitemap.xml"""
    pages = []
    
    # Главная страница
    pages.append({
        'loc': url_for('index', _external=True),
        'changefreq': 'daily',
        'priority': '1.0',
        'lastmod': datetime.utcnow().strftime('%Y-%m-%d')
    })
    
    # Статические страницы
    static_pages = [
        ('fundraisers', 'weekly', '0.9'),
        ('tournaments', 'weekly', '0.9'),
        ('news', 'daily', '0.8'),
        ('our_people', 'monthly', '0.7'),
        ('about', 'monthly', '0.6')
    ]
    
    for route, changefreq, priority in static_pages:
        pages.append({
            'loc': url_for(route, _external=True),
            'changefreq': changefreq,
            'priority': priority,
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d')
        })
    
    # Сборы средств
    fundraisers = Fundraiser.query.filter_by(is_active=True).all()
    for fundraiser in fundraisers:
        pages.append({
            'loc': url_for('fundraiser_detail', id=fundraiser.id, _external=True),
            'changefreq': 'weekly',
            'priority': '0.8',
            'lastmod': fundraiser.created_at.strftime('%Y-%m-%d')
        })
    
    # Турниры
    tournaments = Tournament.query.filter(Tournament.date >= datetime.utcnow()).all()
    for tournament in tournaments:
        pages.append({
            'loc': url_for('tournament_detail', id=tournament.id, _external=True),
            'changefreq': 'weekly',
            'priority': '0.8',
            'lastmod': tournament.created_at.strftime('%Y-%m-%d')
        })
    
    # Новости
    news_items = News.query.order_by(News.created_at.desc()).limit(100).all()
    for news_item in news_items:
        pages.append({
            'loc': url_for('news_detail', id=news_item.id, _external=True),
            'changefreq': 'monthly',
            'priority': '0.7',
            'lastmod': news_item.created_at.strftime('%Y-%m-%d')
        })
    
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    return response


# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================

def init_db():
    """Инициализация базы данных и создание админа по умолчанию"""
    with app.app_context():
        db.create_all()
        
        # Создаем админа, если его еще нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin')
            admin.set_password('SportFund2026!Secure')
            db.session.add(admin)
            db.session.commit()
            print('Создан пользователь admin с безопасным паролем')
        
        # Создаем контактную информацию по умолчанию, если её нет
        if not ContactInfo.query.first():
            contact_info = ContactInfo(
                phone='+375 (XX) XXX-XX-XX',
                email='info@sportfund.by',
                telegram='',
                viber='',
                whatsapp='',
                vk='',
                instagram='',
                additional_info='Обновите контактную информацию в админ-панели'
            )
            db.session.add(contact_info)
            db.session.commit()
            print('Создана контактная информация по умолчанию')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

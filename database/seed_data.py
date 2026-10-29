import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal, init_db
from database.models import Movie, User, Rating

MOVIES_DATA = [
    {
        "title": "Начало",
        "release_year": 2010,
        "genres": "Фантастика, Боевик, Триллер",
        "director": "Кристофер Нолан",
        "cast": "Леонардо ДиКаприо, Джозеф Гордон-Левитт, Эллиот Пейдж, Том Харди",
        "description": "Кобб — искусный вор, лучший из лучших в опасном искусстве извлечения: он крадет ценные секреты из глубин подсознания во время сна. Ему предлагают необычное задание — не украсть мысль, а внедрить ее.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/447301.jpg"
    },
    {
        "title": "Интерстеллар",
        "release_year": 2014,
        "genres": "Фантастика, Драма, Приключения",
        "director": "Кристофер Нолан",
        "cast": "Мэттью МакКонахи, Энн Хэтэуэй, Джессика Честейн, Майкл Кейн",
        "description": "Когда засуха, пыльные бури и вымирание растений приводят человечество к продовольственному кризису, коллектив исследователей отправляется сквозь червоточину в поисках планеты с подходящими для людей условиями.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/258687.jpg"
    },
    {
        "title": "Матрица",
        "release_year": 1999,
        "genres": "Фантастика, Боевик",
        "director": "Лана Вачовски, Лилли Вачовски",
        "cast": "Киану Ривз, Лоренс Фишбёрн, Кэрри-Энн Мосс, Хьюго Уивинг",
        "description": "Хакер Нео узнает страшную правду: привычная реальность — это симуляция, созданная подчинившим мир искусственным интеллектом, а человечество используется как источник энергии.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/301.jpg"
    },
    {
        "title": "Темный рыцарь",
        "release_year": 2008,
        "genres": "Боевик, Криминал, Драма",
        "director": "Кристофер Нолан",
        "cast": "Кристиан Бэйл, Хит Леджер, Аарон Экхарт, Майкл Кейн",
        "description": "Бэтмен поднимает ставки в войне с криминалом в Готэме. Однако город погружается в хаос, когда на сцену выходит загадочный преступный гений по прозвищу Джокер.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/111543.jpg"
    },
    {
        "title": "Бегущий по лезвию 2049",
        "release_year": 2017,
        "genres": "Фантастика, Детектив, Драма",
        "director": "Дени Вильнёв",
        "cast": "Райан Гослинг, Харрисон Форд, Ана де Армас, Сильвия Хукс",
        "description": "Офицер полиции Кей — репликант, выслеживающий сбежавших сородичей. Случайно он раскрывает секрет, способный нарушить хрупкое равновесие между людьми и искусственными созданиями.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/589290.jpg"
    },
    {
        "title": "Аватар",
        "release_year": 2009,
        "genres": "Фантастика, Приключения, Боевик",
        "director": "Джеймс Кэмерон",
        "cast": "Сэм Уортингтон, Зои Салдана, Сигурни Уивер, Стивен Лэнг",
        "description": "Бывший морпех Джейк Салли прилетает на планету Пандора, населенную расой На'ви. Привязавшись к местным жителям, он возглавляет восстание против земных колонизаторов.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/589290.jpg"
    },
    {
        "title": "Мстители: Финал",
        "release_year": 2019,
        "genres": "Фантастика, Боевик, Приключения",
        "director": "Энтони Руссо, Джо Руссо",
        "cast": "Роберт Дауни мл., Крис Эванс, Марк Руффало, Крис Хемсворт",
        "description": "Оставшиеся в живых члены команды Мстителей и их союзники должны объединиться, чтобы исправить разрушительные последствия щелчка Таноса и вернуть стертую половину вселенной.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/843650.jpg"
    },
    {
        "title": "Крестный отец",
        "release_year": 1972,
        "genres": "Криминал, Драма",
        "director": "Фрэнсис Форд Коппола",
        "cast": "Марлон Брандо, Аль Пачино, Джеймс Каан, Дайан Китон",
        "description": "История сицилийской мафиозной семьи Корлеоне в Нью-Йорке. Глава клана дон Вито Корлеоне передает бразды правления своему младшему сыну Майклу, не желавшему связывать жизнь с криминалом.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/325.jpg"
    },
    {
        "title": "Крестный отец 2",
        "release_year": 1974,
        "genres": "Криминал, Драма",
        "director": "Фрэнсис Форд Коппола",
        "cast": "Аль Пачино, Роберт Де Ниро, Роберт Дюваль, Дайан Китон",
        "description": "Две временные линии: становление юного Вито Корлеоне в начале XX века и укрепление мафиозной империи под руководством его повзрослевшего сына Майкла в конце 1950-х.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/325.jpg"
    },
    {
        "title": "Криминальное чтиво",
        "release_year": 1994,
        "genres": "Криминал, Драма",
        "director": "Квентин Тарантино",
        "cast": "Джон Траволта, Ума Турман, Сэмюэл Л. Джексон, Брюс Уиллис",
        "description": "Нелинейная история криминального мира Лос-Анджелеса: двое бандитов ведут философские беседы, боксер нарушает уговор о бое, а грабители пытаются захватить закусочную.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/342.jpg"
    },
    {
        "title": "Славные парни",
        "release_year": 1990,
        "genres": "Криминал, Драма, Биография",
        "director": "Мартин Скорсезе",
        "cast": "Роберт Де Ниро, Рэй Лиотта, Джо Пеши, Лоррейн Бракко",
        "description": "История Генри Хилла, который с детства мечтал стать гангстером и шаг за шагом пробивал себе путь в итальянской мафии Нью-Йорка, рискуя всем ради роскоши и власти.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/325.jpg"
    },
    {
        "title": "Побег из Шоушенка",
        "release_year": 1994,
        "genres": "Драма",
        "director": "Фрэнк Дарабонт",
        "cast": "Тим Роббинс, Морган Фриман, Боб Гантон, Уильям Сэдлер",
        "description": "Успешный банкир Энди Дюфрейн несправедливо осужден на два пожизненных срока за убийство жены и попадает в одну из самых суровых тюрем Новой Англии — Шоушенк.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/326.jpg"
    },
    {
        "title": "Бойцовский клуб",
        "release_year": 1999,
        "genres": "Драма, Триллер",
        "director": "Дэвид Финчер",
        "cast": "Брэд Питт, Эдвард Нортон, Хелена Бонем Картер, Мит Лоаф",
        "description": "Уставший от рутины офисный клерк встречает харизматичного продавца мыла Тайлера Дердена, исповедующего философию разрушения. Они организуют подпольный бойцовский клуб.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/361.jpg"
    },
    {
        "title": "Форрест Гамп",
        "release_year": 1994,
        "genres": "Драма, Мелодрама, Комедия",
        "director": "Роберт Земекис",
        "cast": "Том Хэнкс, Робин Райт, Гэри Синиз, Салли Филд",
        "description": "Удивительная история жизни доброго и наивного Форреста Гампа, который благодаря открытому сердцу становится героем спорта, национальным любимцем и миллионером.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/448.jpg"
    },
    {
        "title": "Унесенные призраками",
        "release_year": 2001,
        "genres": "Анимация, Приключения, Фэнтези",
        "director": "Хаяо Миядзаки",
        "cast": "Руми Хираги, Мию Ирино, Мари Нацуки, Такаси Найто",
        "description": "Маленькая девочка Тихиро вместе с родителями попадает в заброшенный городок, населенный духами и богами. Чтобы спасти заколдованных родителей, ей предстоит пройти множество испытаний.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/370.jpg"
    },
    {
        "title": "Король Лев",
        "release_year": 1994,
        "genres": "Анимация, Приключения, Семейный",
        "director": "Роджер Аллерс, Роб Минкофф",
        "cast": "Мэттью Бродерик, Джереми Айронс, Джеймс Эрл Джонс, Вупи Голдберг",
        "description": "У величественного короля саванны Муфасы рождается наследник Симба. Завистливый дядя Шрам плетет интриги, стремясь захватить трон, и юному львенку предстоит найти свой путь домой.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/2360.jpg"
    },
    {
        "title": "ВАЛЛ-И",
        "release_year": 2008,
        "genres": "Анимация, Фантастика, Семейный",
        "director": "Эндрю Стэнтон",
        "cast": "Бен Бертт, Элисса Найт, Джефф Гарлин, Фред Уиллард",
        "description": "Трогательный робот-мусорщик ВАЛЛ-И столетиями прибирает опустевшую Землю. Его жизнь меняется, когда он встречает исследовательского робота ЕВУ и следует за ней к звездам.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/279102.jpg"
    },
    {
        "title": "Тайна Коко",
        "release_year": 2017,
        "genres": "Анимация, Приключения, Семейный, Комедия",
        "director": "Ли Анкрич, Эдриан Молина",
        "cast": "Энтони Гонсалес, Гаэль Гарсиа Берналь, Бенджамин Брэтт",
        "description": "12-летний Мигель мечтает стать музыкантом вопреки семейному запрету. В День мертвых он волшебным образом переносится в Страну Мертвых, чтобы найти своего предка.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/111543.jpg"
    },
    {
        "title": "История игрушек",
        "release_year": 1995,
        "genres": "Анимация, Комедия, Семейный",
        "director": "Джон Лассетер",
        "cast": "Том Хэнкс, Тим Аллен, Дон Риклз, Джим Варни",
        "description": "Игрушки мальчика Энди оживают, когда рядом нет людей. Лидерство ковбоя Вуди оказывается под угрозой с появлением суперсовременного космического рейнджера Базза Лайтера.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/442.jpg"
    },
    {
        "title": "Человек-паук: Через вселенные",
        "release_year": 2018,
        "genres": "Анимация, Боевик, Фантастика",
        "director": "Боб Персичетти, Питер Рэмзи, Родни Ротман",
        "cast": "Шамейк Мур, Джейк Джонсон, Хейли Стайнфелд, Махершала Али",
        "description": "Бруклинский подросток Майлз Моралес получает суперспособности и встречает альтернативных Людей-пауков из других измерений, чтобы остановить катастрофу вселенского масштаба.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/920265.jpg"
    },
    {
        "title": "Ла-Ла Ленд",
        "release_year": 2016,
        "genres": "Мелодрама, Драма, Комедия",
        "director": "Дэмьен Шазелл",
        "cast": "Райан Гослинг, Эмма Стоун, Розмари ДеУитт, Дж.К. Симмонс",
        "description": "История любви начинающей актрисы Мии и фанатичного джазового музыканта Себастьяна в солнечном Лос-Анджелесе. Успех в карьере ставит под угрозу их искренние чувства.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/841081.jpg"
    },
    {
        "title": "Амели",
        "release_year": 2001,
        "genres": "Комедия, Мелодрама",
        "director": "Жан-Пьер Жене",
        "cast": "Одри Тоту, Матьё Кассовиц, Рюфюс, Жамель Деббуз",
        "description": "Необычная девушка Амели живет в Париже с богатым воображением. Случайная находка вдохновляет ее тайно совершать добрые поступки, меняющие жизни незнакомцев.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/341.jpg"
    },
    {
        "title": "Отель «Гранд Будапешт»",
        "release_year": 2014,
        "genres": "Комедия, Приключения, Детектив",
        "director": "Уэс Андерсон",
        "cast": "Рэйф Файнс, Тони Револори, Сирша Ронан, Эдриан Броуди",
        "description": "Захватывающие похождения безупречного консьержа месье Густава и его верного помощника, юного портье Зеро Мустафы, вокруг кражи бесценной картины эпохи Возрождения.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/683999.jpg"
    },
    {
        "title": "Вечное сияние чистого разума",
        "release_year": 2004,
        "genres": "Фантастика, Мелодрама, Драма",
        "director": "Мишель Гондри",
        "cast": "Джим Керри, Кейт Уинслет, Элайджа Вуд, Марк Руффало",
        "description": "Джоэл и Клементина после тяжелого расставания решают стереть друг друга из памяти с помощью новейшей технологии, однако в процессе Джоэл понимает, что все еще любит ее.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/5492.jpg"
    },
    {
        "title": "Эта дурацкая любовь",
        "release_year": 2011,
        "genres": "Комедия, Мелодрама, Драма",
        "director": "Гленн Фикарра, Джон Рекуа",
        "cast": "Стив Карелл, Райан Гослинг, Джулианна Мур, Эмма Стоун",
        "description": "Семейная жизнь Кэла рушится, когда жена просит о разводе. Молодой обаятельный ловелас Джейкоб берет его под свое крыло, обучая секретам привлекательности и уверенности.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/505898.jpg"
    },
    {
        "title": "Сияние",
        "release_year": 1980,
        "genres": "Ужасы, Драма, Детектив",
        "director": "Стэнли Кубрик",
        "cast": "Джек Николсон, Шелли Дювалл, Дэнни Ллойд, Скэтмэн Крозерс",
        "description": "Писатель Джек Торренс устраивается зимним смотрителем в отрезанный от мира горный отель «Оверлук». Зловещие призраки прошлого начинают сводить его с ума.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/409.jpg"
    },
    {
        "title": "Психо",
        "release_year": 1960,
        "genres": "Ужасы, Триллер, Детектив",
        "director": "Альфред Хичкок",
        "cast": "Энтони Перкинс, Джанет Ли, Вера Майлз, Джон Гэвин",
        "description": "Сбежавшая с деньгами клиента девушка останавливается на ночлег в уединенном придорожном мотеле, хозяин которого — скромный парень Норман Бейтс с пугающими семейными тайнами.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/409.jpg"
    },
    {
        "title": "Паразиты",
        "release_year": 2019,
        "genres": "Триллер, Драма, Комедия",
        "director": "Пон Чжун Хо",
        "cast": "Сон Кан Хо, Ли Сон Гюн, Чо Ё Чжон, Чхве У Шик",
        "description": "Бедное семейство Ким с помощью ловких махинаций по очереди устраивается на высокооплачиваемую работу в роскошный особняк богатой семьи Пак.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/589290.jpg"
    },
    {
        "title": "Молчание ягнят",
        "release_year": 1991,
        "genres": "Триллер, Криминал, Детектив",
        "director": "Джонатан Демми",
        "cast": "Джоди Фостер, Энтони Хопкинс, Скотт Гленн, Тед Левайн",
        "description": "Курсантка академии ФБР Кларисса Старлинг расследует серию жестоких убийств. Единственный, кто может помочь составить профиль маньяка — гениальный психиатр-людоед Ганнибал Лектер.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/409.jpg"
    },
    {
        "title": "Прочь",
        "release_year": 2017,
        "genres": "Ужасы, Триллер, Детектив",
        "director": "Джордан Пил",
        "cast": "Дэниэл Калуя, Эллисон Уильямс, Кэтрин Кинер, Брэдли Уитфорд",
        "description": "Молодой темнокожий фотограф Крис приезжает на выходные в загородный дом родителей своей белой девушки, где за благочестивыми улыбками скрывается жуткий заговор.",
        "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/409.jpg"
    }
]

USERS_LIST = [
    {"username": "Алексей", "fav": ["Фантастика", "Боевик"], "low": ["Мелодрама"]},
    {"username": "Дмитрий", "fav": ["Криминал", "Драма"], "low": ["Анимация"]},
    {"username": "Екатерина", "fav": ["Анимация", "Семейный"], "low": ["Ужасы"]},
    {"username": "Михаил", "fav": ["Мелодрама", "Комедия"], "low": ["Боевик"]},
    {"username": "Анна", "fav": ["Ужасы", "Триллер"], "low": ["Комедия"]},
    {"username": "Сергей", "fav": ["Боевик", "Приключения"], "low": []},
    {"username": "Ольга", "fav": ["Фантастика", "Детектив"], "low": ["Мелодрама"]},
    {"username": "Иван", "fav": ["Драма", "Криминал"], "low": ["Фэнтези"]},
    {"username": "Мария", "fav": ["Семейный", "Анимация"], "low": ["Ужасы"]},
    {"username": "Павел", "fav": ["Триллер", "Детектив"], "low": ["Комедия"]},
]


def seed_database(force_refresh: bool = False):
    init_db()
    db = SessionLocal()

    try:
        if force_refresh:
            db.query(Rating).delete()
            db.query(Movie).delete()
            db.query(User).delete()
            db.commit()

        existing_movies = db.query(Movie).count()
        if existing_movies >= len(MOVIES_DATA) and not force_refresh:
            return

        for m in MOVIES_DATA:
            movie = Movie(
                title=m["title"],
                release_year=m["release_year"],
                genres=m["genres"],
                director=m["director"],
                cast=m["cast"],
                description=m["description"],
                poster_url=m["poster_url"]
            )
            db.add(movie)
        db.commit()

        all_movies = db.query(Movie).all()
        for movie in all_movies:
            movie.poster_url = f"app/static/posters/{movie.id}.jpg"
        db.commit()

        random.seed(42)
        for u_data in USERS_LIST:
            user = User(username=u_data["username"])
            db.add(user)
            db.commit()

            for movie in all_movies:
                if random.random() > 0.65:
                    continue

                movie_genres = [g.strip() for g in movie.genres.split(",")]
                is_fav = any(g in u_data["fav"] for g in movie_genres)
                is_low = any(g in u_data["low"] for g in movie_genres)

                if is_fav:
                    score = random.choice([4.0, 4.5, 5.0])
                elif is_low:
                    score = random.choice([1.0, 1.5, 2.0, 2.5])
                else:
                    score = random.choice([3.0, 3.5, 4.0])

                rating_date = datetime.utcnow() - timedelta(days=random.randint(1, 100))
                rating = Rating(
                    user_id=user.id,
                    movie_id=movie.id,
                    rating=score,
                    timestamp=rating_date
                )
                db.add(rating)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force_refresh=True)
    print("Database seeded with Russian movies, reviews and users.")

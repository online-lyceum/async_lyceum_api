from datetime import time

import asyncpg

from async_lyceum_api import app


async def create_tables():
    async with app['pool'].acquire() as conn:
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS School (
                        school_id SERIAL PRIMARY KEY UNIQUE,
                        name VARCHAR NOT NULL UNIQUE,
                        address VARCHAR
                    );
            ''')
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS Teacher (
                        teacher_id SERIAL PRIMARY KEY UNIQUE,
                        name VARCHAR
                    );
            ''')
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS LessonTime (
                        lesson_time_id SERIAL PRIMARY KEY UNIQUE,
                        school_id INT NOT NULL,
                        weekday INT NOT NULL,
                        week INT NULL,
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        CONSTRAINT fk_school_id
                            FOREIGN KEY (school_id)
                                REFERENCES School(school_id)
                    );
            ''')
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS Lesson (
                        lesson_id SERIAL PRIMARY KEY UNIQUE,
                        school_id INT NOT NULL,
                        name VARCHAR NOT NULL,
                        teacher_id INT NOT NULL,
                        lesson_time_id INT NOT NULL,
                        CONSTRAINT fk_school_id
                            FOREIGN KEY (school_id)
                                REFERENCES School(school_id),
                        CONSTRAINT fk_teacher_id
                            FOREIGN KEY (teacher_id)
                                REFERENCES Teacher(teacher_id),
                        CONSTRAINT fk_lesson_time_id
                            FOREIGN KEY (lesson_time_id)
                                REFERENCES LessonTime(lesson_time_id),
                        CONSTRAINT uq_lesson
                            UNIQUE (
                                school_id, 
                                name, 
                                lesson_time_id, 
                                teacher_id
                            )
                    );
            ''')
        await conn.execute('''
                    CREATE TABLE IF NOT EXISTS Class (
                        class_id SERIAL PRIMARY KEY UNIQUE,
                        number INT NOT NULL,
                        letter VARCHAR,
                        school_id INT NOT NULL,
                        teacher_id INT,
                        CONSTRAINT fk_teacher_id
                            FOREIGN KEY (teacher_id)
                                REFERENCES Teacher(teacher_id),
                        CONSTRAINT fk_school_id
                            FOREIGN KEY (school_id)
                                REFERENCES School(school_id),
                        CONSTRAINT uq_class
                        UNIQUE (number, letter, school_id)
                    );
            ''')
        await conn.execute('''
                CREATE TABLE IF NOT EXISTS Subgroup (
                    subgroup_id SERIAL PRIMARY KEY UNIQUE,
                    class_id INT NOT NULL,
                    name VARCHAR,
                    CONSTRAINT fk_group_id
                        FOREIGN KEY (class_id)
                            REFERENCES Class(class_id),
                    CONSTRAINT uq_class_id_name
                        UNIQUE (class_id, name)
                );
        ''')
        await conn.execute('''
                CREATE TABLE IF NOT EXISTS SubgroupLesson (
                    subgroup_lesson_id SERIAL PRIMARY KEY UNIQUE,
                    subgroup_id INT NOT NULL,
                    lesson_id INT NOT NULL,
                    CONSTRAINT fk_subgroup_id
                        FOREIGN KEY (subgroup_id)
                            REFERENCES Subgroup(subgroup_id),
                    CONSTRAINT fk_lesson_id
                        FOREIGN KEY (lesson_id)
                            REFERENCES Lesson(lesson_id),
                    CONSTRAINT uq_lesson_id_subgroup_id
                        UNIQUE (subgroup_id, lesson_id)
                );
        ''')


async def create_school(name, address):
    async with app['pool'].acquire() as conn:
        await conn.execute(f'''
            INSERT INTO School (name, address) VALUES
                ('{name}', '{address}')
            ON CONFLICT DO NOTHING;
        ''')


async def create_teacher(name):
    async with app['pool'].acquire() as conn:
        await conn.execute(f'''
            INSERT INTO Teacher (name) VALUES
                ('{name}')
            ON CONFLICT DO NOTHING;
        ''')


async def create_class(school_id, number, letter):
    async with app['pool'].acquire() as conn:
        await conn.execute(f'''
            INSERT INTO Class (school_id, number, letter) VALUES
                ('{school_id}', '{number}', '{letter}')
            ON CONFLICT DO NOTHING;
        ''')
        res = await conn.fetchrow(f'''
            SELECT class_id FROM Class
                WHERE school_id = '{school_id}' AND
                      number = '{number}' AND
                      letter = '{letter}'
        ''')
        await conn.execute(f'''
            INSERT INTO Subgroup (class_id, name) VALUES
                ('{res['class_id']}', 'default')
            ON CONFLICT DO NOTHING;
        ''')
        return res['class_id']


async def create_lesson(name, start_time, end_time, weekday, week=None,
                        teacher_id=None, *, class_id=None, subgroup_id=None):
    if isinstance(start_time, list):
        start_time = time(*start_time)
    if isinstance(end_time, list):
        end_time = time(*end_time)
    if class_id is None and subgroup_id is None:
        raise TypeError('Set class_id or subgroup_id')
    async with app['pool'].acquire() as conn:
        conn: asyncpg.Connection
        if class_id is not None:
            school_id_row = await conn.fetchrow(f'''
                    SELECT school_id 
                        FROM Class
                    WHERE class_id = '{class_id}'
            ''')
        if subgroup_id is not None:
            school_id_row = await conn.fetchrow(f'''
                    SELECT school_id 
                        FROM Class
                    JOIN Subgroup ON Class.class_id = Subgroup_id.class_id
                    WHERE Subgroup.subgroup_id = '{subgroup_id}'
            ''')
        school_id = school_id_row['school_id']
        await conn.execute(f'''
                INSERT INTO LessonTime (
                            school_id, 
                            start_time, 
                            end_time,
                            weekday,
                            week
                        ) VALUES
                    ('{school_id}', 
                    '{start_time}', 
                    '{end_time}', 
                    '{weekday}',
                    {f"'{week}'" if week is not None else "null"})
                ON CONFLICT DO NOTHING;
        ''')
        lesson_time_id_row = await conn.fetchrow(f'''
                SELECT lesson_time_id 
                    FROM LessonTime
                WHERE start_time = '{start_time}' AND 
                      end_time = '{end_time}'
        ''')
        lesson_time_id = lesson_time_id_row['lesson_time_id']
        await conn.execute(f'''
                INSERT INTO Lesson (
                        school_id, 
                        name, 
                        lesson_time_id, 
                        teacher_id
                    ) VALUES (
                        '{school_id}', 
                        '{name}', 
                        '{lesson_time_id}', 
                        '{teacher_id}'
                    ) ON CONFLICT DO NOTHING;
        ''')
        lesson_id_row = await conn.fetchrow(f'''
                SELECT lesson_id FROM Lesson
                    WHERE name = '{name}' AND 
                          lesson_time_id = '{lesson_time_id}'
        ''')
        lesson_id = lesson_id_row['lesson_id']
        if subgroup_id is not None:
            await conn.execute(f'''
                    INSERT INTO SubgroupLesson (
                                    lesson_id,
                                    subgroup_id
                                    ) VALUES
                        ('{lesson_id}', '{subgroup_id}')
                    ON CONFLICT DO NOTHING
            ''')
        elif class_id is not None:
            subgroups = await conn.fetch(f'''
                    SELECT subgroup_id FROM Subgroup
                        WHERE class_id = '{class_id}' 
            ''')
            await conn.execute(f'''
                    INSERT INTO SubgroupLesson (
                                    lesson_id, 
                                    subgroup_id
                                    ) VALUES
                        {', '.join([f"('{lesson_id}', "
                                    f"'{subgroup_row['subgroup_id']}')"
                                    for subgroup_row in subgroups])}
                    ON CONFLICT DO NOTHING;
            ''')
        return lesson_id


async def get_times(school_id: int):
    async with app['pool'].acquire() as connection:
        lessons = await connection.fetch('''
                SELECT  
                        Class.class_id,
                        Class.letter,
                        Class.number,
                        Lesson.name,
                        LessonTime.weekday,
                        LessonTime.week,
                        LessonTime.start_time,
                        LessonTime.end_time,
                        Teacher.name as teacher_name
                    FROM Lesson
                JOIN Teacher
                    ON Lesson.teacher_id = Teacher.teacher_id
                JOIN SubgroupLesson 
                    ON Lesson.lesson_id = SubgroupLesson.lesson_id
                JOIN Subgroup
                    ON SubgroupLesson.subgroup_id = Subgroup.subgroup_id
                JOIN Class
                    ON Subgroup.class_id = Class.class_id
                JOIN LessonTime
                    ON Lesson.lesson_time_id = LessonTime.lesson_time_id 
                        AND Class.school_id = LessonTime.school_id
                WHERE Class.school_id = '{}'
        '''.format(school_id))

        raise NotImplementedError()


async def create_db():
    pass


async def get_class_lessons(class_id: int):
    async with app['pool'].acquire() as conn:
        lessons = await conn.fetch(f'''
                SELECT 
                        Lesson.name,
                        LessonTime.weekday,
                        LessonTime.week,
                        LessonTime.start_time,
                        LessonTime.end_time,
                        Teacher.name AS teacher_name,
                        Class.class_id
                    FROM Lesson
                JOIN Teacher
                    ON Lesson.teacher_id = Teacher.teacher_id
                JOIN SubgroupLesson
                    ON Lesson.lesson_id = SubgroupLesson.lesson_id
                JOIN Subgroup
                    ON SubgroupLesson.subgroup_id = Subgroup.subgroup_id
                JOIN Class
                    ON Subgroup.class_id = Class.class_id
                JOIN LessonTime
                    ON Lesson.lesson_time_id = LessonTime.lesson_time_id 
                        AND Class.school_id = LessonTime.school_id
                WHERE Class.class_id = '{class_id}'
        ''')

        raise NotImplementedError()


async def initialize_database(args):
    await create_db(args)
    await create_tables()
    await create_school('Лицей №2', 'Иркутск')
    await create_school('Школа №35', 'Иркутск')
    await create_class(1, 10, 'Б'),
    await create_class(1, 10, 'В'),
    await create_teacher('Светлана Николаевна')
    await create_teacher('Мария Александровна')
    await create_lesson('Разговоры о важном', time(8, 0), time(8, 30), 0,
                        class_id=1, teacher_id=1)
    await create_lesson('Алгебра и начало анализа', time(8, 35), time(9, 5), 0,
                        class_id=1, teacher_id=2)
    await create_lesson('Разговоры о важном', time(8, 0), time(8, 30), 0,
                        class_id=2, teacher_id=2)

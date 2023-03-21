from typing import Optional

from pydantic import BaseModel, Field

from .times import Time
from .teachers import Teacher


class BaseLesson(BaseModel):
    name: str
    start_time: Time
    end_time: Time
    week: Optional[bool] = None
    weekday: int = Field(0, ge=0, le=6)
    room: str
    school_id: int


class InternalLesson(BaseLesson):
    lesson_id: int

    class Config:
        orm_mode = True


class LessonCreate(BaseLesson):
    teacher_id: int


class Lesson(InternalLesson):
    teacher: Teacher


class LessonList(BaseModel):
    lessons: list[Lesson]


class LessonListWithWeekday(BaseModel):
    lessons: list[Lesson]
    weekday: int


class DayLessonList(LessonList):
    is_today: bool
    weekday: Optional[int]
    week: int

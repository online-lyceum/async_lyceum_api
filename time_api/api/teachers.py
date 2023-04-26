import logging

from fastapi import APIRouter, Depends

from time_api import schemas
from time_api.services.teachers import TeacherService
from time_api.services.auth import authenticate


logger = logging.getLogger(__name__)
router = APIRouter(
    prefix='/api/teachers',
    tags=['Teachers'],
)


@router.get(
    '',
    response_model=schemas.teachers.TeacherList
)
async def get_teachers(
        service: TeacherService = Depends(TeacherService)
):
    return await service.get_list()


@router.get(
    '/{teacher_id}',
    response_model=schemas.teachers.Teacher
)
async def get_teacher(
        teacher_id: int,
        service: TeacherService = Depends(TeacherService)
):
    return await service.get(teacher_id=teacher_id)


@router.post(
    '',
    response_model=schemas.teachers.Teacher,
    status_code=201,
    responses={
        200: {
            'model': schemas.teachers.Teacher,
            'description': 'Объект уже существует'
        }
    }
)
async def create_teacher(
        teacher: schemas.teachers.TeacherCreate,
        _=Depends(authenticate.teacher()),
        service: TeacherService = Depends(TeacherService)
):
    return await service.create(teacher)


@router.delete(
    '/{teacher_id}',
    status_code=204
)
async def delete_teacher(
        teacher_id: int,
        _=Depends(authenticate.teacher()),
        service: TeacherService = Depends(TeacherService)
):
    return await service.delete(teacher_id=teacher_id)


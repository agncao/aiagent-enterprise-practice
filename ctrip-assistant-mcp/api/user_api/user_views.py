from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from config import CONFIG,get_logger
from utils.jwt_utils import create_token
from utils.password_hash import get_hashed_password, verify_password
from api.user_api.user_schemas import UserLoginSchema, UserLoginRspSchema

# 创建分路由
router = APIRouter()

log = get_logger(__name__)


@router.post('/login/', description='用户登录', summary='用户登录', response_model=UserLoginRspSchema)
def login(obj_in: UserLoginSchema):
    # # 实现用户登录，成功之后返回用户信息，包括token
    # # 第一步：根据用户名去查询用户
    # user = _dao.get_user_by_username(session, obj_in.username)
    # log.info(user)
    # if not user:  # 用户不存在
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f'用户名{obj_in.username}，在数据库表中不存在!'
    #     )
    # if not verify_password(obj_in.password, user.password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f'登录密码错误'
    #     )
    # 代码执行到此，则登录成功
    return {
        'id': '3442 587242',
        'username': 'cczx',
        'phone': '18810212201',
        'real_name': '古惑仔',
        'token': create_token( '3442 587242:cczx')  # 创建token
    }


@router.post('/auth/', description='接口文档中认证表单提交')
def auth(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    接口文档中，用于接受认证表单提交的视图函数
    :param form_data: 表单数据
    :param session:
    :return:
    """
    # user = _dao.get_user_by_username(session, form_data.username)
    # log.info(user)
    # if not user:  # 用户不存在
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f'用户名{form_data.username}，在数据库表中不存在!'
    #     )
    # if not verify_password(form_data.password, user.password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=f'登录密码错误'
    #     )
    # 代码执行到此，则登录成功
    return {
        'access_token': create_token('3442 587242:cczx'),  # 创建token
        'token_type': 'bearer'
    }


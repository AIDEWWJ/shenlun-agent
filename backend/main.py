from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.init_db import init_database
from app.modules.admin.api import router as admin_users_router
from app.modules.ai_config.api import admin_router as admin_ai_configs_router
from app.modules.ai_config.api import user_router as user_ai_configs_router
from app.modules.auth.api import router as auth_router
from app.modules.dashboard.api import router as dashboard_router
from app.modules.email.api import router as admin_emails_router
from app.modules.library.api import router as library_router
from app.modules.notebook.api import router as notebook_router
from app.modules.paper.api import router as paper_router
from app.modules.practice.api import router as practice_router
from app.modules.practice.streaming import router as practice_streaming_router
from app.modules.prompt.api import router as admin_prompts_router
from app.modules.question.api import router as questions_router
from app.modules.review.api import router as review_router
from app.modules.system_config.api import router as admin_system_configs_router


OPENAPI_TAGS = [
    {
        "name": "系统",
        "description": "服务健康检查与根入口。",
    },
    {
        "name": "用户-认证与账户",
        "description": "注册、登录、找回密码、当前用户资料与密码修改。",
    },
    {
        "name": "用户-题库",
        "description": "题库浏览、题目详情、题目工作台与个人题目录入。",
    },
    {
        "name": "用户-统一题库",
        "description": "面向前台题库页的套卷与独立题聚合查询。",
    },
    {
        "name": "用户-练习与批改",
        "description": "答案草稿、练习会话、审题分析、提纲生成、提交批改与练习记录。",
    },
    {
        "name": "用户-批改记录与答疑",
        "description": "批改报告详情、历史批改记录与围绕报告的追问答疑。",
    },
    {
        "name": "用户-AI 配置",
        "description": "用户个人模型配置与系统默认模型查询。",
    },
    {
        "name": "用户-学习概览与统计",
        "description": "学习概览、题型统计、随机抽题与智能推荐。",
    },
    {
        "name": "用户-错题本与学习计划",
        "description": "错题本管理、自动归集错题、学习计划生成与查询。",
    },
    {
        "name": "后台-用户管理",
        "description": "管理员维护系统用户、角色与状态。",
    },
    {
        "name": "后台-系统 AI 配置",
        "description": "管理员维护系统级模型配置与默认模型。",
    },
    {
        "name": "后台-邮件管理",
        "description": "管理员维护 SMTP 配置与邮件模板。",
    },
    {
        "name": "后台-Prompt 管理",
        "description": "管理员维护系统级提示词模板。",
    },
    {
        "name": "后台-系统运行配置",
        "description": "管理员维护系统运行时阈值、词表与回退配置。",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="申论 Agent API",
    description="面向申论训练场景的后端接口，覆盖认证、题库、练习、批改、答疑、模型配置与后台管理。",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_origin_regex=settings.cors_allow_origin_regex if settings.app_env == "development" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

app.include_router(auth_router, prefix="/api")
app.include_router(user_ai_configs_router, prefix="/api")
app.include_router(admin_ai_configs_router, prefix="/api")
app.include_router(admin_users_router, prefix="/api")
app.include_router(admin_emails_router, prefix="/api")
app.include_router(admin_prompts_router, prefix="/api")
app.include_router(admin_system_configs_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(library_router, prefix="/api")
app.include_router(notebook_router, prefix="/api")
app.include_router(paper_router, prefix="/api")
app.include_router(review_router, prefix="/api")
app.include_router(practice_router, prefix="/api")
app.include_router(practice_streaming_router, prefix="/api")
app.include_router(questions_router, prefix="/api")


@app.get("/api/health", summary="健康检查", tags=["系统"])
def health_check():
    """检查服务是否正常运行。"""
    return {"status": "ok"}


@app.get("/", summary="服务根入口", tags=["系统"])
def root():
    """返回服务根入口说明。"""
    return {"message": "申论 Agent API is running"}

import json
from dataclasses import asdict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.capabilities.runtime_config import (
    LanguageAnalysisConfig,
    PointCompareConfig,
    PracticeFallbackConfig,
    RuleValidationConfig,
    StructureAnalysisConfig,
)
from app.modules.system_config.models import SystemConfig
from app.modules.system_config.repository import (
    create_system_config,
    get_system_config,
    list_system_configs,
    update_system_config,
)
from app.modules.system_config.schemas import SystemConfigListResponse, SystemConfigRead, SystemConfigUpsertRequest


SYSTEM_CONFIG_DEFAULTS: dict[str, tuple[str, str, dict]] = {
    "point_compare": ("ai_runtime", "要点比对配置", asdict(PointCompareConfig())),
    "structure_analysis": ("ai_runtime", "结构分析配置", asdict(StructureAnalysisConfig())),
    "language_analysis": ("ai_runtime", "语言分析配置", asdict(LanguageAnalysisConfig())),
    "rule_validation": ("ai_runtime", "规则校验配置", asdict(RuleValidationConfig())),
    "practice_fallback": ("ai_runtime", "练习回退配置", asdict(PracticeFallbackConfig())),
}


def _ensure_supported_key(config_key: str) -> None:
    if config_key not in SYSTEM_CONFIG_DEFAULTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的系统配置类型")


def ensure_default_system_configs(db: Session) -> None:
    changed = False
    for config_key, (category, name, content) in SYSTEM_CONFIG_DEFAULTS.items():
        if get_system_config(db, config_key) is None:
            create_system_config(
                db,
                SystemConfig(category=category, config_key=config_key, name=name, content_json=json.dumps(content, ensure_ascii=False)),
            )
            changed = True
    if changed:
        db.commit()


def list_admin_system_configs(db: Session) -> SystemConfigListResponse:
    ensure_default_system_configs(db)
    items = [SystemConfigRead.model_validate(_to_read(item)) for item in list_system_configs(db)]
    return SystemConfigListResponse(items=items, total=len(items))


def _to_read(config: SystemConfig) -> dict:
    return {
        "id": config.id,
        "category": config.category,
        "config_key": config.config_key,
        "name": config.name,
        "content_json": _load_json(config.content_json),
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


def _load_json(content_json: str) -> dict:
    try:
        loaded = json.loads(content_json)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def upsert_admin_system_config(db: Session, config_key: str, data: SystemConfigUpsertRequest) -> SystemConfigRead:
    _ensure_supported_key(config_key)
    category, _, default_content = SYSTEM_CONFIG_DEFAULTS[config_key]
    merged_content = {**default_content, **data.content_json}
    config = get_system_config(db, config_key)
    if config is None:
        config = create_system_config(
            db,
            SystemConfig(
                category=category,
                config_key=config_key,
                name=data.name,
                content_json=json.dumps(merged_content, ensure_ascii=False),
            ),
        )
    else:
        config = update_system_config(
            db,
            config,
            name=data.name,
            content_json=json.dumps(merged_content, ensure_ascii=False),
        )
    db.commit()
    db.refresh(config)
    return SystemConfigRead.model_validate(_to_read(config))


def load_point_compare_config(db: Session) -> PointCompareConfig:
    ensure_default_system_configs(db)
    config = get_system_config(db, "point_compare")
    payload = _load_json(config.content_json) if config else asdict(PointCompareConfig())
    return PointCompareConfig(**payload)


def load_structure_analysis_config(db: Session) -> StructureAnalysisConfig:
    ensure_default_system_configs(db)
    config = get_system_config(db, "structure_analysis")
    payload = _load_json(config.content_json) if config else asdict(StructureAnalysisConfig())
    return StructureAnalysisConfig(**payload)


def load_language_analysis_config(db: Session) -> LanguageAnalysisConfig:
    ensure_default_system_configs(db)
    config = get_system_config(db, "language_analysis")
    payload = _load_json(config.content_json) if config else asdict(LanguageAnalysisConfig())
    return LanguageAnalysisConfig(**payload)


def load_rule_validation_config(db: Session) -> RuleValidationConfig:
    ensure_default_system_configs(db)
    config = get_system_config(db, "rule_validation")
    payload = _load_json(config.content_json) if config else asdict(RuleValidationConfig())
    if "summary_question_type_hints" in payload:
        payload["summary_question_type_hints"] = tuple(payload["summary_question_type_hints"])
    if "applied_doc_type_hints" in payload:
        payload["applied_doc_type_hints"] = tuple(payload["applied_doc_type_hints"])
    return RuleValidationConfig(**payload)


def load_practice_fallback_config(db: Session) -> PracticeFallbackConfig:
    ensure_default_system_configs(db)
    config = get_system_config(db, "practice_fallback")
    payload = _load_json(config.content_json) if config else asdict(PracticeFallbackConfig())
    if "question_type_mapping" in payload:
        payload["question_type_mapping"] = tuple(tuple(item) for item in payload["question_type_mapping"])
    if "structured_question_types" in payload:
        payload["structured_question_types"] = tuple(payload["structured_question_types"])
    if "structured_hints" in payload:
        payload["structured_hints"] = tuple(payload["structured_hints"])
    if "default_hints" in payload:
        payload["default_hints"] = tuple(payload["default_hints"])
    return PracticeFallbackConfig(**payload)

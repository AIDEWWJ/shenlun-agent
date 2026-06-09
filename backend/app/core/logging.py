"""应用日志基础配置。"""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """配置全局日志。"""

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

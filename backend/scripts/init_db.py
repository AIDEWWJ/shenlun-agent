from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.init_db import init_database


if __name__ == "__main__":
    print("开始初始化数据库...")
    init_database()
    print("数据库初始化完成。")

import os
import re

ENV_NAME = "TG_ALLOWED_USER_IDS"


def parse_allowed_user_ids(value: str) -> frozenset[int]:
    items = [item for item in re.split(r"[\s,;]+", value.strip()) if item]
    if not items:
        raise RuntimeError(f"必须设置 {ENV_NAME}，例如：{ENV_NAME}=123456789")
    invalid = [item for item in items if not item.isdigit() or int(item) <= 0]
    if invalid:
        raise RuntimeError(f"{ENV_NAME} 包含无效 UID：{', '.join(invalid)}")
    return frozenset(int(item) for item in items)


ALLOWED_USER_IDS = parse_allowed_user_ids(os.environ.get(ENV_NAME, ""))

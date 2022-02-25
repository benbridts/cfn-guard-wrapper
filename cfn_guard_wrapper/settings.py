from pathlib import Path

from appdirs import user_cache_dir

APP_NAME = "CfnGuardWrapper"
APP_AUTHOR = "CfnGuardWrapper"

CONFIG_FILE = ".cfn-guard-wrapper.yaml"

CACHE_DIR = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
REPO_DIR = CACHE_DIR / "repositories"
RULE_DIR = CACHE_DIR / "rules"

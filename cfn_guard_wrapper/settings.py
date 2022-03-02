from pathlib import Path

from appdirs import user_cache_dir

APP_NAME = "CfnGuardWrapper"
APP_AUTHOR = "CfnGuardWrapper"

CONFIG_FILE = ".cfn-guard-wrapper.yaml"

CACHE_DIR = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
REPO_DIR = CACHE_DIR / "repositories"
RULE_DIR = CACHE_DIR / "rules"

DEFAULT_CONFIG_YAML = """
sources:
  IanMcKay:
    type: git
    url: https://github.com/iann0036/cfn-guard-rules.git
    folder: rules
  BenBridts:
    type: git
    url: https://github.com/benbridts/cfn-guard-rules.git
    folder: rules
"""

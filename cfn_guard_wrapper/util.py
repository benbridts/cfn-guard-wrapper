import dataclasses
import enum
import os.path
import tempfile
from typing import List, Optional, Mapping

import invoke.context
import yaml

from .exceptions import ConfigFileNotFoundError
from .settings import RULE_DIR, REPO_DIR, CONFIG_FILE
from pathlib import Path


@enum.unique
class GuardRuleStatus(enum.Enum):
    compliant = enum.auto()
    not_compliant = enum.auto()
    not_applicable = enum.auto()


@dataclasses.dataclass
class Source:
    id: str

    def download(self, c: invoke.context.Context, working_dir: Path) -> None:
        raise NotImplementedError("Method _download not implemented")


@dataclasses.dataclass
class GitSource(Source):
    url: str
    branch: str = "main"
    folder: str = ""

    def download(self, c: invoke.context.Context, working_dir: Path) -> None:
        if not (working_dir / ".git").exists():
            c.run(f"git clone {self.url} .", hide="both")
        c.run(f"git checkout {self.branch}", hide="both")
        c.run(f"git pull --ff-only", hide="out")
        c.run(f"git reset --hard HEAD", hide="out")


@dataclasses.dataclass
class GuardRuleResult:
    id: str
    rule_file: str
    template_file: str
    status: GuardRuleStatus
    path: Optional[str] = None
    reason: Optional[str] = None
    _original: Optional[Mapping] = None

    @property
    def description(self) -> str:
        description = f"{self.id}"
        if self.path:
            description += f" at {self.path}"
        description += f": {self.status.name}"
        if self.reason:
            description += f" ({self.reason})"
        return description

    @property
    def short_description(self) -> str:
        description = f"{self.id}"
        if self.path:
            description += f" at {self.path}"
        if self.reason:
            description += f": {self.reason}"
        else:
            description += f": {self.status.name}"
        return description

    @property
    def guard_command(self) -> str:
        return f"cfn-guard validate --type CFNTemplate -r {self.rule_file} -d {self.template_file}"


class SpooledTemporaryFileForInvoke(tempfile.SpooledTemporaryFile):
    def write(self, s: str) -> int:
        return super(SpooledTemporaryFileForInvoke, self).write(s.encode("utf-8"))


def non_guard_files(dir, files) -> list:
    return [
        x
        for x in files
        # it needs to be included unless it's a directory or it ends with .guard
        if not (os.path.isdir(os.path.join(dir, x)) or x.lower().endswith(".guard"))
    ]


@dataclasses.dataclass
class WrapperConfig:
    sources: List[Source]
    ignore: List[str] = dataclasses.field(default_factory=list)

    @classmethod
    def load(cls) -> "WrapperConfig":
        try:
            with open(CONFIG_FILE, "r") as fh:
                data = yaml.safe_load(fh)
        except FileNotFoundError as e:
            raise ConfigFileNotFoundError(f"Could not find {CONFIG_FILE}") from e

        sources = []
        for source, config in data.get("sources", {}).items():
            config_type = config.pop("type")
            if config_type == "git":
                sources.append(GitSource(id=source, **config))
            else:
                raise NotImplementedError(f"Unknown type {config_type}")

        return cls(
            sources=sources,
            ignore=data.get("ignore", []),
        )

import sys

from invoke import Program, Collection, Config
from . import tasks


class ProgramConfig(Config):
    # Use https://docs.pyinvoke.org/en/stable/concepts/configuration.html,
    # but with the prefix as name
    prefix = "cfn-guard-wrapper"


program = Program(
    # Version of the CLI
    version="0.1.0",
    # Where to find our tasks
    namespace=Collection.from_module(tasks),
    config_class=ProgramConfig,
)


if __name__ == "__main__":
    program.run(sys.argv)

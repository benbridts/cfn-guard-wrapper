import json
import shutil
import sys
from typing import List, MutableMapping

import invoke.context
from invoke import task

from .exceptions import ConfigFileNotFoundError
from .settings import RULE_DIR, REPO_DIR
from .util import GuardRuleResult, GuardRuleStatus, non_guard_files, WrapperConfig


@task
def clean(c):
    shutil.rmtree(RULE_DIR)
    shutil.rmtree(REPO_DIR)


@task
def download_rules(c, delete_repositories=False):
    assert isinstance(c, invoke.context.Context)
    try:
        config = WrapperConfig.load()
    except ConfigFileNotFoundError as e:
        print(e, file=sys.stderr)
        raise

    if RULE_DIR.exists():
        shutil.rmtree(RULE_DIR)
    RULE_DIR.mkdir(parents=True)

    if delete_repositories:
        shutil.rmtree(REPO_DIR)

    for source in config.sources:
        repo_dir = REPO_DIR / source.id
        repo_dir.mkdir(parents=True, exist_ok=True)
        with c.cd(repo_dir):
            print(f"getting rules for the source with id {source.id}", file=sys.stderr)
            source.download(c, repo_dir)

        if hasattr(source, "folder") and source.folder not in ["", "."]:
            src_dir = repo_dir / source.folder
        else:
            src_dir = repo_dir
        dest_dir = RULE_DIR / source.id
        shutil.copytree(src_dir, dest_dir, ignore=non_guard_files)


@task(download_rules, iterable=['template'])
def validate(c, template, verbose=False):
    config = WrapperConfig.load()

    results: List[GuardRuleResult] = []

    for t in template:
        output: invoke.runners.Result = c.run(
            f"cfn-guard validate --type CFNTemplate --data {t} --rules {RULE_DIR} --output-format json --show-summary none",
            hide="out",
            warn=True,
        )
        for line in output.stdout.splitlines():
            try:
                data = json.loads(line)
            except json.decoder.JSONDecodeError as e:
                print(line)
                raise

            rules_from = data["rules_from"][:-6] if data["rules_from"].endswith(".guard") else data["rules_from"]
            rule_file = str(RULE_DIR / data["rules_from"])
            template_file = t  # data['data_from'] only has the filename

            result_kwargs = {"rule_file": rule_file, "template_file": template_file}

            for name, details in data.get("not_compliant", {}).items():
                for error in details:
                    rule = error["rule"]
                    message = error["message"]
                    path = "/".join(["Resources", name, error["path"]]) if error["path"] else None
                    results.append(
                        GuardRuleResult(
                            id=f"{rules_from}/{rule}",
                            status=GuardRuleStatus.not_compliant,
                            path=path,
                            reason=message,
                            _original={name: details},
                            **result_kwargs,
                        )
                    )
            for rule in data.get("not_applicable", []):
                results.append(
                    GuardRuleResult(
                        id=f"{data['rules_from']}/{rule}",
                        status=GuardRuleStatus.not_applicable,
                        **result_kwargs,
                    )
                )
            for rule in data.get("compliant", []):
                results.append(
                    GuardRuleResult(
                        id=f"{data['rules_from']}/{rule}",
                        status=GuardRuleStatus.compliant,
                        **result_kwargs,
                    )
                )

    problem_overview: MutableMapping[str, MutableMapping[str, List]] = {}

    skipped = compliant = non_compliant = 0
    for result in results:
        if result.status == GuardRuleStatus.compliant:
            compliant += 1
            continue
        if result.status == GuardRuleStatus.not_applicable:
            skipped += 1
            continue
        if [True for x in config.ignore if result.id.startswith(x)]:
            skipped += 1
            continue

        if result.template_file not in problem_overview:
            problem_overview[result.template_file] = {}
        if result.rule_file not in problem_overview[result.template_file]:
            problem_overview[result.template_file][result.rule_file] = []
        problem_overview[result.template_file][result.rule_file].append(result)
        non_compliant += 1

    for template_file, rules in problem_overview.items():
        print(f"{template_file}:", file=sys.stderr)
        for rule_file, problem_list in rules.items():
            if verbose:
                print(problem_list[0].guard_command, file=sys.stderr)
            for result in problem_list:
                print("  " + result.short_description, file=sys.stderr)
                if verbose:
                    print(f"Original data:\n{json.dumps(result._original, indent=2)}", file=sys.stderr)

    print(
        f"""
    Summary:
    {compliant: 3d} compliant checks
    {skipped: 3d} skipped (not applicable or ignored) checks
    {non_compliant: 3d} non-compliant checks
    """,
        file=sys.stderr,
    )
    if non_compliant:
        exit(1)

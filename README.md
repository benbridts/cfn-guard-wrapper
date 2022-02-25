# cfn-guard-wrapper
Make cfn-guard easier to use

The current version assumes you have cfn-guard and git installed

## Installation
The preferred way to install this tool, is with `pipx`. Packages are not available
yet, but you can run (after installing pipx):

```shell
pipx install git+https://github.com/benbridts/cfn-guard-wrapper.git
```

## Usage
1. Put a `.cfn-guard-wrapper.yaml` file in the directory where you're going to 
   run the tool from (typically the same directory that contains your templates).
   See the file in this repository for an example 
2. Run `cfn-guard-wrapper validate {cloudformation_template_file}`
   - This will download rule files with git, according to the configuration file
   - The template will be checked against all the downloaded rule files


## Implementation
This a thin wrapper to make it easier to execute cfn-guard.
We leverage `invoke` to execute commands directly, so all actions are defined in
`cfn_guard_wrapper/tasks.py`
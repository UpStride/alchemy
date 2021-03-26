# Alchemy CLI

this is the command line interface (CLI) for alchemy

One parameter is mandatory : `log_file`, the path of the tensorboard log file to parse.

The other parameter can be passed using the command line or will be asked by the script to the user

These parameters are:
- `--user`: email to connect to alchemy
- `--password`: password to connect to alchemy
- `--step`: step between two points to upload
- `--project`: Alchemy project to update
- `--run`: Alchemy run to update
- `--tags`: tags associated with the run (only if new run)
- `--dataset`: dataset used in run (only if new run)
- `--model`: Neural Network model used in the run (only if new run)
- `--scalar_plots`: scalar graph to upload

Every parameter except ` log_file` can be stored in a yaml file, and provided with the `yaml_file`. An example can be seen in the file `example.yaml`

This script can be run "as is" with python 3

```
python alchemy_cli.py <log_file> <parameters>
```

But it can also be installed with setuptools
```
pip install [-e] .
```
or
```
python setup.py {install, develop}
```

and then be used directly with
```
alchemy_cli <log_fie> <parameters>
```

## Upload_everything

If your experiments are stored in a way that every event files comes with a corresponding yaml, you can use a dedicated script to upload runs based on a wildcard file pattern

```
bash upload_everything.sh "*my_pattern*" "my_password"
```
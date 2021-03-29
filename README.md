# Alchemy CLI

this is the software development kit (SDK) and command line interface (CLI) for alchemy

## install

to install this package run
```python
pip install upstride-alchemy
```

or clone this repository and run
```python
pip install [-e] .
```
or
```python
python setup.py {install, develop}
```

## SDK
To import the sdk in your project, do a simple

```python
import alchemy
```

you can now login to alchemy using your credentials and initialize the project :

```python
alchemy.login('your@email', 'yourpassword')
alchemy.init(project_name='project42', 
             run_name='mobilenet on cifar10', 
             dataset='cifar10', 
             model='mobilenet_v3', 
             tags=['pytorch'])
```

now you can simply call the `log` function to send results to the platform 

```python
alchemy.log(epochs=1, metrics={'accuracy': 0.8, 'loss': 3.1415, 'whatever metric you want': 0.9})
```

## Command line interface

this repository provides a script to update results from a tensorboard checkpoint : `alchemy_cli`

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

Every parameter except ` log_file` can be stored in a yaml file, and provided with the `yaml_file`. An example yaml file can be:
```yaml
user: your@email
project: my_project
run: my_run
scalar_plots:
 - my_metric1
 - my_metric2
tags:
 - tag1
 - tag2
dataset: my_dataset
model: my_model
```

This script can be run with
```bash
alchemy_cli <log_fie> <parameters>
```

### Upload_everything

If your experiments are stored in a way that every event files comes with a corresponding yaml, you can use a dedicated script to upload runs based on a wildcard file pattern

```
bash upload_everything.sh "*my_pattern*" "my_password"
```
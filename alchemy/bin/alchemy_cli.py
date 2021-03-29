#!/usr/bin/env python3
import argparse
import getpass
import math
import os
from typing import List

import requests
import tensorflow as tf
import yaml
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

N_POINTS_LIMIT = 300  # Maximum number of point to upload for one curve
ALCHEMY_BACKEND_URL = 'https://alchemyback.upstride.io'


parser = argparse.ArgumentParser(description='Cli for alchemy')
parser.add_argument('log_file', help='Tensorboard log file to parse')
parser.add_argument('--yaml_file', help="Path to yaml file containing parameters, overwritten by following arguments")
parser.add_argument('--user', help='email to connect to alchemy')
parser.add_argument('--password', help='password to connect to alchemy')
parser.add_argument('--step', type=int, default=1, help='step between two points to upload')
parser.add_argument('--project', help='Alchemy project to update')
parser.add_argument('--run', help='Alchemy run to update')
group = parser.add_argument_group('run options', 'If the run is new, you can add more parameters')
group.add_argument('--tags', help='Tags associated with selected run', nargs='*')
group.add_argument('--model', help='Model used in the selected run')
group.add_argument('--dataset', help='Dataset used in the selected run')
group.add_argument('--accept', '-y', action='store_true',
                   help='If selected, will not ask permission before creating a new run')
parser.add_argument('--scalar_plots', nargs='*', help='scalar graph to upload')


def login(username, password):
  """send a request to alchemy backend to get the user connection token
  """
  headers = {'content-type': 'application/json'}
  data = {'username': username,
          'password': password, }

  r = requests.get(ALCHEMY_BACKEND_URL + '/login', headers=headers, json=data)
  assert r.status_code == 200, f'status code: {r.status_code}, error: {r.text}'
  token = r.text
  return token


def get_requests(endpoint, token):
  return requests.get(ALCHEMY_BACKEND_URL + endpoint, headers={'Authorization': f'Bearer {token}'})


def post_requests(endpoint, data, token):
  return requests.post(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {token}'})


def put_requests(endpoint, data, token):
  return requests.put(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {token}'})


def ask_if_not_defined(variable, question, hidden=False):
  if not variable:
    print(f"\n{question}")
    if not hidden:
      user_input = input('> ')
    if hidden:
      user_input = getpass.getpass('> ')
    return user_input
  return variable


def get_project_id(token: str, project_name: str):
  """get the project id from the project name given by the user or by user inputs

  Args:
      token (str): connection token to Alchemy backend
      project_name (str): name provided by the user

  Returns: the project id
  """

  r = get_requests('/api/projects', token)
  projects = r.json()
  if project_name and (project_name in [p['name'] for p in projects]):
    # Then don't ask user
    for p in projects:
      if project_name == p['name']:
        project_id = p['id']
  else:
    # Ask user which project he is working on
    print("\nSelect a project")
    for i, project in enumerate(projects):
      print(f'{i} {project["name"]}')
    project_id = projects[int(input())]['id']
  print(f"project id : {project_id}")
  return project_id


def create_run(token: str, project_id: str, name: str,
               state: str, user: str, tags: List[str],
               dataset: str, model: str):
  if not name:
    print("\nNew run name:")
    name = input()
  if not tags:
    print("Please specify a list of tags, separated by spaces")
    tags = input().split(" ")

  if not dataset:
    print("Dataset:")
    dataset = input()

  if not model:
    print("Model:")
    model = input()
  run_info = {
      'name': name,
      'state': state or 'done',
      'user': user,
      'tags': tags,
      'dataset': dataset,
      'model': model
  }
  r = post_requests(f'/api/projects/{project_id}/runs', run_info, token)
  assert r.status_code == 200, f"error: {r.text}"
  return r.json()["id"]


def get_run_id(token: str, project_id: str, user: str, run_name: str, accept: bool, **kwargs):
  r = get_requests(f'/api/projects/{project_id}/runs', token)
  runs = r.json()
  run_id_by_names = {r['name']: r['id'] for r in runs}
  run_names_list = run_id_by_names.keys()
  if not run_name:
    # ask user which run he is working on
    print("\nSelect a run")
    print("0 New run")
    for i, name in enumerate(run_names_list):
      print(f'{i+1} {name}')
    user_input = int(input())

    if user_input == 0:
      # Then create a new run
      run_id = create_run(token, project_id, None, 'done', user, **kwargs)
    else:
      name = run_names_list[int(user_input) - 1]
      run_id = run_id_by_names[name]
  elif (run_name in run_names_list):
    # Then don't ask user
    run_id = run_id_by_names[run_name]
  else:
    # Create a new run
    if accept:
      answer = 'y'
    else:
      answer = None
    while answer not in ['y', 'n', '']:
      answer = input(f"Creating a new run named {run_name}, continue ? [Y,n]").lower()
    if answer == 'n':
      return
    else:
      run_id = create_run(token, project_id, run_name, 'done', user, **kwargs)
  print(f"run id : {run_id}")
  return run_id


def run_cli(log_file: str, user: str, password: str, step: int, project: str, run: str, scalar_plots: List[str], **kwargs):
  if not os.path.exists(log_file):
    print('log file not found')
    return

  # Login to alchemy
  user = ask_if_not_defined(user, "Please enter username")
  password = ask_if_not_defined(password, "Please enter password", hidden=True)
  token = login(user, password)

  # Get informations
  project_id = get_project_id(token, project)
  run_id = get_run_id(token, project_id, user, run, **kwargs)
  if run_id is None:
    print("Aborted")
    return

  # Prepare tensorflow logs
  print('\n load tensorboard file, this can take some time')
  event_acc = EventAccumulator(log_file, {'tensors': 10000, })
  event_acc.Reload()
  print('loading done')

  # Inside tensorboard, scalar_plots can be saved as scalars or as tensors (but most of the time as scalars)
  # First try to load scalars and if we found nothing then we load tensors
  names = event_acc.Tags()['scalars']
  event_containers = event_acc.Scalars
  events = {name: event_containers(name) for name in names}
  tensors = False
  if not names:
    names = event_acc.Tags()['tensors']
    # Filter tensors that are not scalars, i.e. images or histograms
    event_containers = event_acc.Tensors
    events = {}
    for name in names:
      if event_acc.summary_metadata[name].plugin_data.plugin_name == 'scalars':
        events[name] = event_containers(name)
    tensors = True

  # If the user didn't specify which plot to upload, then ask him
  if not scalar_plots:
    # Show all tags in the log file
    print('\npossible scalar plot to upload on Alchemy :')
    for i, name in enumerate(names):
      print(f'{i}- {name} ({len(events[name])} points)')
    print('please enter list of id separated by space')
    user_input = input()
    scalar_plots_ids = user_input.split(' ')
    scalar_plots = [names[int(i)] for i in scalar_plots_ids]

  data_plots = []
  for scalar_plot in scalar_plots:
    _, step_nums, vals = zip(*event_containers(scalar_plot))
    while len(step_nums)/step > N_POINTS_LIMIT:
      print(f'Too many points to upload for curve {scalar_plot}. Please choose a new step')
      user_input = input()
      step = int(user_input)

    # Select the points to upload. Here we have one constraint : we want the last point of the curve to be
    # uploaded, as it's often quite an important one
    points = []
    N = len(step_nums)
    n_points = math.ceil(N/step)
    for i in range(n_points):
      id = N - 1 - i * step

      if tensors:
        v = float(tf.make_ndarray(vals[id]))
      else:
        v = vals[id]
      points.append({'x': step_nums[id], 'y': v})

    data_plots.append({"name": scalar_plot, "points": points[::-1]})
  r = put_requests(f'/api/projects/{project_id}/runs/{run_id}/plots', {'plots': data_plots}, token)
  print(r.text)


def main():
  args = parser.parse_args()
  parameters = vars(args)
  yaml_file = parameters.pop("yaml_file", None)
  if yaml_file:
    with open(yaml_file, 'r') as f:
      # Merge params from args and from yaml file, priority is given to args
      yaml_params = yaml.load(f, Loader=yaml.SafeLoader)
      for k in parameters:
        if k in yaml_params and parameters[k] is None:
          parameters[k] = yaml_params[k]
  run_cli(**parameters)


if __name__ == "__main__":
  main()

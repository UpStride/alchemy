#!/usr/bin/python3
import argparse
import math
import os
from typing import List
import tensorflow as tf
import getpass

import requests
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

N_POINTS_LIMIT = 300  # Maximum number of point to upload for one curve
ALCHEMY_BACKEND_URL = 'https://alchemyback.upstride.io'
# ALCHEMY_BACKEND_URL = 'http://127.0.0.1:4443'


parser = argparse.ArgumentParser(description='Cli for alchemy')
parser.add_argument('log_file', help='Tensorboard log file to parse')
parser.add_argument('--user', help='email to connect to alchemy')
parser.add_argument('--password', help='password to connect to alchemy')
parser.add_argument('--step', type=int, default=1, help='step between two points to upload')
parser.add_argument('--project', help='Alchemy project to update')
parser.add_argument('--run', help='Alchemy run to update')
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


def main(log_file: str, user: str, password: str, step: int, project: str, run: str, scalar_plots: List[str]):
  if not os.path.exists(log_file):
    print('invalid log file')
    return

  # Login to alchemy
  user = ask_if_not_defined(user, "Please enter username")
  password = ask_if_not_defined(password, "Please enter password", hidden=True)
  token = login(user, password)

  # Ask user which project he is working on
  r = get_requests('/api/projects', token)
  projects = r.json()
  if project:
    assert project in [p['name'] for p in projects]
    for p in projects:
      if project == p['name']:
        project_id = p['id']    
  else:
    print("\nSelect a project")
    for i, project in enumerate(projects):
      print(f'{i} {project["name"]}')
    project_id = projects[int(input())]['id']
  print(f"project id : {project_id}")

  # ask user which run he is working on
  r = get_requests(f'/api/projects/{project_id}/runs', token)
  runs = r.json()
  if run:
    assert run in [r['name'] for r in runs]
    for r in runs:
      if run == r['name']:
        run_id = r['id']  
  else:
    print("\nSelect a run")
    print("0 New run")
    for i, run in enumerate(runs):
      print(f'{i+1} {run["name"]}')
    user_input = int(input())

    if user_input == 0:
      # Then create a new run
      print("\nNew run name:")
      name = input()
      print("Please specify a list of tags, separated by spaces")
      tags = input().split(" ")
      run_info = {
          'name': name,
          'state': 'done',
          'user': user,
          'tags': tags
      }
      r = post_requests(f'/api/projects/{project_id}/runs', run_info, token)
      assert r.status_code == 200, f"error: {r.text}"
      run_id = r.json()["id"]
    else:
      run_id = runs[int(user_input) - 1]['id']
  print(f"run id : {run_id}")

  # Prepare tensorflow logs
  print('\n load tensorboard file, this can take some time')
  event_acc = EventAccumulator(log_file, {'tensors': 10000,})
  event_acc.Reload()
  print('loading done')
  
  names = event_acc.Tags()['scalars']
  event_containers = event_acc.Scalars
  tensors = False
  if not names:
    names = event_acc.Tags()['tensors']
    event_containers = event_acc.Tensors
    tensors = True

  # If the user didn't specify which plot to upload, then ask him
  if not scalar_plots:
    # Show all tags in the log file
    print('\npossible scalar plot to upload on Alchemy :')
    for i, name in enumerate(names):
      print(f'{i}- {name} ({len(event_containers(name))} points)')
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


if __name__ == "__main__":
  args = parser.parse_args()
  main(**vars(args))

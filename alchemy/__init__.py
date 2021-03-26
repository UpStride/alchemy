import requests
from typing import Dict, List

__user = ''
__password = ''
__auth_token = ''
__project_id = None

ALCHEMY_BACKEND_URL = 'https://alchemyback.upstride.io'


class LoginError(Exception):
  pass


class UnknownProjectError(Exception):
  pass


class AlreadyExistingRunError(Exception):
  pass


class CreatingRunError(Exception):
  pass


def __get_requests(endpoint):
  return requests.get(ALCHEMY_BACKEND_URL + endpoint, headers={'Authorization': f'Bearer {__auth_token}'})


def __post_requests(endpoint, data):
  return requests.post(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {__auth_token}'})


def __put_requests(endpoint, data):
  return requests.put(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {__auth_token}'})


def login(user: str, password: str) -> None:
  global __user, __password, __auth_token
  __user = user
  __password = password
  # send a request to alchemy backend to get the user connection token
  headers = {'content-type': 'application/json'}
  data = {'username': __user,
          'password': __password, }

  r = requests.get(ALCHEMY_BACKEND_URL + '/login', headers=headers, json=data)
  if r.status_code != 200:
    raise LoginError(f'status code: {r.status_code}, error: {r.text}')
  __auth_token = r.text


def init(project_name: str, run_name: str, dataset: str,  model: str, tags=[], exist_ok=False) -> None:
  global __project_id

  # get project id
  r = __get_requests('/api/projects')
  projects = r.json()
  __project_id = None
  for p in projects:
    if project_name == p['name']:
      __project_id = p['id']
  if __project_id is None:
    raise UnknownProjectError()

  # get run id
  r = __get_requests(f'/api/projects/{__project_id}/runs')
  runs = r.json()
  run_id_by_names = {r['name']: r['id'] for r in runs}
  if run_name in run_id_by_names:
    if exist_ok:
      __run_id = run_id_by_names[run_name]
    else:
      raise AlreadyExistingRunError()
  else:
    # create the run
    run_info = {
        'name': run_name,
        'state': 'in progress',
        'user': __user,
        'tags': tags,
        'dataset': dataset,
        'model': model
    }
    r = __post_requests(f'/api/projects/{__project_id}/runs', run_info)
    if r.status_code != 200:
      raise CreatingRunError(r.text)
    __run_id = r.json()["id"]


def log(epochs: List[int], metrics: List[Dict[str, float]]) -> None:
  if type(epochs) != list:
    epoch = [epochs]
  if type(metrics) != list:
    message = [metrics]

  if len(metrics) != len(epochs):
    raise ValueError("metrics and epochs lists should have the same number of elements")

  plots = {}
  for k in metrics[0].keys():
    plots[k] = []

  for e, m in zip(epochs, metrics):
    for k in m.keys():
      plots[k].append({'x': e, 'y': m[k]})

  data_plots = [{"name": plot_name, "points": plots[plot_name]} for plot_name in messages[0].keys()]
  r = __put_requests(f'/api/projects/{__project_id}/runs/{__run_id}/plots', {'plots': data_plots})
  print(r.text)

import requests
from typing import Dict, List

p_user = ''
p_password = ''
p_auth_token = ''
p_project_id = None
p_run_id = None

ALCHEMY_BACKEND_URL = 'https://alchemyback.upstride.io'


class LoginError(Exception):
  pass


class UnknownProjectError(Exception):
  pass


class AlreadyExistingRunError(Exception):
  pass


class CreatingRunError(Exception):
  pass


def get_requests(endpoint):
  return requests.get(ALCHEMY_BACKEND_URL + endpoint, headers={'Authorization': f'Bearer {p_auth_token}'})


def post_requests(endpoint, data):
  return requests.post(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {p_auth_token}'})


def put_requests(endpoint, data):
  return requests.put(ALCHEMY_BACKEND_URL + endpoint, json=data, headers={'Authorization': f'Bearer {p_auth_token}'})


def login(user: str, password: str) -> None:
  global p_user, p_password, p_auth_token
  p_user = user
  p_password = password
  # send a request to alchemy backend to get the user connection token
  headers = {'content-type': 'application/json'}
  data = {'username': p_user,
          'password': p_password, }

  r = requests.get(ALCHEMY_BACKEND_URL + '/login', headers=headers, json=data)
  if r.status_code != 200:
    raise LoginError(f'status code: {r.status_code}, error: {r.text}')
  p_auth_token = r.text


def init(project_name: str, run_name: str, dataset: str,  model: str, tags=[], exist_ok=False) -> None:
  global p_project_id, p_run_id

  # get project id
  r = get_requests('/api/projects')
  projects = r.json()
  p_project_id = None
  for p in projects:
    if project_name == p['name']:
      p_project_id = p['id']
  if p_project_id is None:
    raise UnknownProjectError()

  # get run id
  r = get_requests(f'/api/projects/{p_project_id}/runs')
  runs = r.json()
  run_id_by_names = {r['name']: r['id'] for r in runs}
  if run_name in run_id_by_names:
    if exist_ok:
      p_run_id = run_id_by_names[run_name]
    else:
      raise AlreadyExistingRunError()
  else:
    # create the run
    run_info = {
        'name': run_name,
        'state': 'in progress',
        'user': p_user,
        'tags': tags,
        'dataset': dataset,
        'model': model
    }
    r = post_requests(f'/api/projects/{p_project_id}/runs', run_info)
    if r.status_code != 200:
      raise CreatingRunError(r.text)
    p_run_id = r.json()["id"]


def log(epochs: List[int], metrics: List[Dict[str, float]]) -> None:
  if type(epochs) != list:
    epochs = [epochs]
  if type(metrics) != list:
    metrics = [metrics]

  if len(metrics) != len(epochs):
    raise ValueError("metrics and epochs lists should have the same number of elements")

  plots = {}
  for k in metrics[0].keys():
    plots[k] = []

  for e, m in zip(epochs, metrics):
    for k in m.keys():
      plots[k].append({'x': e, 'y': m[k]})

  data_plots = [{"name": plot_name, "points": plots[plot_name]} for plot_name in metrics[0].keys()]
  r = put_requests(f'/api/projects/{p_project_id}/runs/{p_run_id}/plots', {'plots': data_plots})
  print(r.text)

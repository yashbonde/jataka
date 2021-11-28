class Stub:
  import time
  import json
  import requests
  VERSION = '0.0' # not sure how I'll use it but good to have

  def __init__(self, url, model_id):
    self.url = url
    self.model_id = model_id
    self.session = self.requests.Session()

  def __repr__(self):
    return f"<Stub({self.url}, {self.model_id}) | version: {self.VERSION}>"

  def __call__(self, data):
    if not isinstance(data, dict): raise Exception("data must be a dict and keys data to be logged")
    if "time" in data:
      raise Exception("time must not be in data")
    try:
      self.json.dumps(data)
    except:
      raise Exception("data must be json serializable")

    # send the data to the server
    data = {
      "spec": {
        "id": self.model_id,
        "time": self.time.time()
      },
      "user": data
    }
    r = self.session.post(f"{self.url}/log", json=data)
    if r.status_code != 200:
      print("Error:", r.status_code, r.text)
      raise Exception("logging failed")

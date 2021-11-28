import requests
import randomname

def get_job_id():
  return randomname.get_name()

class JatakaClient:
  def __init__(self, url, model_name = None, meta = None):
    self.url = url
    self.model_name = model_name or get_job_id()
    self.meta = meta
    
    self.session = requests.Session()
    self.session.headers.update({
      "Content-Type": "application/json",
      "Accept": "application/json"
    })

    # tell the server that you want to be logged
    print("Registering:", self.model_name)
    r = requests.post(
      f"{self.url}/register",
      json={"model_name": self.model_name, "meta": self.meta}
    )
    if r.status_code != 200:
      print("Error:", r.status_code, r.text)
      raise Exception("registering failed")
    data = r.json()
    exec(data["code"]); from stub import Stub
    self.stub = Stub(self.url, data["id"])

  def __repr__(self):
    return f"<JatakaClient: [{self.stub}] {self.model_name}>"
    
  def __call__(self, data):
    assert "time" not in data, "kwarg time is not allowed"
    self.stub(data)

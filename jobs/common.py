import requests
import time
import randomname

def get_job_id():
  return randomname.get_name()

def log(data):
  assert "time" not in data, "kwarg time is not allowed"
  assert "job_id" in data, "kwarg job_id is required"
  data["time"] = str(int(round(time.time() * 1000)))
  r = requests.post("http://localhost:8989/log", json=data)
  if r.status_code != 200:
    print("Error:", r.status_code, r.text)
    raise Exception("logging failed")

# this is the python version of the Go server, instead of creating a full fledged
# fastAPI server, I am writing a much simpler a asgi server.
# in this case I have added a 4 methods (routes) to the server,
# /     : returns the index.html file which is the (only) main page
# /ping : returns the system time
# /log  : writes the log to the log file
# /get  : returns the data from the log file
#
# Since I am using asgi, I will have to use some webserver. I have chosen to use
# uvicorn instead of uwsgi not to be confused with protocol-uwsgi.
# to run the server, use the following command:
# $ uvicorn asgi:app # --reload
#
# where applicable functions must be golang style by returning (output,error) tuple
#
# Structure
# =========
# 
# There is a sqlite3 DB called "jataka.db" in the same folder as this file, there
# is a "master_table" which stores (model_id, name, meta, time) and then each
# model_id gets its own table with the following columns: (key, value)
# since the user can send in data-key (ex. loss, images) we have two options:
#
# 1. we store the entire data in the table, but, storing dumplicate things is bad
# 2. we create a new column telling about the key, but, indexing would be harder
#    because of using two keys time and data-key
# 3. the index (or key of table) can be concatenation of time and data-key
#    so when querying we can query the exact keys we want
#
# Option 3 makes the most sense, index looks like this: "3769509001", "3769509002"
# the time of this writing is 1637695090:
# * 1600000000 was 2020/9/13, this date has already passed
# * 1700000000 will be 2023/11/15, code won't live long enough to reach that date
# so we can trim the first 2 digits because they will always be "16" and the last
# two digits will be the "id", and string to this "id" will be in the model_meta
# When querying we can get all the keys and filter those that do not have the last
# two digits.

import os
import time
import json
import hashlib
import inspect
import sqlite3
from uuid import uuid4
from functools import lru_cache
from pprint import pprint as pp
from json import loads as jloads, dumps as jdumps

TIME_START = "16"

# functions

def sha256(s):
  return hashlib.sha256(s.encode()).hexdigest()

# code below is stub that executes on the client side
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


# static items can be precached as this is tiny
with open(os.path.join(os.path.split(os.path.abspath(__file__))[0], "index.html"), "rb") as f:
  page = f.read()
exec_code = f'''open("./stub.py", "w").write("""{inspect.getsource(Stub)}""")'''


# basic CRUD DB for sqlite3: this is the full exhaustive database
class DB:
  def __init__(self, path = "jataka.db"):
    self.path = path

    # the DB has the following structure: master_table has model_ids
    # each model get's its own table with keys: timekey, value
    self.conn = sqlite3.connect(self.path)
    self.cursor = self.conn.cursor()

    # create the master table if it doesn't exist
    self.__execute('CREATE TABLE IF NOT EXISTS master_table (model_id TEXT PRIMARY KEY, name TEXT, meta TEXT, time REAL)')

    # cache the metadata for each model
    self.model_meta = {}
    all_models = self.__execute('''SELECT * FROM master_table''').fetchall()
    for model_id, name, meta, time in all_models:
      self.model_meta[model_id] = {"name": name, "meta": jloads(meta), "time": time}
    all_model_ids = [x[0] for x in all_models]

    # get counts of all items in tables and delete all the empty tables
    if len(all_model_ids) > 0:
      command = 'SELECT ' + ", ".join([f'(SELECT COUNT(*) FROM "{table}")' for i, table in enumerate(all_model_ids)])
      print("> Getting tables and deleting empty items")
      counts = self.__execute(command, log = False).fetchone()
      empty_tables = [model_id for i, model_id in enumerate(all_model_ids) if counts[i] == 0]
      for i, model_id in enumerate(all_model_ids):
        self.model_meta[model_id]["count"] = counts[i]

      for model_id in empty_tables:
        self.__execute(f'DROP TABLE "{model_id}"')
        del self.model_meta[model_id]
        self.__execute(f'DELETE FROM master_table WHERE model_id = "{model_id}"')

    pp(self.model_meta.keys())

    self.model_times = {}

  def __repr__(self):
    return f"<DB: {self.path}, {len(self.model_meta)}>"

  def __execute(self, sql, args = None, log=True):
    if log:
      print(">", sql)
    if args != None:
      return self.cursor.execute(sql, args)
    else:
      return self.cursor.execute(sql)

  def create(self, model_id, name, meta):
    try:
      self.__execute(f'CREATE TABLE IF NOT EXISTS "{model_id}" (timekey REAL, value TEXT)')
      self.conn.commit()
      _time = int(time.time())
      self.__execute('''INSERT INTO master_table VALUES (?, ?, ?, ?)''', (model_id, name, meta, _time))
      self.conn.commit()
      self.model_meta[model_id] = {"name": name, "meta": jloads(meta), "time": _time}
      return b"OK", None
    except Exception as e:
      return None, str(e).encode()

  def read(self, model_id, keys, from_time, to_time):
    if model_id not in self.model_meta:
      return None, b"Model id not found: " + str(model_id).encode()
    
    sql = f"SELECT * FROM {model_id}"
    keys_meta = set(self.model_meta[model_id]["meta"]["keys"])
    keys = set(keys)
    if not keys.issubset(keys_meta):
      return None, b"Keys not found: " + str(list(keys - keys_meta)).encode()
    
    # remove "16"
    if from_time != None:
      from_time = str(from_time)[2:]
      sql += f" WHERE timekey >= {from_time}00"
    if to_time != None:
      to_time = str(to_time)[2:]
      sql += f" AND timekey <= {to_time}00"
    
    # get & parse data
    store_data = self.__execute(sql).fetchall()
    keys_map = self.model_meta[model_id]["meta"]["keys"]

    res = {
      "keys_map": keys_map,
      "data": []
    }
    time_prev = 0
    for x in store_data:
      try:
        value = jloads(x[1]) # is this json
      except:
        value = x[1]
      
      timekey = str(x[0]).split(".")[0]
      key = timekey[-2:]
      key_str = keys_map[int(key)]
      time_ = int("16" + timekey[:-2])

      new_time = time_ > time_prev # boolean to tell if inserting in a new record
      if len(keys) and key_str not in keys:
        continue

      if new_time:
        res["data"].append({"time": time_, key: value})
      else:
        res["data"][-1][key] = value
      time_prev = time_
      
    return res, None

  def read_all(self):
    return self.model_meta

  @lru_cache()
  def get_keys(self, model_id):
    return self.model_meta[model_id].setdefault("keys", [])

  def update(self, model_id, data):
    if model_id not in self.model_meta:
      return None, "model_id not found"
    
    new_ = model_id in self.model_times
    if new_:
      self.model_times[model_id] = int(time.time())
    _time = str(time.time()).split(".")[0][2:]
    if not new_ and self.model_times[model_id] == int(_time):
      # record data on a second/second basis
      return b"OK", None

    self.model_times[model_id] = int(_time)
    try:
      all_keys = self.get_keys(model_id)
      data_keys = set(data.keys())
      diff_keys = data_keys.difference(set(all_keys))
      for x in diff_keys:
        self.model_meta[model_id]["keys"].append(x)
      
      if len(diff_keys) > 0:
        self.__execute(f'UPDATE master_table SET meta = ? WHERE model_id = ?', (jdumps(self.model_meta[model_id]), model_id))
        self.conn.commit()

      insertions = []
      for x in data_keys:
        _key = f'"{_time}{all_keys.index(x):02d}"'
        if isinstance(data[x], dict):
          insertions.append(f"({_key}, '{jdumps(data[x])}')")
        else:
          insertions.append(f"({_key}, {data[x]})")
      insertions = f"INSERT INTO '{model_id}' (timekey, value) VALUES" + ", ".join(insertions)
      self.__execute(insertions, log=False)
      self.conn.commit()
      return b"OK", None
    except Exception as e:
      return None, str(e).encode()

  def delete(self, model_id):
    # delete model_id table then entry from master_table
    if model_id not in self.model_meta:
      return None, "model_id not found"
    self.__execute(f'''DROP TABLE {model_id}''')
    self.__execute(f'''DELETE FROM master_table WHERE model_id = "{model_id}"''')
    self.conn.commit()
    return b"OK", None


# Server Code
class JatakaServer:
  def __init__(self):
    self.db = DB()

  # ===== functions performed by the server ===== #

  def _log(self, data):
    """log the data to the log file, each data packet from the client
    will contain user logged data ("user") and autogenerated data ("spec")"""
    try:
      data = jloads(data.decode())
    except:
      return b"", b"invalid json"

    if "spec" not in data:
      return b"", b"key 'spec' is required"
    if "user" not in data:
      return b"", b"key 'user' is required"

    out, err = self.db.update(data["spec"]["id"], data["user"])
    if err != None:
      print("error logging data:", err)
    return out, err

  def _get(self, data):
    """get the data from the DB. query body must look like:
    {
      # string 'query' must be present
      "query: None or {
        "model_id": required, # string 'model_id' must be present
        "keys": None or [],   # list of keys to be returned
        "from": None or int,  # int, unix timestamp
        "to": None or int,    # int, unix timestamp
      }
    }

    if query == None: returns the master_table
    else: returns things on model to model basis

    There is difference between _log and _get data. _get data is retrieved
    on time basis 
    """
    try:
      data = jloads(data.decode())
    except:
      return b"", b"invalid json"
    print("<", data)
    
    if "query" not in data:
      return b"", b"key 'query' is required in request"

    q = data["query"]
    if q == None:
      # in this case return the master table with all the data
      return jdumps(self.db.read_all()).encode(), None
    elif isinstance(q, dict):
      model_id = q.pop("model_id", None)
      if model_id == None:
        return b"", b"key 'model_id' is required in request"
      
      keys = q.pop("keys", [])
      from_ = q.pop("from", None)
      to_ = q.pop("to", None)

      if len(q) > 0:
        return b"", b"unrecognized keys in request: " + ",".join(tuple(q.keys())).encode()

      out, err = self.db.read(model_id, keys, from_, to_)
      if err != None:
        print("error getting data:", err)
      print(out)
      return out, err

    else:
      return b"", b"value to 'query' must be a dict or None, got: " + str(type(q)).encode()

  def _register(self, body):
    """register a model"""
    try:
      body = jloads(body.decode())
    except:
      return b"", b"invalid json"

    _id = sha256(str(uuid4())) # unique key for this client
    _name = body.get("model_name", None)
    _meta = body.get("meta", None)

    if _meta != None:
      try:
        print(type(_meta))
        type(_meta) == dict
      except Exception as e:
        return b"", str(e).encode()

    _, err = self.db.create(_id, _name, jdumps(_meta))
    if err != None:
      print("error:", err)
      return b"", err

    return jdumps({"id": _id, "code": exec_code}), b""

   # ===== functions for server client relationship ===== #

  async def read_body(self, receive):
    """Read and return the entire body from an incoming ASGI message."""
    body = b''
    more_body = True

    while more_body:
      message = await receive()
      body += message.get('body', b'')
      more_body = message.get('more_body', False)

    return body

  async def send_response(self, send, body, status = 200, json = False):
    """Send a response."""
    await send({
      "type": "http.response.start",
      "status": status,
      "headers": [
        (b"Content-Type", b"text/html" if not json else b"application/json"),
      ],
    })

    # try-catch is faster than hasattr or isinstance
    try:
      body = body.encode()
    except:
      try:
        body = jdumps(body).encode()
      except:
        pass
 
    # send the body
    await send({
      "type": "http.response.body",
      "body": body,
    })

  async def __call__(self, scope, receive, send):
    """Handle an incoming request."""
    # print(scope, receive, send)
    assert scope['type'] == 'http'

    if scope["path"] == "/":
      await self.send_response(send, page)
    elif scope["path"] == "/ping":
      await self.send_response(send, str(int(round(time.time() * 1000))))
    elif scope["path"] == "/register":
      body = await self.read_body(receive)
      body, err  = self._register(body)
      if err:
        await self.send_response(send, err, 500)
      else:
        await self.send_response(send, body, 200)
    elif scope["path"] == "/log":
      out = await self.read_body(receive)
      out, err = self._log(out)
      if err:
        await self.send_response(send, err, 500)
      else:
        await self.send_response(send, b"OK")
    elif scope["path"] == "/get":
      out = await self.read_body(receive)
      out, err = self._get(out)
      if err:
        await self.send_response(send, err, 500)
      else:
        await self.send_response(send, out, 200)
    else:
      await self.send_response(send, b"404 Not Found", 404)

# this is what gets called by uvicorn
app = JatakaServer()

#!/usr/bin/env python3

# as if its deployed

import os
import sys
import random
from time import sleep
from common import get_job_id, log

PID = os.getpid()
JOB_ID = get_job_id()

print("> Starting job 2 (text class. depl.):", PID)

log_every = 1
salt = 4
step_id = 0
all_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " * 100

step_id = 0
while 1:
  # log deployment metrics
  sleep(log_every + random.randint(1, salt))
  p_value = random.random() * 0.5
  high_p_value_strings = "".join(random.sample(all_chars, random.randint(60, 128)))
  high_p_value_pred = random.randint(1, 100)
  print(f"> [{JOB_ID}] p_value: {p_value}, high_p_value_strings: {high_p_value_strings}, high_p_value_pred: {high_p_value_pred}")

  log({
    "job_id": JOB_ID,
    "input_string": high_p_value_strings,
    "model_prediction": high_p_value_pred
  })

  if step_id == random.randint(1, 100):
    sys.exit(0)

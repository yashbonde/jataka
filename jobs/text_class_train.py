#!/usr/bin/env python3

import os
import sys
import random
from time import sleep
from common import get_job_id, log

PID = os.getpid()
JOB_ID = get_job_id()

print("> Starting job 1 (text class. train):", PID)

log_every_train = 2
log_every_test = 3
salt = 2
step_id = 0
all_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " * 100

while 1:
  # log training metrics after sleeping
  sleep(log_every_train + random.random() * salt)
  train_loss = (1 + random.random()) * 5
  print(f"> [{JOB_ID}] [{PID}] train loss: {train_loss}")

  log({
    "job_id": JOB_ID,
    "train_loss": train_loss,
  })

  # log test metrics after sleeping
  sleep(log_every_test + random.random() * salt)
  test_loss = (1 + random.random()) * 6
  high_test_loss_strings = ["".join(random.sample(all_chars, random.randint(60, 128))) for _ in range(2)]
  high_test_loss_pred = [random.randint(1, 100) for _ in range(2)]
  high_test_loss_labels = [random.randint(1, 100) for _ in range(2)]
  high_test_loss = [(1 + random.random()) * 10 for _ in range(2)]
  print(f"> [{JOB_ID}] [{PID}] test loss: {test_loss}")

  log({
    "job_id": JOB_ID,
    "test_loss": test_loss,
    "high_test_loss_strings": high_test_loss_strings,
    "high_test_loss_pred": high_test_loss_pred,
    "high_test_loss_labels": high_test_loss_labels,
    "high_test_loss": high_test_loss,
  })

  if step_id == random.randint(1, 100):
    sys.exit(0)

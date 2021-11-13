#!/usr/bin/env python3

import os
import sys
import random
import base64
import numpy as np
from PIL import Image
from time import sleep
from common import get_job_id, log

PID = os.getpid()
JOB_ID = get_job_id()


print("> Starting job 0 (image class. train):", )

log_every_train = 6
log_every_test = 5
salt = 4
step_id = 0

while 1:
  # log training metrics after sleeping
  sleep(log_every_train + random.randint(0, salt))
  train_loss = (1 + random.random()) * 5
  print(f"> [{JOB_ID}] [{PID}] train loss: {train_loss}")
  
  log({"job_id": JOB_ID, "train_loss": train_loss})

  # log test metrics after sleeping
  sleep(log_every_test + random.randint(0, salt))
  test_loss = (1 + random.random()) * 6
  high_test_loss_images = [Image.fromarray(x) for x in np.random.randint(0, 256, size=(2, 10, 10, 3))]
  high_test_loss_pred = [random.randint(1, 100) for _ in range(2)]
  high_test_loss_labels = [random.randint(1, 100) for _ in range(2)]
  high_test_loss = [(1 + random.random()) * 10 for _ in range(2)]
  print(f"> [{JOB_ID}] [{PID}] test loss: {test_loss}")

  # images in high_test_loss_images needs to be encoded as base64
  images_to_send = [base64.b64encode(image.tobytes()).decode('utf-8') for image in high_test_loss_images]

  log({
    "job_id": JOB_ID,
    "test_loss": test_loss,
    "high_test_loss_images": images_to_send,
    "high_test_loss": high_test_loss,
    "high_test_loss_pred": high_test_loss_pred,
    "high_test_loss_labels": high_test_loss_labels,
  })

  if step_id == random.randint(1, 100):
    sys.exit(0)
  

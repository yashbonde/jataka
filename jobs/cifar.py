#!/usr/bin/env python3
import os
import json
import torch
import random
from uuid import uuid1
from tqdm.auto import trange
from tempfile import gettempdir
from torchvision import datasets

from gperc import BinaryConfig, Perceiver, ArrowConsumer, Trainer
from common import JatakaClient

ds_train = datasets.CIFAR10(gettempdir(), download = True, train = True)
ds_test = datasets.CIFAR10(gettempdir(), download = True, train = False)

# create labels
labels = [ "airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
class_to_id = {x:i for i,x in enumerate(labels)}

# create a target dir
target_dir = os.path.join(gettempdir(), "cifar10-ByTe-train")
if not os.path.exists(target_dir):
  os.makedirs(target_dir, exist_ok=True)

  # first create the training dataset
  print("Creating dataset")
  truth = {}
  for _, (x, l) in zip(trange(len(ds_train)), ds_train):
    fp = os.path.join(target_dir, str(uuid1()) + random.choice([".png", ".jpg", ".tif"]))
    truth[fp] = labels[l]
    x.save(fp)
    
  with open(os.path.join(target_dir, "truth.json"), "w") as f:
    f.write(json.dumps(truth))

  # now create the test dataset
  truth_test = {}
  for _, (x, l) in zip(trange(len(ds_test)), ds_test):
    fp = os.path.join(target_dir, str(uuid1()) + random.choice([".png", ".jpg", ".tif"]))
    truth_test[fp] = labels[l]
    x.save(fp)

  with open(os.path.join(target_dir, "truth_test.json"), "w") as f:
    f.write(json.dumps(truth_test))

else:
  print("Loading pre-prepared dataset")
  with open(os.path.join(target_dir, "truth.json"), "r") as f:
    truth = json.load(f)

  with open(os.path.join(target_dir, "truth_test.json"), "r") as f:
    truth_test = json.load(f)

# create a small subset of the actual dataset
class_to_files = {}
for x in truth:
  class_to_files.setdefault(truth[x], []).append(x)

class_to_files_test = {}
for x in truth_test:
  class_to_files_test.setdefault(truth_test[x], []).append(x)

train_ = {k:v[:10] for k,v in class_to_files.items()}
test_ = {k:v[:1] for k,v in class_to_files_test.items()}

data = ArrowConsumer(train_, n_bytes=1, class_to_id=class_to_id)
data_test = ArrowConsumer(test_, n_bytes=1, class_to_id=class_to_id)
data.create_batches(58)
data_test.create_batches(128)
print(data)
print(data_test)

# create the model
device = "cpu" if not torch.cuda.is_available() else "cuda:0"
config = BinaryConfig(
  seqlen = data.seqlen,
  vocab_size = data.vocab_size,
  latent_dim = 8,
  latent_frac = 0.001,
  n_classes = len(class_to_id),
  ffw_ratio=1.0,
  num_heads = 2,
  num_layers = 1,
  decoder_reduction = "mean"
)
model = Perceiver(config).to(device)
print("number of parameters:", model.num_parameters())

client = JatakaClient("http://localhost:8000", None, config.get_dict(),)
print("client:", client)

trainer = Trainer(model, client)
trainer.train(
  optim = torch.optim.Adam(model.parameters(), 0.001),
  train_data = data,
  n_steps = 10000,
  test_every = 1000,
  test_data = data_test,
)

#!/bin/bash

cardano-node run \
  --config /code/configs/config.json \
  --topology /code/configs/topology.json \
  --database-path /data/db --socket-path /ipc/node.socket
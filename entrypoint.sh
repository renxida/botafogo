#!/bin/bash
eval "$(micromamba shell hook --shell bash)"
micromamba activate /root/micromamba
exec python /root/app.py --port 15781

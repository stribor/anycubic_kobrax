#!/usr/bin/env bash

rsync -avr \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  custom_components/anycubic_kobrax/ \
  has:HomeAssistant/custom_components/anycubic_kobrax/


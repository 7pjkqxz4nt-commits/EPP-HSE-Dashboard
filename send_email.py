name: Daily HSE Report

on:
  schedule:
    - cron: "0 4 * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - run: pip install pandas reportlab openpyxl

      - run: python send_email.py

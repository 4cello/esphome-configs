#! /usr/bin/env python3

import subprocess
import os
import sys

import argparse

from InquirerPy import prompt
from InquirerPy.separator import Separator

from prompt_toolkit import HTML, print_formatted_text
from prompt_toolkit.styles import Style

PROMPT_STYLE = {
    "separator": '#6C6C6C',
    "questionmark": '#FF9D00 bold',
    "selected": '#5F819D',
    "pointer": '#FF9D00 bold',
    "instruction": '',  # default
    "answer": '#5F819D bold',
    #"question": '',
}

IDS_WITHOUT_DISPLAY = [
  "79a6"
]

IDS_WITH_DISPLAY = [
  "4e78",
  "b34a"
]

ACTIONS = [
  "run",
  "logs",
  "compile",
  "upload"
]

class IDAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    if values not in IDS_WITHOUT_DISPLAY and values not in IDS_WITH_DISPLAY:
      parser.error(f"Unknown id: {values}")
    setattr(namespace, self.dest, values)


class ActionAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    if values not in ACTIONS:
      parser.error(f"Unknown action: {values}")
    setattr(namespace, self.dest, values)

def dialog(given = {}):
  config_choices = [Separator(line="With display:")] + IDS_WITH_DISPLAY + [Separator(line="Without Display:")] + IDS_WITHOUT_DISPLAY

  q_conf = {
      "type": "list",
      "name": "id",
      "message": "Which configuration should be selected?",
      "choices": config_choices
    }
  q_action = {
      "type": "list",
      "name": "action",
      "message": "Which action should be performed?",
      "choices": ACTIONS
    }

  questions = []
  if not "id" in given:
    questions.append(q_conf)
  else:
    print_formatted_text(HTML(f"? <question>{q_conf['message']}</question> <answer>{given['id']}</answer>"), style=Style.from_dict(PROMPT_STYLE))
  
  if not "action" in given:
    questions.append(q_action)
  else:
    print_formatted_text(HTML(f"? {q_action['message']} <answer>{given['action']}</answer>"), style=Style.from_dict(PROMPT_STYLE))

  answers = prompt(questions, style=PROMPT_STYLE)
  return dict(given, **answers)


def main():
  parser = argparse.ArgumentParser(description="ESPHome notification light runner")
  parser.add_argument("-i", "--id", action=IDAction)
  parser.add_argument("-a", "--action", action=ActionAction)
  args = parser.parse_args()
  given = {k:v for k,v in vars(args).items() if v is not None}

  answers = dialog(given)
  yaml = "notification_light.yaml" if answers["id"] in IDS_WITHOUT_DISPLAY else "notification_light_with_display.yaml"
  os.chdir(os.path.join(os.path.abspath(sys.path[0]), "../NotificationEgg"))
  cmd = [
    "esphome",
    "-s", "id_code", answers["id"],
    answers['action'],
    yaml
  ]
  print(cmd)
  subprocess.run(cmd, shell=True)


if __name__ == "__main__":
  main()
#!/bin/zsh
set -eu
PACKAGE_PATH="${0:A:h}"
if ! python3 "$PACKAGE_PATH/patch_asar.py" launch; then
  print '\n中文启动失败，请查看上面的提示。按回车关闭。'
  read -r
  exit 1
fi

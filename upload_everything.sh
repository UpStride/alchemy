#!/bin/bash
# Finds all the tensorboard folders that follow the given pattern (don't forget the commas !)
# and then upload them to alchemy with a corresponding report.yaml file
# Usage : bash upload_everything "*" my_password
find . -type d -wholename "$1" -exec sh -c 'alchemy_cli "$1" --yaml_file "$1/report_corrected.yaml" --password "$2" -y' sh {} $2 ';'

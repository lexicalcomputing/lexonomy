#!/usr/bin/python3
import sys, os, glob
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ops

script_dir = os.path.dirname(os.path.realpath(__file__))

import argparse
parser = argparse.ArgumentParser(description='Upload NVH data as a dictionary with a widget using makeDict')
parser.add_argument('filename', type=str, help='dictionary NVH file')
parser.add_argument('creator', type=str, help='uploader email')
parser.add_argument('title', type=str, help='dictionary title')
parser.add_argument('dict_id', type=str, help='dictionary ID')
parser.add_argument('lang', type=str, help='language')
parser.add_argument('widget_dir', type=str, help='widget directory')
args = parser.parse_args()

widget_hash = os.popen(f'git -C "{args.widget_dir}" rev-parse --short=8 HEAD').read().strip()
print(f'Using widget from commit ID: {widget_hash}')

if os.path.exists(f'{args.widget_dir}/public'):
  print('Syncing widget\'s public files...')
  # widget path is of the type [...]/[customization]/[widget]/
  widget = os.path.basename(os.path.realpath(args.widget_dir))
  customization = os.path.basename(os.path.dirname(os.path.realpath(args.widget_dir)))
  os.system(f'rsync -r --mkpath "{args.widget_dir}/public/" "{script_dir}/../customization/{customization}/{widget}/"')
  print('Done.')
else:
  print('Widget has no public files. Nothing to sync.')

def merge_files(files, include_header = True, header_note = '', separator = None):
  data = ''
  for fname in files:
    if include_header: data += '/* ' + os.path.basename(fname) + (' ' + header_note if header_note else '') + ' */\n\n'
    with open(fname) as file:
      data += file.read().strip().rstrip(separator) + (separator or '') + '\n\n'
  return data.rstrip().rstrip(separator)

input_files = {}

data = '{\n' + merge_files(sorted(glob.glob(f'{args.widget_dir}/custom_editor_js_*.js')), header_note=widget_hash, separator=',') + '\n}'
if data: input_files['custom_editor.js'] = BytesIO(data.encode('utf-8'))

data = merge_files(sorted(glob.glob(f'{args.widget_dir}/custom_editor_css_*.css')), header_note=widget_hash)
if data: input_files['custom_editor.css'] = BytesIO(data.encode('utf-8'))

data = merge_files(sorted(glob.glob(f'{args.widget_dir}/styles_*.css')), header_note=widget_hash)
if data: input_files['styles.css'] = BytesIO(data.encode('utf-8'))

try:
  input_files['structure.nvh'] = open(f'{args.widget_dir}/structure.nvh', 'rb')
except FileNotFoundError:
  pass

try:
  input_files['configs.json'] = open(f'{args.widget_dir}/configs.json', 'rb')
except FileNotFoundError:
  pass

if args.filename: input_files['entries.nvh'] = open(args.filename, 'rb')

res = ops.makeDict(args.dict_id, None, args.title, args.lang, '', args.creator, input_files=input_files)
if not res['success']:
  print(f'Error: {res}')
  sys.exit(1)
print(f'Upload processed in: {res["upload_file_path"]}')
print(res['upload_message'])
print('Log:')
logfile = open(f'{res["upload_file_path"]}/import_progress.log', 'r')
while True:
  logline = logfile.readline()
  if logline:
    print(logline, end='')
    if logline.startswith('END'):
      break
print('Done.')

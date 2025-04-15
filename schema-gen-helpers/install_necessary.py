import collections
import json
import os
import shutil
import sys

import util.topological_sort as uts

def order_dict(d, order):
  return collections.OrderedDict([
    (k, d[k])
    for k in (order + [j for j in d if j not in order])
    if k in d
  ])

def main(src_dir, dest_dir, interactive=False, *, baseline_necessary_module_names=['server', '!GlobalTypes']):
  baseline_necessary_fnames = [f'{module_name}.json' for module_name in baseline_necessary_module_names]
  baseline_necessary_fnames_set = set(baseline_necessary_fnames)
  if len(baseline_necessary_fnames) != len(baseline_necessary_fnames_set):
    print(f"Error baseline_necessary_fnames")
    sys.exit(1)
  src_json_fnames = []
  for item in os.listdir(src_dir):
    if os.path.isfile(os.path.join(src_dir, item)) and item.endswith('.json'):
      src_json_fnames.append(item)

  residual_postprocessed_files = [fname for fname in src_json_fnames if fname.endswith('_postprocessed.json')]
  if residual_postprocessed_files:
    print(f"Residual postprocessing files found:")
    print(f"{os.path.join(src_dir, "x")}")
    print(f"x = {residual_postprocessed_files}")
    
    if not interactive:
      print(f"Won't postprocess with residual files present.")
      sys.exit(1)

    print(f"Delete? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
    print("Deleting...")
    for fname in residual_postprocessed_files:
      os.remove(os.path.join(src_dir, fname))
    print("Deleted")

    src_json_fnames = []
    for item in os.listdir(src_dir):
      if os.path.isfile(os.path.join(src_dir, item)) and item.endswith('.json'):
        src_json_fnames.append(item)
    residual_postprocessed_files = [fname for fname in src_json_fnames if fname.endswith('_postprocessed.json')]
    if residual_postprocessed_files:
      print("Error residula_postprocessed_files")
      sys.exit(1)

  dest_json_fnames = []
  for item in os.listdir(dest_dir):
    if not (os.path.isfile(os.path.join(dest_dir, item)) and item.endswith('.json')):
      print(f"Unexpected item in destination directory: {os.path.join(dest_dir, item)}")
      sys.exit(1)
    dest_json_fnames.append(item)

  src_set = set([fname.lower() for fname in src_json_fnames])
  dest_set = set([fname.lower() for fname in dest_json_fnames])
  for fname in baseline_necessary_fnames:
    if fname.lower() not in src_set:
      print(f"Baseline necessary module not present: {os.path.join(src_dir, fname)}")
      sys.exit(1)
    if fname.lower() not in dest_set:
      print(f"Baseline necessary module not present: {os.path.join(dest_dir, fname)}")
      sys.exit(1)

  print("Configuring install...")

  dest_enums = set()
  dest_classes = set()
  for fname in dest_json_fnames:
    with open(os.path.join(dest_dir, fname), 'r') as f:
      module = json.load(f)
    dest_enums.update(module['enums'].keys())
    dest_classes.update(module['classes'].keys())

  i = 0
  src_json_fnames = (
    baseline_necessary_fnames
    + [fname for fname in src_json_fnames if fname.lower() not in baseline_necessary_fnames_set and fname.lower() in dest_set]
    + [fname for fname in src_json_fnames if fname.lower() not in baseline_necessary_fnames_set and fname.lower() not in dest_set]
  )
  while i < len(src_json_fnames):
    with open(os.path.join(src_dir, src_json_fnames[i]), 'r') as f:
      module = json.load(f)

    install_module = False

    for ek in set(dest_enums):
      if ek in module['enums']:
        install_module = True
        dest_enums.remove(ek)
    
    for ck in set(dest_classes):
      if ck in module['classes']:
        install_module = True
        dest_classes.remove(ck)
    
    if install_module:
      i += 1
    else:
      src_json_fnames.pop(i)
  src_set = set([fname.lower() for fname in src_json_fnames])

  for fname in baseline_necessary_fnames:
    if fname.lower() not in src_set:
      src_json_fnames.append(fname)
      src_set.add(fname.lower())

  overwrite_list = [fname for fname in src_json_fnames if fname.lower() in dest_set]
  new_list = [fname for fname in src_json_fnames if fname.lower() not in dest_set]
  remove_list = [fname for fname in dest_json_fnames if fname.lower() not in src_set]

  if interactive:
    if overwrite_list:
      print(f"Will overwrite the following files:")
      print(f"Source: {os.path.join(src_dir, "x")}")
      print(f"Dest:   {os.path.join(dest_dir, "x")}")
      print(f"x = {overwrite_list}")
    if new_list:
      print(f"Will add the following new files:")
      print(f"Source: {os.path.join(src_dir, "x")}")
      print(f"Dest:   {os.path.join(dest_dir, "x")}")
      print(f"x = {new_list}")
    if remove_list:
      print(f"Will remove the following files:")
      print(f"{os.path.join(dest_dir, "x")}")
      print(f"x = {remove_list}")
    print(f"Ok? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
    
  print("Installing...")

  for fname in overwrite_list + new_list:
    shutil.copy(
      os.path.join(src_dir, fname),
      os.path.join(dest_dir, fname)
    )
  
  for fname in remove_list:
    os.remove(dest_dir, fname)

  print("Done")

if __name__ == '__main__':
  if not (
    len(sys.argv) == 3
    or (len(sys.argv) == 4 and sys.argv[3] == '--non-interactive')
  ):
    print(f"Usage: {sys.argv[0] if len(sys.argv) > 0 else 'program'} <path_to_schema_dir_src> <path_to_schema_dir_dest> [--non-interactive]")
    sys.exit(1)

  main(sys.argv[1], sys.argv[2], interactive=(len(sys.argv) == 3))
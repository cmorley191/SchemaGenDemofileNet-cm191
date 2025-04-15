import collections
import json
import os
import re
import shutil
import sys

def order_dict(d, order):
  return collections.OrderedDict([
    (k, d[k])
    for k in (order + [j for j in d if j not in order])
    if k in d
  ])

def main(schema_dir, interactive=False):
  schema_json_fnames = []
  for item in os.listdir(schema_dir):
    if os.path.isfile(os.path.join(schema_dir, item)) and item.endswith('.json'):
      schema_json_fnames.append(item)

  residual_postprocessed_files = [fname for fname in schema_json_fnames if fname.endswith('_postprocessed.json')]
  if residual_postprocessed_files:
    print(f"Residual postprocessing files found:")
    print(f"{os.path.join(schema_dir, "x")}")
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
      os.remove(os.path.join(schema_dir, fname))
    print("Deleted")

    schema_json_fnames = []
    for item in os.listdir(schema_dir):
      if os.path.isfile(os.path.join(schema_dir, item)) and item.endswith('.json'):
        schema_json_fnames.append(item)
    residual_postprocessed_files = [fname for fname in schema_json_fnames if fname.endswith('_postprocessed.json')]
    if residual_postprocessed_files:
      print("Error residula_postprocessed_files")
      sys.exit(1)

  if interactive:
    print(f"Will post-process the following files in-place:")
    print(f"{os.path.join(schema_dir, "x")}")
    print(f"x = {schema_json_fnames}")
    print(f"Ok? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
  
  print("Post-processing...")

  for fname in schema_json_fnames:
    print(fname)

    with open(os.path.join(schema_dir, fname), 'r') as f:
      module = json.load(f)

    for ck in module['classes']:
      c = module['classes'][ck]
      for f in c['fields']:
        t = f['type']
        while True:
          if t['category'] == 4 and (t['atomic'] == 1 or t['atomic'] == 2):
            assert 'inner' in t
            assert t['name'].endswith(f'< {t["inner"]["name"]} >')
            if 'outer' not in t:
              outer = t['name'][:-len(f'< {t["inner"]["name"]} >')]
              assert len(outer) == len(outer.strip())
              assert '<' not in outer and '>' not in outer
              t['outer'] = outer

          if 'inner' in t:
            t = t['inner']
          else:
            break

      field_order = ['name', 'category', 'arraySize', 'atomic', 'outer', 'inner']
      for f in c['fields']:
        t = f['type']
        tree = [t]
        while 'inner' in tree[-1]:
          tree.append(tree[-1]['inner'])
        for j in range(len(tree)):
          j = len(tree) - j - 1
          if j == 0:
            f['type'] = order_dict(tree[j], field_order)
          else:
            tree[j-1]['inner'] = order_dict(tree[j], field_order)

    dump = json.dumps(module, indent=2)
    for i in range(3):
      dump = re.sub(r'(\n\s+)("[^"]+": \[)(\],?\n)', r'\1\2\1\3', dump)
    with open(os.path.join(schema_dir, f"{fname}_postprocessed.json"), 'w') as f:
      f.write(dump)

  print(f"Saving...")
  for fname in schema_json_fnames:
    shutil.copy(
      os.path.join(schema_dir, f"{fname}_postprocessed.json"),
      os.path.join(schema_dir, fname)
    )
  
  print(f"Cleaning up...")
  for fname in schema_json_fnames:
    os.remove(os.path.join(schema_dir, f"{fname}_postprocessed.json"))

  print(f"Done")

if __name__ == '__main__':
  if not (
    len(sys.argv) == 2
    or (len(sys.argv) == 3 and sys.argv[2] == '--non-interactive')
  ):
    print(f"Usage: {sys.argv[0] if len(sys.argv) > 0 else 'program'} <path_to_schema_dir_to_postprocess> [--non-interactive]")
    sys.exit(1)

  main(sys.argv[1], interactive=(len(sys.argv) == 2))
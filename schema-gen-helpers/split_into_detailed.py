import collections
import json
import os
import re
import shutil
import sys

import util.topological_sort as uts

def order_dict(d, order):
  return collections.OrderedDict([
    (k, d[k])
    for k in (order + [j for j in d if j not in order])
    if k in d
  ])

def main(schema_dir, output_dir, interactive=False):
  schema_json_fnames = []
  for item in os.listdir(schema_dir):
    if os.path.isfile(os.path.join(schema_dir, item)) and item.endswith('.json'):
      schema_json_fnames.append(item)

  if not os.path.isdir(output_dir):
    print(f"Output dir does not exist: {output_dir}")
    sys.exit(1)

  output_items = os.listdir(output_dir)
  if output_items:
    print(f"Output directory is populated:")
    print(f"{os.path.join(schema_dir, "x")}")
    print(f"x = <{len(output_items)} items>")

    if not interactive:
      print(f"Won't output here with items already present.")
      sys.exit(1)

    print(f"Clear directory? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
    print("Clearing...")
    for item in output_items:
      os.remove(os.path.join(output_dir, fname))
    print("Clear")

    output_items = os.listdir(output_dir)
    if output_items:
      print("Error output_items")
      sys.exit(1)

  if interactive:
    print(f"Will split the following files into directories:")
    print(f"Source: {os.path.join(schema_dir, "x")}")
    print(f"x = {schema_json_fnames}")
    print(f"Dest:   {os.path.join(output_dir, "y")}")
    print(f"y = {[fname[:-len('.json')] for fname in schema_json_fnames]}")
    print(f"Ok? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
  
  print("Splitting...")

  for fname in schema_json_fnames:
    print(fname)

    module_path = os.path.join(output_dir, fname[:-len('.json')])
    os.mkdir(module_path)
    os.mkdir(os.path.join(module_path, 'enums'))
    os.mkdir(os.path.join(module_path, 'classes'))

    with open(os.path.join(schema_dir, fname), 'r') as f:
      module = json.load(f)

    assert len(set([ek.replace(':', '_') for ek in module['enums']])) == len(module['enums'])
    assert len(set([ck.replace(':', '_') for ck in module['classes']])) == len(module['classes'])

    for ek in module['enums']:
      with open(os.path.join(module_path, 'enums', f'{ek.replace(':', '_')}.json'), 'w') as f:
        e = module['enums'][ek]
        #for _ in range(1): # just a scope we can break out of
        #  if len(e['items']) < 4:
        #    break
        #
        #  for non_consecutive_pad in range(min(5, len(e['items']) - 3)):
        #    for start_pad in range(non_consecutive_pad+1):
        #      interval = e['items'][1+start_pad]['value'] - e['items'][start_pad]['value']
        #      if (not [i for i in range(len(e['items']) - 1 - non_consecutive_pad) if e['items'][i+1+start_pad]['value'] - e['items'][i+start_pad]['value'] != interval]):
        #        non_consecutive_items = e['items'][:start_pad]
        #        if start_pad < non_consecutive_pad:
        #          non_consecutive_items += e['items'][-(non_consecutive_pad - start_pad):]
        #        original_items = module['enums'][ek]['items']
        #        module['enums'][ek]['items'] = collections.OrderedDict([
        #          ("consecutive_items", collections.OrderedDict([
        #            ("run_start_index", start_pad),
        #            ("start_value", e['items'][start_pad]['value']),
        #            ("interval", interval),
        #            ("item_names", [i['name'] for i in e['items'][start_pad:len(e['items'])-non_consecutive_pad+start_pad]])
        #          ])),
        #          ("items", non_consecutive_items)
        #        ])
        #        # validation
        #        reconstructed_items = []
        #        reconstructed_items += module['enums'][ek]['items']['items'][:module['enums'][ek]['items']['consecutive_items']['run_start_index']]
        #        reconstructed_items += [{
        #          "value": module['enums'][ek]['items']['consecutive_items']['start_value'] + (i*module['enums'][ek]['items']['consecutive_items']['interval']),
        #          "name": module['enums'][ek]['items']['consecutive_items']['item_names'][i]
        #        } for i in range(len(module['enums'][ek]['items']['consecutive_items']['item_names']))]
        #        reconstructed_items += module['enums'][ek]['items']['items'][module['enums'][ek]['items']['consecutive_items']['run_start_index']:]
        #        assert original_items == reconstructed_items, f"Reconstruction error.\n\nOriginal: {original_items}\n\nReconstructed: {reconstructed_items}\n\n{non_consecutive_pad},{start_pad}"
        #        break
        #    else:
        #      continue
        #    break
        #  else:
        #    continue
        #  break
        #else:
        #  for _ in range(1): # just a scope we can break out of
        #    if len(e['items']) < 4:
        #      break
        #
        #    for non_powers_pad in range(min(5, len(e['items']) - 3)):
        #      for start_pad in range(non_powers_pad+1):
        #        if (not [i for i in range(len(e['items']) - 1 - non_powers_pad) if e['items'][i+start_pad]['value'] <= 0 or e['items'][i+1+start_pad]['value'] / e['items'][i+start_pad]['value'] != 2.0]):
        #          non_powers_items = e['items'][:start_pad]
        #          if start_pad < non_powers_pad:
        #            non_powers_items += e['items'][-(non_powers_pad - start_pad):]
        #          original_items = module['enums'][ek]['items']
        #          module['enums'][ek]['items'] = collections.OrderedDict([
        #            ("powers_of_two_items", collections.OrderedDict([
        #              ("run_start_index", start_pad),
        #              ("start_value", e['items'][start_pad]['value']),
        #              ("item_names", [i['name'] for i in e['items'][start_pad:len(e['items'])-non_powers_pad+start_pad]])
        #            ])),
        #            ("items", non_powers_items)
        #          ])
        #          # validation
        #          reconstructed_items = []
        #          reconstructed_items += module['enums'][ek]['items']['items'][:module['enums'][ek]['items']['powers_of_two_items']['run_start_index']]
        #          reconstructed_items += [{
        #            "value": module['enums'][ek]['items']['powers_of_two_items']['start_value'] * (2 ** i),
        #            "name": module['enums'][ek]['items']['powers_of_two_items']['item_names'][i]
        #          } for i in range(len(module['enums'][ek]['items']['powers_of_two_items']['item_names']))]
        #          reconstructed_items += module['enums'][ek]['items']['items'][module['enums'][ek]['items']['powers_of_two_items']['run_start_index']:]
        #          assert original_items == reconstructed_items, f"Reconstruction error.\n\nOriginal: {original_items}\n\nReconstructed: {reconstructed_items}\n\n{non_powers_pad},{start_pad}"
        #          break
        #      else:
        #        continue
        #      break
        #    else:
        #      continue
        #    break
        #  else:
        #    module['enums'][ek]['items'] = { "items": e['items'] }
        module['enums'][ek]['items'] = collections.OrderedDict([
          ("names", [i['name'] for i in module['enums'][ek]['items']]),
          ("values", [i['value'] for i in module['enums'][ek]['items']]),
        ])
        
        json.dump(module['enums'][ek], f, indent=2)

    for ck in module['classes']:
      with open(os.path.join(module_path, 'classes', f'{ck.replace(':', '_')}.json'), 'w') as f:
        json.dump(module['classes'][ck], f, indent=2)

    with open(os.path.join(module_path, 'enums.json'), 'w') as f:
      json.dump(list(module['enums']), f, indent=2)
    
    with open(os.path.join(module_path, 'classes.json'), 'w') as f:
      json.dump(list(module['classes']), f, indent=2)

  print(f"Done")

if __name__ == '__main__':
  if not (
    len(sys.argv) == 3
    or (len(sys.argv) == 4 and sys.argv[3] == '--non-interactive')
  ):
    print(f"Usage: {sys.argv[0] if len(sys.argv) > 0 else 'program'} <path_to_schema_dir_to_split> <path_to_output_split_dir> [--non-interactive]")
    sys.exit(1)

  main(sys.argv[1], sys.argv[2], interactive=(len(sys.argv) == 3))
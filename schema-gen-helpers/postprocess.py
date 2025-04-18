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

def main(sdk_dir, reference_dir=None, interactive=False):
  sdk_json_fnames = []
  for item in os.listdir(sdk_dir):
    if os.path.isfile(os.path.join(sdk_dir, item)) and item.endswith('.json'):
      sdk_json_fnames.append(item)

  if reference_dir is not None:
    reference_json_fnames = []
    for item in os.listdir(reference_dir):
      if os.path.isfile(os.path.join(reference_dir, item)) and item.endswith('.json'):
        reference_json_fnames.append(item)

  residual_postprocessed_files = [fname for fname in sdk_json_fnames if fname.endswith('_postprocessed.json')]
  if residual_postprocessed_files:
    print(f"Residual postprocessing files found:")
    print(f"{os.path.join(sdk_dir, "x")}")
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
      os.remove(os.path.join(sdk_dir, fname))
    print("Deleted")

    sdk_json_fnames = []
    for item in os.listdir(sdk_dir):
      if os.path.isfile(os.path.join(sdk_dir, item)) and item.endswith('.json'):
        sdk_json_fnames.append(item)
    residual_postprocessed_files = [fname for fname in sdk_json_fnames if fname.endswith('_postprocessed.json')]
    if residual_postprocessed_files:
      print("Error residula_postprocessed_files")
      sys.exit(1)

  sdk_json_fnames_set = set([fname.lower() for fname in sdk_json_fnames])

  if reference_dir is not None:
    reference_json_fnames = [fname for fname in reference_json_fnames if fname.lower() in sdk_json_fnames_set]
    reference_json_fnames_set = set([fname.lower() for fname in reference_json_fnames])

  if interactive:
    print(f"Will post-process the following files in-place:")
    print(f"{os.path.join(sdk_dir, "x")}")
    print(f"x = {sdk_json_fnames}")
    if reference_dir is not None:
      print(f"...using the following files for key ordering (though dependency ordering will take precedence):")
      print(f"{os.path.join(reference_dir, "x")}")
      print(f"x = {reference_json_fnames}")
    print(f"Ok? (y/n)")
    i = input()
    if i.strip().lower() not in ['y', 'yes']:
      print("Did not receive 'yes'")
      sys.exit(1)
  
  print("Post-processing...")

  for fname in sdk_json_fnames:
    print(fname)

    with open(os.path.join(sdk_dir, fname), 'r') as f:
      lines = f.readlines()

    outlines = []
    for i in range(1, len(lines)):
      prev_line_spaces = len(lines[i-1]) - len(lines[i-1].lstrip())
      assert not [c for c in lines[i-1][:prev_line_spaces] if c != ' ']
      this_line_spaces = len(lines[i]) - len(lines[i].lstrip())
      assert not [c for c in lines[i][:this_line_spaces] if c != ' ']
      assert ((this_line_spaces - prev_line_spaces) % 4) == 0
      tab_diff = (this_line_spaces - prev_line_spaces) // 4
      assert tab_diff >= -1 and tab_diff <= 1
      if tab_diff == -1:
        assert lines[i-1][-2:] == ',\n'
        outlines.append(lines[i-1][:-2] + '\n')
      else:
        outlines.append(lines[i-1])
    outlines.append(lines[-1])

    del lines
    module = json.loads(''.join(outlines))
    del outlines

    class_usages = { ck: set() for ck in module['classes'] }

    for ck in module['classes']:
      c = module['classes'][ck]
      if 'parent' in c and c['parent'] in module['classes']:
        assert c['parent'] != ck, ck
        class_usages[c['parent']].add(ck)
      for f in c['fields']:
        t = f['type']
        while True:
          if t['category'] == 4 and (t['atomic'] == 1 or t['atomic'] == 2):
            assert 'inner' in t
            assert 'outer' not in t
            assert t['name'].endswith(f'< {t["inner"]["name"]} >')
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
        if t['category'] == 5 and t['name'] in module['classes']:
          if t['name'] != ck:
            class_usages[t['name']].add(ck)
        while 'inner' in tree[-1]:
          tree.append(tree[-1]['inner'])
          if tree[-1]['category'] == 5 and tree[-1]['name'] in module['classes']:
            if tree[-1]['name'] != ck:
              class_usages[tree[-1]['name']].add(ck)
        for j in range(len(tree)):
          j = len(tree) - j - 1
          if j == 0:
            f['type'] = order_dict(tree[j], field_order)
          else:
            tree[j-1]['inner'] = order_dict(tree[j], field_order)

      remove_metadata = set([
        'MVDataNodeType', 'MVDataOverlayType',
        'MParticleReplacementOp',
        'MPropertyCustomEditor',
        'MCellForDomain',
        'MPulseCellOutflowHookInfo', 'MPulseEditorHeaderIcon', 'MPulseProvideFeatureTag'
      ])
      for i in range(len(c['metadata'])):
        if 'value' in c['metadata'][i] and c['metadata'][i]['name'] in remove_metadata:
          del c['metadata'][i]['value']
        c['metadata'][i] = order_dict(c['metadata'][i], ['name', 'value'])

      module['classes'][ck] = order_dict(c, ['parent', 'metadata', 'fields'])
    
    # priority 3 sort: original output ordering
    class_tie_ordering = list(module['classes'].keys())
  
    # priority 2 sort: compare file's ordering
    if reference_dir is not None and fname.lower() in reference_json_fnames_set:
      with open(os.path.join(reference_dir, [fname2 for fname2 in reference_json_fnames if fname2.lower() == fname.lower()][0]), 'r') as f:
        # note: this load is used later in a similar if-statement below
        reference_module = json.load(f)
      reference_module_class_ordering = list(reference_module['classes'])
      reference_module_class_ordering = { reference_module_class_ordering[i]: i for i in range(len(reference_module_class_ordering)) }
      class_tie_ordering.sort(key=lambda ck: reference_module_class_ordering[ck] if ck in reference_module_class_ordering else float('inf'))

    # priority 1 sort: dependency order
    module['classes'] = order_dict(module['classes'], uts.topological_sort_with_tie_ordering(order_dict(class_usages, class_tie_ordering), class_tie_ordering))

    for ek in module['enums']:
      e = module['enums'][ek]
      for i in range(len(e['items'])):
        e['items'][i] = order_dict(e['items'][i], ['name', 'value'])
      module['enums'][ek] = order_dict(e, ['align', 'items'])

    # priority 2 sort: original output ordering
    enum_ordering = list(module['enums'].keys())

    # priority 1 sort: compare file's ordering
    if reference_dir is not None and fname.lower() in reference_json_fnames_set:
      # note: reference_module was loaded above
      reference_module_enum_ordering = list(reference_module['enums'])
      reference_module_enum_ordering = { reference_module_enum_ordering[i]: i for i in range(len(reference_module_enum_ordering)) }
      enum_ordering.sort(key=lambda ek: reference_module_enum_ordering[ek] if ek in reference_module_enum_ordering else float('inf'))

    module['enums'] = order_dict(module['enums'], enum_ordering)

    module = order_dict(module, ['enums', 'classes'])

    dump = json.dumps(module, indent=2)
    for i in range(3):
      dump = re.sub(r'(\n\s+)("[^"]+": \[)(\],?\n)', r'\1\2\1\3', dump)
    with open(os.path.join(sdk_dir, f"{fname}_postprocessed.json"), 'w') as f:
      f.write(dump)

  print(f"Saving...")
  for fname in sdk_json_fnames:
    shutil.copy(
      os.path.join(sdk_dir, f"{fname}_postprocessed.json"),
      os.path.join(sdk_dir, fname)
    )
  
  print(f"Cleaning up...")
  for fname in sdk_json_fnames:
    os.remove(os.path.join(sdk_dir, f"{fname}_postprocessed.json"))

  print(f"Done")

if __name__ == '__main__':
  if not (
    len(sys.argv) == 2
    or len(sys.argv) == 3
    or (len(sys.argv) == 4 and sys.argv[3] == '--non-interactive')
  ):
    print(f"Usage: {sys.argv[0] if len(sys.argv) > 0 else 'program'} <path_to_schema_dir_to_postprocess> [path_to_reference_schema_dir] [--non-interactive]")
    sys.exit(1)

  main(
    sys.argv[1], 
    reference_dir=(None if len(sys.argv) == 2 or (len(sys.argv) == 3 and sys.argv[2] == '--non-interactive') else sys.argv[2]), 
    interactive=(len(sys.argv) < 3 or sys.argv[-1] != '--non-interactive')
  )
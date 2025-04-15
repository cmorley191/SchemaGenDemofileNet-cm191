
def topological_sort_with_tie_ordering(graph, tie_ordering):
  tie_ordering = { tie_ordering[i]: i for i in range(len(tie_ordering)) }

  in_degree = {node: 0 for node in graph}
  for node in graph:
    for neighbor in graph[node]:
      in_degree[neighbor] += 1
  
  queue = [node for node in graph if in_degree[node] == 0]
  
  result = []
  
  while queue:
    queue.sort(key=lambda x: tie_ordering[x] if x in tie_ordering else float('inf'))
    
    node = queue.pop(0)
    result.append(node)
    
    for neighbor in graph[node]:
      in_degree[neighbor] -= 1
      if in_degree[neighbor] == 0:
        queue.append(neighbor)
  
  if len(result) != len(graph):
    print(f"Cycle detected, {len([x for x in in_degree if in_degree[x] != 0])}: {[x for x in in_degree if in_degree[x] != 0][:10]}")
  
  return result + [x for x in graph if x not in result]
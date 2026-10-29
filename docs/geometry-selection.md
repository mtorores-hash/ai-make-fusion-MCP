# Geometry Selection

## Geometric selection

The selector returns ALL matches with a count. It never silently chooses the first edge.
Example: restrict to vertical line edges in a tower's local bounding region, associated
with the current faces of its extrusion:

```python
edges = ctx.select_edges(tower_body, {
    'geometry_type': 'Line3D',
    'parallel_to': [0, 0, 1],
    'length_mm': [20, 40],
    'within_box_mm': [[-8, -8, 0], [8, 8, 45]],
    'tolerance_mm': 0.05
}, feature=tower_extrusion)
ctx.record('tower_edge_candidates', [ctx.ref(e) for e in edges])
```

Supported predicates: geometry_type; parallel_to; normal_parallel_to; length_mm,
radius_mm and area_mm2 ranges; within_box_mm; at_coordinate_mm; tolerance_mm;
angular_tolerance_deg. Geometry is component-local. Geometric bounds describe whole
entities, so `at_coordinate_mm: {'z': 10}` selects geometry entirely on that plane.

“Outer spring-tower edges” is design intent. The agent has to translate it
using the inspected model. Feature filtering uses its current faces/boundary edges, not
immutable historical topology. Requery after an edit; compare live entities when needed,
not entityToken string equality. Existing read_selection remains available for ambiguous
cases. Repeated instances require occurrence context for assembly checks.


## v0.4 update

See [Execution and verification contracts and remaining work](upgrade-v0.4.md) for the latest behavior.

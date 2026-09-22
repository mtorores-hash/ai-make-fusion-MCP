from typing import Literal
from mcp.server.fastmcp import FastMCP
from bridge_client import call

mcp = FastMCP('Fusion Prompt MCP', instructions='Inspect the active document and target component before mutations. '
    'For complex work use run_model_script once, then poll job_status; reuse the SAME operation_id and '
    'identical request after a connection timeout. Interrupted jobs are NEVER automatically replayed. '
    'Scripts are trusted full Python, not sandboxed. Use ctx.stage checkpoints before major changes. '
    'All API calls run on the Fusion main thread. Native length units are cm; use ctx.point/value. '
    'Inspect/validate results. Do not equate sampled motion clearance with continuous collision freedom.')

@mcp.tool()
def inspect_design() -> dict:
    """Read active design ID, root bodies, sketches, parameters, and feature health."""
    return call('inspect')

@mcp.tool()
def new_design() -> dict:
    """Open a new unsaved parametric design without closing existing documents."""
    return call('new_design')

@mcp.tool()
def rectangle_sketch(design_id: str, name: str, width_mm: float, height_mm: float,
                     x_mm: float = 0, y_mm: float = 0,
                     plane: Literal['XY','XZ','YZ'] = 'XY') -> dict:
    """Create a rectangle in a new root sketch from a lower-left corner. Size is initial geometry,
    not driven by named parameters. Returns a sketch token for extrude."""
    return call('rectangle', locals())

@mcp.tool()
def circle_sketch(design_id: str, name: str, diameter_mm: float,
                  x_mm: float = 0, y_mm: float = 0,
                  plane: Literal['XY','XZ','YZ'] = 'XY') -> dict:
    """Create a circle in a new root sketch. Coordinates are sketch-local mm."""
    return call('circle', locals())

@mcp.tool()
def extrude(design_id: str, sketch_token: str, distance: str, name: str,
            operation: Literal['new_body','new_component','join','cut'] = 'new_body',
            profile_index: int = 0, target_body_token: str = '') -> dict:
    """Extrude a profile; distance is positive, e.g. '4 mm' or 'plate_thickness'.
    new_component creates an assembly component. Cut requires target_body_token. Starts at sketch plane in positive normal direction.
    Join may affect touching root bodies. Inspect before and after."""
    return call('extrude', locals())

@mcp.tool()
def set_parameter(design_id: str, name: str, expression: str, unit: str = 'mm') -> dict:
    """Create/update a user parameter. Existing model parameters can also be updated by name.
    Example expression '4 mm'. Only features that reference it will change."""
    return call('parameter', locals())

@mcp.tool()
def export_model(design_id: str, filename: str, format: Literal['step','stl'],
                 body_token: str = '') -> dict:
    """Export STEP of root component or STL of one specified body. Filename only, no paths.
    Writes to ~/FusionPromptExports and refuses overwrites. Returns local path."""
    return call('export', locals())

@mcp.tool()
def fusion_capabilities(design_id: str) -> dict:
    """Report loaded add-in version and supported advanced operations."""
    return call('capabilities', locals())

@mcp.tool()
def inspect_assembly(design_id: str) -> dict:
    """List native components, occurrence tokens, component body tokens and root joints.
    Keep the occurrence token with native geometry to distinguish repeated instances."""
    return call('inspect_assembly', locals())

@mcp.tool()
def inspect_body(design_id: str, body_token: str) -> dict:
    """List edge/face/vertex tokens and component-local geometry in mm.
    Reinspect after topology edits; do not guess edge indices."""
    return call('inspect_body', locals())

@mcp.tool()
def read_selection(design_id: str) -> dict:
    """Read entities selected by the user in Fusion, with occurrence contexts.
    Useful when verbal edge/face descriptions are ambiguous. Finish active commands first."""
    return call('read_selection', locals())

@mcp.tool()
def fillet_edges(design_id: str, edge_tokens: list[str], radius: str,
                 name: str = 'MCP Fillet', tangent_chain: bool = False,
                 rolling_ball: bool = True) -> dict:
    """Create a native constant-radius fillet on explicitly inspected/selected edges of one body.
    Radius accepts '2 mm' or a parameter. Works inside local components; modifying a component
    definition affects ALL its instances. Linked components must be edited in their source.
    Kernel failures can occur for oversized radii. Inspect health and topology after editing."""
    return call('fillet', locals())

@mcp.tool()
def create_joint(design_id: str, geometry_one: str, geometry_two: str,
                 occurrence_one: str = '', occurrence_two: str = '',
                 kind: Literal['rigid','revolute','slider','cylindrical'] = 'rigid',
                 name: str = 'MCP Joint', axis: Literal['X','Y','Z'] = 'Z',
                 keypoint_one: Literal['center','start','end','middle'] = 'center',
                 keypoint_two: Literal['center','start','end','middle'] = 'center',
                 offset: str = '0 mm', angle: str = '0 deg', flipped: bool = False) -> dict:
    """Create a STANDARD joint: Fusion may reposition components to align the references.
    Use planar face centers, compatible edge keypoints, or vertices from inspect_body/selection.
    Each component reference needs its occurrence token from inspect_assembly; empty means root.
    Axis is in the joint frame, NOT global coordinates. This is not an as-built joint.
    Preserve existing placements unless the user requested alignment. Inspect returned health."""
    return call('joint', locals())

def job_store():
    from FusionPromptBridge.job_store import Store
    return Store()

@mcp.tool()
def run_model_script(operation_id: str, document_id: str, component_token: str,
                     units: Literal['mm','cm','m','in'], script: str,
                     checkpoint_before: bool = True, validate_after: bool = True) -> dict:
    """Enqueue a complete trusted Fusion Python script defining run(ctx); returns immediately.
    Arbitrary Python executes with the user's permissions INSIDE Fusion, on its main thread.
    document_id is inspect_design.design_id; component_token is an explicit Component token.
    Use ctx.target, ctx.point/value, ctx.progress, ctx.stage, ctx.record, ctx.export and return JSON.
    The same operation_id + exact request returns the same job; changed content is rejected.
    Poll job_status/job_result; NEVER auto-retry an interrupted job with a fresh ID.
    Checkpoints export the full design before code runs. Failure aborts before modeling.
    Cancellation is cooperative; a kernel call or tight Python loop cannot be forcibly interrupted.
    Units declare helper inputs; raw adsk floats STILL use Fusion native cm/radians."""
    return job_store().submit(locals())

@mcp.tool()
def job_status(job_id: str) -> dict:
    """Read durable status/progress without waiting for Fusion's UI thread."""
    return job_store().status(job_id)

@mcp.tool()
def job_result(job_id: str) -> dict:
    """Read structured results, created refs, measurements, warnings, files and full traceback.
    While running, returns the latest flushed partial result. Local file paths refer to Fusion's PC."""
    return job_store().result(job_id)

@mcp.tool()
def list_jobs(limit: int = 30) -> list[dict]:
    """Find previous jobs after reconnecting; newest first."""
    return job_store().list(limit)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """Cancel queued work, or request cooperative cancellation of running work. No automatic rollback."""
    return job_store().cancel(job_id)

@mcp.tool()
def inspect_full_assembly(design_id: str, include_topology: bool = False,
                          offset: int = 0, limit: int = 10) -> dict:
    """Page all component definitions including nested bodies, feature/joint health, sketch dimensions,
    named parameters and occurrence transforms. Optional faces/edges can be large. Follow next_offset.
    Geometry is component-local mm; transform matrices use cm. ctx.inspect(True) returns all pages in a batch."""
    return call('inspect_full', locals())

@mcp.tool()
def select_geometry(design_id: str, body_token: str, kind: Literal['edge','face'],
                    filters: dict, feature_token: str = '') -> dict:
    """Select ALL matches by geometry, optionally bounded by current faces of an originating feature.
    Filters: geometry_type (Line3D/Plane/Cylinder/Circle3D), parallel_to or normal_parallel_to [x,y,z],
    length_mm/radius_mm/area_mm2 [min,max], within_box_mm [[minxyz],[maxxyz]],
    at_coordinate_mm {x:...,y:...,z:...}, tolerance_mm, angular_tolerance_deg.
    Bounds and directions are COMPONENT-LOCAL. Requery after edits; check count, never blindly use first.
    Feature association means its CURRENT faces/boundary edges, not immutable historical provenance."""
    return call('select_geometry', locals())

@mcp.tool()
def measure_minimum_distance(design_id: str, one: dict, two: dict) -> dict:
    """World-space minimum distance in mm. Refs: {token, occurrence_token}.
    Component geometry needs occurrence context. Zero may mean touching or overlapping."""
    return call('measure_distance', locals())

@mcp.tool()
def check_interference(design_id: str, references: list[dict]) -> dict:
    """Check current-pose interference volumes for body/occurrence references in assembly context.
    Preserves design type. API unsupported-state errors are reported, never treated as a clear result."""
    return call('check_interference', locals())

@mcp.tool()
def validate_model(design_id: str) -> dict:
    """Report feature/joint errors and warnings across component definitions. Not a printability guarantee."""
    return call('validate_model', locals())

if __name__ == '__main__':
    mcp.run(transport='stdio')

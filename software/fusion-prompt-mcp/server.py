from typing import Literal
from mcp.server.fastmcp import FastMCP
from bridge_client import call, require_compatible_bridge

mcp = FastMCP('Fusion Prompt MCP', instructions='Inspect the active document and target component before mutations. '
    'Observe with inspect_document_state; acquire_edit_token with the designated writer before mutations. '
    'Use selected scope and task contract 1.0 for bounded work; legacy calls remain unbounded. Preserve manual edits; '
    'save named parts in Fusion cloud projects and link them into assemblies. '
    'For complex work use run_model_script once, then poll job_status; reuse the SAME operation_id and '
    'identical request after a connection timeout. Interrupted jobs are NEVER automatically replayed. '
    'Scripts are trusted full Python, not sandboxed. Use ctx.stage checkpoints before major changes. '
    'All API calls run on the Fusion main thread. Native length units are cm; use ctx.point/value. '
    'Before modeling, call get_modeling_rules and follow the returned authoring standard. '
    'Use named components and parameters, fully constrain native sketches, and audit_modeling_hygiene '
    'before declaring completion. Use ctx.export_checked for checked deliverables; checkpoints stay available. '
    'Contract 2.0: state/token/job/reconcile replies default compact; use report_id for immutable detail. '
    'Declare task.authoring budgets for bounded tree growth. Missing policy is procedural/unbounded; native health is not maintainability. '
    'Wrap slow native calls in ctx.native_call; record measurements before optional capture. '
    'Inspect/validate results. Do not equate sampled motion clearance with continuous collision freedom.')

@mcp.tool()
def get_modeling_rules(known_sha256: str = '') -> dict:
    """Read the installed authoring rules, version and SHA-256 before any design task.
    No Fusion connection required. Rules include required behavior, preferences, exceptions,
    manual-review items and the limits of automated hygiene enforcement."""
    from FusionPromptBridge.modeling_rules import get_rules
    return get_rules(known_sha256)

@mcp.resource('fusion://modeling-rules')
def modeling_rules_resource() -> str:
    """Installed Fusion authoring standard; also available via get_modeling_rules."""
    return get_modeling_rules()['text']

@mcp.tool()
def audit_modeling_hygiene(design_id: str, scope: dict | None = None) -> dict:
    """Read-only scoped audit (scope omitted = legacy whole-design authoring checks): naming, sketch constraints/size/Fix, timeline health,
    parameter metadata/dependencies and root-body review. Does not regenerate or repair.
    Unknown API data fails completeness; zero errors is NOT proof of the full standard.
    Imported/linked definitions are included; preserve ownership before proposing repairs."""
    return call('audit_hygiene', locals())

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
                     plane: Literal['XY','XZ','YZ'] = 'XY', edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
    """CONCEPT PRIMITIVE: create a rectangle in a new root sketch from a lower-left corner. Size is initial geometry,
    not driven by named parameters. Returns a sketch token for extrude."""
    return call('rectangle', locals())

@mcp.tool()
def circle_sketch(design_id: str, name: str, diameter_mm: float,
                  x_mm: float = 0, y_mm: float = 0,
                  plane: Literal['XY','XZ','YZ'] = 'XY', edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
    """CONCEPT PRIMITIVE: create a circle in a new root sketch; no driving constraints promised. Coordinates are sketch-local mm."""
    return call('circle', locals())

@mcp.tool()
def extrude(design_id: str, sketch_token: str, distance: str, name: str,
            operation: Literal['new_body','new_component','join','cut'] = 'new_body',
            profile_index: int = 0, target_body_token: str = '', edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
    """ROOT CONCEPT PRIMITIVE: extrude a root profile; distance is positive, e.g. '4 mm' or 'plate_thickness'.
    new_component creates an assembly component. Cut requires target_body_token. Starts at sketch plane in positive normal direction.
    Join may affect touching root bodies. Inspect before and after."""
    return call('extrude', locals())

@mcp.tool()
def set_parameter(design_id: str, name: str, expression: str, unit: str = 'mm', edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
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
def fusion_capabilities(design_id: str = '') -> dict:
    """Compare server/native runtime, contract, rules and build identities. Empty design_id returns identity without selecting a document.
    compatible=False blocks mutations; reconnect/restart matching builds. A supplied inspected design_id also returns modeling capabilities."""
    from FusionPromptBridge.compatibility import identity
    bridge=call('runtime_identity',{})
    server=identity()
    result=call('capabilities',{'design_id':design_id}) if design_id else {'version':bridge['runtime'],'caller_contract_version':bridge['caller_contract']}
    return dict(result,server_identity=server,bridge_identity=bridge,
                compatible=all(bridge.get(k)==v for k,v in server.items()))

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
                 rolling_ball: bool = True, edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
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
                 offset: str = '0 mm', angle: str = '0 deg', flipped: bool = False, edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
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
                     checkpoint_before: bool = True, validate_after: bool = True,
                       mode: Literal['modeling','read_only','reconcile'] = 'modeling', edit_token: str = '', scope: dict | None = None, task: dict | None = None,
                 accepted_reference_versions: dict | None = None) -> dict:
    """Enqueue a complete trusted Fusion Python script defining run(ctx); returns immediately.
    Arbitrary Python executes with the user's permissions INSIDE Fusion, on its main thread.
    document_id is inspect_design.design_id; component_token is an explicit Component token or @root.
    mode=read_only accepts ONLY def run(ctx): return queries with literal arguments to
    ctx.inspect/validate/minimum_distance/interference/capture/present/audit_hygiene/evidence_fingerprint. Set checkpoint_before=False.
    Read-only queries do not regenerate. Full Python modeling always regenerates at completion.
    Use ctx.native_call for durable operation identity; ctx.record flushes measurements; ctx.capture(required=False) is optional.
    task.authoring adopts issue budgets; arbitrary Python is measured posthoc, not pre-dispatch bounded.
    Use ctx.target, ctx.point/value, ctx.progress, ctx.stage, ctx.record, ctx.export and return JSON.
    The same operation_id + exact request returns the same job; changed content is rejected.
    Poll job_status/job_result; NEVER auto-retry an interrupted job with a fresh ID.
    Modeling requires acquire_edit_token (matching task.writer_id), or the explicit legacy writer path.
    Caller contract 2.0 retains scope/task version 1.0; scope revisions are checked before execution, and allowed edits afterward. Checkpoints use local F3D or
    a completed clean cloud version manifest for linked assemblies. Failure aborts before modeling.
    mode='reconcile' accepts only return ctx.acknowledge_authoring(...) with literal arguments;
    use current scope/task/writer token and checkpoint_before=False, validate_after=False. Ledger-only, never regeneration/replay.
    Cancellation is cooperative; a kernel call or tight Python loop cannot be forcibly interrupted.
    Units declare helper inputs; raw adsk floats STILL use Fusion native cm/radians."""
    request=locals()
    if mode!='read_only':require_compatible_bridge()
    return job_store().submit(request)

@mcp.tool()
def job_status(job_id: str) -> dict:
    """Read durable status/progress without waiting for Fusion's UI thread."""
    return job_store().status(job_id)

@mcp.tool()
def job_result(job_id: str = '', section: str = 'summary', report_id: str = '',
               offset: int = 0, limit: int = 50, after_revision: str = '', baseline_report_id: str = '') -> dict:
    """Compact by default; full is explicit. Immutable detail: report_id plus raw or JSON-pointer section,
    offset/limit (structured <=100). raw cursors count characters. delta compares document parameters.
    events returns durable activity after offset cursor. engineering retains detailed engineering retrieval.
    Full evidence remains stored; omissions never imply pass. Poll job_status while Fusion is busy."""
    from FusionPromptBridge import reporting
    store=job_store()
    if report_id:return reporting.page(store,report_id,section,offset,limit,baseline_report_id)
    if section=='events':return store.events(job_id,offset,min(limit,100))
    if section=='engineering':
        from FusionPromptBridge.job_store import load_engineering_report
        return load_engineering_report(store,job_id)
    return reporting.response(store,store.result(job_id),section,after_revision,offset,limit)

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
                          offset: int = 0, limit: int = 10, scope: dict | None = None,
                          include_context: bool = False) -> dict:
    """Page selected components (scope omitted = legacy full design), including bodies, health, sketch dimensions,
    named parameters and occurrence transforms. Optional faces/edges can be large. Follow next_offset.
    Occurrences/parameters appear on page zero or include_context=True. Geometry is component-local mm; transform matrices use cm. ctx.inspect(True) returns all pages in a batch."""
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
def validate_model(design_id: str, scope: dict | None = None) -> dict:
    """Report feature/joint errors and warnings across component definitions. Not a printability guarantee."""
    return call('validate_model', locals())

@mcp.tool()
def browse_cloud(hub_id: str = '', project_id: str = '', folder_id: str = '') -> dict:
    """Browse Fusion hubs, projects, or one folder's files/subfolders. IDs are authoritative.
    Omit all IDs for hubs; supply hub for projects; hub+project for its root folder.
    File records contain stable id, version_id for opening, version, processing/read-only state."""
    return call('browse_cloud', locals())

@mcp.tool()
def inspect_document_state(document_id: str, acquire_token: bool = False, section: Literal['summary','full'] = 'summary', after_revision: str = '') -> dict:
    """Read-only observation by default: cloud identity, dirty state, revisions and references.
    Does not invalidate a writer token. acquire_token=True is the v0.5 legacy writer path.
    New writers use acquire_edit_token, with writer identity and explicit accepted reference pins.
    Historical inspection never authorizes overwriting a newer cloud target."""
    return call('document_state', locals())

@mcp.tool()
def cloud_operation(operation_id: str,
                    action: Literal['ensure_project','ensure_folder','save','save_component','open','insert','update_reference'],
                    arguments: dict) -> dict:
    """Durable main-thread cloud job. Poll job_status/job_result; retry SAME ID+arguments.
    ensure_project: hub_id,name; creates/reuses project and Assembly/Parts/Purchased Components folders.
    ensure_folder: hub_id,project_id,folder_id (parent),name.
    open: version_id,expected_version; allow_historical=True permits inspection, never stale-target writes.
    save: document_id,edit_token,description; FIRST save also hub_id,project_id,folder_id,name.
    save_component: same first-save arguments + component_token; independent native copy, NOT link replacement.
    insert: document_id,edit_token,version_id,expected_version,transform_cm (16 matrix values).
    update_reference: document_id,edit_token,file_id,expected_latest_version; one direct reference.
    Insert/update require a clean completed cloud save as recovery checkpoint. Insert links same-project files.
    Save succeeds only after isComplete. Cancellation stops monitoring, not the actual cloud upload.
    Results preserve file id/version_id and source mapping. Interrupted jobs are never replayed.
    Mutating arguments also take writer_id and accepted_reference_versions (file_id: exact current version).
    Historical insert needs allow_historical=True and accepted_insert_version.
    Dirty/stale preservation: save with accepted pins; update one reference; repin current versions and save; repeat.
    Uncertain terminal saves block further mutations until reconcile_cloud_job records an observed version and caller note.
    No deletes, share links, contributor changes or automatic replacement of existing components."""
    request=locals()
    require_compatible_bridge()
    return job_store().submit_cloud(request)

@mcp.tool()
def acquire_edit_token(document_id: str, writer_id: str,
                       accepted_reference_versions: dict | None = None, section: Literal['summary','full'] = 'summary') -> dict:
    """Acquire/reuse one unchanged writer baseline. Pins map cloud file_id to exact accepted version.
    A different writer cannot replace the lease; release it explicitly. Single-use token, optimistic
    checks only. Writer IDs and approval text are caller assertions, not authenticated authorization."""
    return call('acquire_edit_token',locals())

@mcp.tool()
def release_edit_token(document_id: str, writer_id: str, edit_token: str) -> dict:
    """Release an unused writer token by exact identity; does not change the model."""
    return call('release_edit_token',locals())

@mcp.tool()
def reconcile_cloud_job(job_id: str, version_id: str = '', confirmation_note: str = '', section: Literal['summary','full'] = 'summary') -> dict:
    """Observe a failed/cancelled/interrupted save's expected cloud version without replay.
    Provide version_id from Fusion history. A nonempty confirmation_note records the caller's
    verification of its contents and clears the mutation block; it is NOT authenticated approval.
    Original terminal execution status remains intact. Unknown/absent outcomes need manual recovery."""
    return call('reconcile_cloud_job',locals())

@mcp.tool()
def retire_occurrences(operation_id: str, document_id: str, occurrence_tokens: list[str],
                       reason: str, dependency_review_note: str, scope: dict, task: dict,
                       edit_token: str, replacement_id: str = '',
                       accepted_reference_versions: dict | None = None) -> dict:
    """Durably remove selected top-level leaf occurrences using native Remove features.
    Requires explicit scope/task, permitted root and source members, completed checkpoint and reviewed
    dependencies. Refuses live joints/rigid groups, derived occurrences or nested/subtree removal.
    Preserves shared definitions and source/history, verifies surviving placements. Returns lifecycle
    facts for caller reconciliation; does not update BOM/graph/site. Projection/derive review is caller-owned."""
    source='def run(ctx): return ctx.retire_occurrences('+','.join(repr(v) for v in
             (occurrence_tokens,reason,replacement_id,dependency_review_note))+')'
    require_compatible_bridge()
    return job_store().submit(dict(operation_id=operation_id,document_id=document_id,component_token='@root',
        units='mm',script=source,checkpoint_before=True,validate_after=True,edit_token=edit_token,
        scope=scope,task=task,accepted_reference_versions=accepted_reference_versions))

if __name__ == '__main__':
    mcp.run(transport='stdio')

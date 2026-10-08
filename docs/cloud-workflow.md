# Fusion cloud workflow — v0.5.0 development

This build adds executable tools for shared human/AI CAD editing. It has not been validated
against a live Fusion cloud account here. Both the MCP server and add-in must be upgraded.

## Normal workflow

1. `browse_cloud()` lists accessible hubs. Select the user's intended hub by ID.
2. `cloud_operation(operation_id, "ensure_project", {"hub_id": ..., "name": ...})` creates
   or reuses an unambiguous project and Assembly, Parts and Purchased Components folders.
   Poll `job_result` for IDs. No contributors, permissions or public sharing are changed.
3. Create a new native part with `new_design`, name its geometry and model parametrically.
   Before every mutation get `inspect_document_state(document_id)` and pass its edit_token.
4. First `save` supplies document_id, edit_token, hub_id, project_id, folder_id, name and
   optional description. Later saves supply only document_id, edit_token and description:
   they create versions of the same file in place. Poll until succeeded AND cloud_complete.
5. Create/save a named assembly in Assembly. Use `insert` with the part's version_id,
   expected_version and an explicit transform_cm matrix. Only linked same-project insertion
   is supported. Identity matrix: `[1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]`.
   The assembly must be clean and fully saved before each insertion/reference update.
6. Save the assembly, and hand off its project/name/file ID plus the part IDs and versions.

The cloud file's `id` is stable lineage identity; `version_id` identifies one saved version
and is accepted by Autodesk's findFileById. Bridge document_id and component tokens are not
substitutes for persistent file identity. Record mappings in the design project's handoff;
job results also retain returned IDs, versions and source component tokens locally.

## User edits and AI resumption

Open the named part from Fusion's Data Panel, edit normally and save. The AI browses/inspects
again, opens the latest inspected version, inspects the actual geometry and obtains a new
token before editing. It must adapt to your geometry rather than rebuild from an old script.
Dirty open documents are never discarded or silently reloaded. If the target is already open
with unsaved changes or an old version, `open` stops and leaves it intact.

In the assembly, inspect state to see nested reference versions. For a direct reference use
`update_reference` with file_id and expected_latest_version plus document_id/edit_token.
It pins that inspected version, preserves the link and leaves the assembly dirty for review.
Edit a nested subassembly in its own document to update its direct references. Inspect
feature/joint health, placements and interference after updating; then save the assembly.

Tokens acknowledge the inspected state, including unsaved edits; they do not implicitly
save it. Component revisions detect dirty-to-dirty edits. Stale/read-only/in-use/processing
cloud targets and unsaved referenced documents block mutations. Stale references block normal
modeling but may be updated explicitly. Tokens are consumed once; inspect again after a
mutation. These are optimistic checks, not multi-user locking or isolation during arbitrary
trusted scripts. Avoid editing interactively during a running batch. API metadata refresh
cannot establish a transactional cloud lock.

## Existing internal components

`save_component` takes the first-save arguments and an explicit native component_token.
It saves an independent native cloud copy through Component.saveCopyAs and returns its file
identity once upload/cloud processing completes. It does not replace any original occurrence
or transfer joints to a new linked occurrence. Do not insert copies over existing parts and
call that migration complete. Preserve the original assembly; plan and inspect the linkage
and joint migration separately. For new work, separate part documents avoid this conversion.

## Jobs and recovery

All cloud writes use durable operation IDs. Retry the identical request with the SAME ID
when a connection times out. Changed content with that ID is rejected. After a failed or
interrupted operation inspect partial results, Data Panel and version history before any new
action. Project/folder creation reuses a unique exact name (case-insensitive comparison);
ambiguous names stop. Existing destination filenames block new file/copy creation.

Saves remain running while a DataFileFuture uploads or a new document version is processing.
Success requires the expected new version and isComplete, not merely save() returning true.
Monitoring is bounded to ten minutes; timeout/cancellation cannot undo the cloud upload.
Cancelled or interrupted saves may finish later. Reconcile their actual status in Fusion.
Never assume a cancelled monitor means the file was not saved. Offline/permissions/API errors
are surfaced; the tool does not create a misleading local-file substitute.

For linked assemblies the checkpoint is a JSON manifest of the clean completed cloud version
and its referenced versions. It is not a standalone archive or automatic rollback. Open the
recorded version in Fusion and inspect its dependencies before choosing recovery manually.
Unsaved linked assemblies must be saved/polled first. Mid-batch checkpoints after changes
therefore stop; split modeling into batches separated by save jobs. Local unlinked designs
keep F3D checkpoint behavior. Disposable F3D experiments reject linked cloud checkpoints.

## Local Fusion acceptance

Use a disposable project and simple parts first:

1. Upgrade both processes; verify capabilities 0.5.0, 28 tools and rules 1.0.5.
2. Create a project twice with the same operation ID: one job/project. Verify three folders.
3. First-save a named native part; observe pending then complete; record ID/version.
   Edit and save again: same ID and next version, no duplicate file.
4. Inspect state, manually change a parameter, submit a batch with the old token: no script
   runs. Reinspect and confirm the next authorized change preserves the manual feature.
5. Save a second part and assembly, link both at known transforms, save after each insertion.
   Open one part, manually modify/save it; verify assembly detects the newer reference.
   Save/inspect assembly, update only that reference, inspect joints and placements, save.
6. Try opening a dirty already-open part: it must stay open/unchanged. Try a stale version,
   read-only target or wrong active document: mutation must stop.
7. Save a component copy and verify native editability and preserved original occurrences/joints.
8. Checkpoint a clean linked assembly: JSON records assembly/reference versions. Dirty linked
   checkpoint stops. Verify recorded versions can actually be opened from Data Panel history.
9. Disconnect/reconnect MCP during upload; poll the original job. Test add-in restart on a
   disposable pending job: interrupted, no replay. Inspect any late cloud completion manually.

Record actual Fusion version/account type, returned IDs/versions and outcomes in the design
project. Automated API doubles do not prove cloud availability, joint preservation after a
real update, native editability of a copy, or the CAD kernel's behavior.

## Autodesk references

- [Project creation](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataProjects_add.htm)
- [Document save](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Document_save.htm)
- [First save](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Document_saveAs.htm)
- [Component copy](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Component_saveCopyAs.htm)
- [Linked insertion](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Occurrences_addByInsert.htm)
- [DataFile identity, versions and processing](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DataFile.htm)
- [Reference version](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_DocumentReference.htm)
- [Component revision ID](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Component_revisionId.htm)

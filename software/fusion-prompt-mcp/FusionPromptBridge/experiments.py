"""Disposable F3D experiments. Trusted callbacks only; not an arbitrary-code sandbox."""
import traceback
import adsk.fusion
from . import model_tools, verification


def snapshot(design, bodies, protected=None):
    bodies=list(bodies)
    if not bodies: raise ValueError('Snapshot requires at least one body')
    boxes=[model_tools.bbox(body) for body in bodies]
    report=model_tools.validate(design)
    return {'body_count':len(bodies), 'all_solid':all(body.isSolid for body in bodies),
            'all_valid':all(body.isValid for body in bodies),
            'volume_mm3':sum(body.volume*1000 for body in bodies),
            'envelope_mm':[min(b['min_mm'][i] for b in boxes) for i in range(3)]+
                          [max(b['max_mm'][i] for b in boxes) for i in range(3)],
            'feature_errors':report['feature_errors'], 'inspection_warnings':report['warnings'],
            'protected':protected or {}}


def try_feature(ctx, name, build, select_bodies, rules, protected_metrics=None, capture=True):
    """Build on a new document imported from a checkpoint, never delete features to undo.

    select_bodies(design) must re-resolve bodies in the NEW document; return geometry
    in one explicit coordinate frame. protected_metrics(design) returns numeric metrics.
    An accepted candidate is exported, NOT merged into the source. Rejected documents
    close without saving. Callbacks must not switch documents or export release files.
    """
    if ctx.read_only: raise ValueError('Experiments require modeling mode')
    if not callable(build) or not callable(select_bodies): raise ValueError('Callbacks required')
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
        raise ValueError('Experiment name must use letters, digits, underscore or hyphen')
    ctx.synchronize()
    source=ctx.document; source_design=ctx.design; source_target=ctx.target; source_guard=ctx.guard
    before=snapshot(source_design,select_bodies(source_design),
                    protected_metrics(source_design) if protected_metrics else {})
    # Validate acceptance policy before invoking a candidate callback.
    verification.geometry_delta(before,before,rules)
    checkpoint=ctx.checkpoint('experiment_'+name)
    candidate=None; report={'accepted':False,'reasons':[],'checkpoint':checkpoint}
    try:
        manager=ctx.app.importManager
        options=manager.createFusionArchiveImportOptions(checkpoint['path'])
        candidate=manager.importToNewDocument(options)
        if not candidate or candidate==source: raise RuntimeError('Disposable import failed')
        if not candidate.activate(): raise RuntimeError('Candidate activation failed')
        design=adsk.fusion.Design.cast(candidate.products.itemByProductType('DesignProductType'))
        if not design: raise RuntimeError('Imported archive has no Design product')
        def candidate_guard():
            if not candidate.isValid or ctx.app.activeDocument!=candidate:
                raise RuntimeError('Experimental document changed; refusing further work')
        ctx.document=candidate; ctx.design=design; ctx.target=design.rootComponent; ctx.guard=candidate_guard
        imported=snapshot(design,select_bodies(design),protected_metrics(design) if protected_metrics else {})
        # Detect archive corruption before applying the experiment.
        if verification.fingerprint(imported)!=verification.fingerprint(before):
            # Entity tokens in feature error reports can differ across archives; reject conservatively.
            raise RuntimeError('Archive snapshot differs from source; inspect round-trip before experimenting')
        camera=ctx.app.activeViewport.camera
        if capture: report['before_capture']=ctx.capture(name+'_before.png')
        build(ctx); ctx.synchronize()
        after=snapshot(design,select_bodies(design),protected_metrics(design) if protected_metrics else {})
        report.update(verification.geometry_delta(before,after,rules))
        if capture:
            camera.isSmoothTransition=False; ctx.app.activeViewport.camera=camera
            report['after_capture']=ctx.capture(name+'_after.png')
        if report['accepted']:
            report['candidate_archive']=ctx.export(name+'_accepted.f3d',design.rootComponent)
    except Exception as exc:
        report.update(accepted=False,reasons=report['reasons']+['candidate_error:'+str(exc)],
                      traceback=traceback.format_exc())
    finally:
        ctx.design=source_design; ctx.target=source_target; ctx.document=source; ctx.guard=source_guard
        try:
            if candidate and candidate!=source and candidate.isValid:
                if not candidate.close(False): raise RuntimeError('Candidate could not be closed')
            if not source.isValid or not source.activate(): raise RuntimeError('Source could not be reactivated')
            source_guard()
        except Exception as exc:
            report['accepted']=False; report['reasons'].append('document_recovery:'+str(exc))
            ctx.warn('Experiment document recovery failed: '+str(exc))
    # If cleanup invalidated acceptance, do not advertise an export as accepted.
    if not report['accepted'] and 'candidate_archive' in report:
        artifact=report.pop('candidate_archive')
        from pathlib import Path
        Path(artifact['path']).unlink(missing_ok=True)
        ctx.result['files']=[f for f in ctx.result['files'] if f['path']!=artifact['path']]
    ctx.record('experiment_'+name,report)
    return report

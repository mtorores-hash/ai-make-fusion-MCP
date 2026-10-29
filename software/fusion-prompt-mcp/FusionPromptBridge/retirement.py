"""Conservative Remove-feature retirement of top-level leaf occurrences.
Preserves definitions/history. Dependency preflight is intentionally limited and reported.
"""
import adsk.fusion
from . import advanced, scope

def retire(ctx, occurrence_tokens, reason, replacement_id='', dependency_review_note=''):
    if not occurrence_tokens or len(set(occurrence_tokens))!=len(occurrence_tokens):raise ValueError('Nonempty unique occurrence tokens required')
    if not reason.strip() or not dependency_review_note.strip():raise ValueError('Retirement reason and caller dependency review note required')
    if not ctx.boundary or not ctx.boundary.enabled:raise ValueError('Retirement requires an explicit task and scope')
    if not ctx.request.get('checkpoint_before'):raise ValueError('Retirement requires checkpoint_before=True')
    d=ctx.design;root=d.rootComponent
    ctx.boundary.require_component(root)
    candidates=[advanced.resolve(d,t,adsk.fusion.Occurrence) for t in occurrence_tokens]
    if any(o==p for i,o in enumerate(candidates) for p in candidates[:i]):raise ValueError('Duplicate occurrence aliases')
    before=scope.each(root.allOccurrences)
    records=[]
    for o in candidates:
        if not any(o==top for top in scope.each(root.occurrences)):
            raise ValueError('Nested retirement is unsupported; edit the owning source subassembly explicitly')
        if o.isDerived or o.childOccurrences.count:
            raise ValueError('Derived occurrence or subtree retirement requires prior dependency disentanglement')
        ctx.boundary.require_component(advanced.native(o.component))
        for attr in ('joints','asBuiltJoints','rigidGroups'):
            if getattr(o,attr).count:raise ValueError('Retirement blocked by live '+attr+'; resolve affected connections explicitly')
        records.append({'occurrence_token':o.entityToken,'part_id':ctx.selection.member(o.component)['id'],
                        'component_token':o.component.entityToken,'last_active_revision':o.component.revisionId,
                        'replacement_id':replacement_id,'reason':reason,
                        'shared_active_instances':sum(1 for p in before if p.component==o.component and not any(p==c for c in candidates))})
    # Keep every survivor's live identity and placement for postcondition checks.
    survivors=[(o,tuple(o.transform2.asArray())) for o in before if not any(o==c for c in candidates)]
    report={'requested':records,'removed':[],'blockers':[], 'external_records_updated':False,
            'history_policy':'Remove features; source documents and component definitions are not deleted',
            'dependency_review':'direct joints/rigid groups/children checked; projection/derive completeness is caller-reviewed',
            'dependency_review_note':dependency_review_note,'approval_status':'not_authenticated'}
    ctx.record('retirement',report)
    try:
        for o,row in zip(candidates,records):
            ctx.check_cancel()
            feature=root.features.removeFeatures.add(o)
            if not feature:raise RuntimeError('Fusion did not create Remove feature')
            feature.name='retire_'+row['part_id']
            ctx.synchronize()
            if any(o==x for x in scope.each(root.allOccurrences)):
                raise RuntimeError('Removed occurrence still in current assembly; retirement unverified')
            report['removed'].append(row);ctx.record('retirement',report)
        now=scope.each(root.allOccurrences)
        for survivor,matrix in survivors:
            if not any(survivor==x for x in now) or tuple(survivor.transform2.asArray())!=matrix:
                raise RuntimeError('Retirement changed an active survivor; inspect partial state')
        # Retire membership only when no current instance of the definition remains.
        current=scope.live_components(d);spec=ctx.selection.current_spec();retired=set()
        for m,c in ctx.selection.entries:
            if not any(c==live for live in current):retired.add(m['id'])
        for m in spec['members']:
            if m['id'] in retired:m['membership']='retired'
        for key in ('targets','dependencies'):
            spec[key]=[ident for ident in spec.get(key,[]) if ident not in retired]
        checks=[];excluded=[]
        for check in spec.get('required_checks',[]):
            remaining=[ident for ident in check['members'] if ident not in retired]
            if not remaining:excluded.append({'id':check['id'],'reason':'all members retired from current assembly'})
            else:checks.append(dict(check,members=remaining))
        spec['required_checks']=checks
        ctx.selection=scope.Selection(d,spec)
        report['retired_member_ids']=sorted(retired)
        report['excluded_checks']=excluded
        report['current_scope']=spec
        report['current_occurrences_verified']=True
        report['next']='Caller reconcile graph/BOM/context/export selections; refresh scope revisions'
        return report
    except Exception as exc:
        report['blockers'].append(str(exc));report['current_occurrences_verified']=False
        raise
    finally:ctx.record('retirement',report)

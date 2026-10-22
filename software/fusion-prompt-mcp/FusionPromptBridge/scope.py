"""Caller contract 1.0: explicit scope, revisions and observed boundaries, not approval.
Autodesk objects are compared by identity/equality after token resolution, never token text.
"""
import copy
import hashlib
import json
import adsk.fusion
from . import advanced

VERSION = '1.0'
ROLES = {'authored','purchased','reference','environment','clearance','fixture','presentation'}
MEMBERSHIP = {'active','retired','archived'}

def each(c): return [c.item(i) for i in range(c.count)]
def same(a,b): return a == b

def component(d, token):
    return d.rootComponent if token=='@root' else advanced.native(advanced.resolve(d,token,adsk.fusion.Component))

def live_components(d):
    result=[d.rootComponent]
    for o in each(d.rootComponent.allOccurrences):
        c=advanced.native(o.component)
        if not any(c==x for x in result):result.append(c)
    return result

def revisions(d):
    return [{'component_token': c.entityToken, 'name':c.name, 'revision':c.revisionId}
            for c in live_components(d)]

def selected(d, target):
    """Migration default: only target, no claim of complete functional dependencies."""
    return {'version':VERSION,'mode':'selected','targets':['target'],'dependencies':[],
            'members':[{'id':'target','component_token':'@root' if same(target,d.rootComponent) else target.entityToken,'revision':target.revisionId,
                        'membership':'active','maturity':'working','role':'authored'}],
            'parameter_names':[], 'required_checks':[], 'dependency_review':'not_supplied'}

class Selection:
    def __init__(self,d,spec,check_revisions=True):
        self.design=d;self.spec=copy.deepcopy(spec);self.entries=[];self.exclusions=[];self.gaps=[]
        self.legacy=spec is None
        live=live_components(d) if spec is not None else each(d.allComponents)
        if spec is None:
            self.spec={'version':VERSION,'mode':'full_design','targets':[],'dependencies':[],'members':[]}
            for i,c in enumerate(live):
                self.entries.append(({'id':'legacy_'+str(i),'component_token':c.entityToken,'revision':getattr(c,'revisionId',None),
                                      'membership':'active','maturity':'working','role':'authored'},c))
            self.target_ids={m['id'] for m,c in self.entries};self.relevant_ids=set(self.target_ids)
            return
        if not isinstance(spec,dict) or spec.get('version')!=VERSION:raise ValueError('scope.version must be 1.0')
        if spec.get('mode') not in ('selected','full_design'):raise ValueError('scope.mode must be selected or full_design')
        members=spec.get('members')
        if not isinstance(members,list) or not members:raise ValueError('Scope members must be nonempty')
        ids=set()
        if not isinstance(spec.get('targets'),list) or not isinstance(spec.get('dependencies',[]),list):raise ValueError('targets/dependencies must be lists')
        parameter_names=spec.get('parameter_names',[])
        if not isinstance(parameter_names,list) or not set(parameter_names)<={p.name for p in each(d.allParameters)}:
            raise ValueError('SCOPE_PARAMETERS_NOT_FOUND: scope.parameter_names must name existing inspected parameters. Put approved new names in task.allowed_parameter_names, then add them to the current scope after creation.')
        for m in members:
            if not isinstance(m,dict) or not isinstance(m.get('id'),str) or not m['id'] or m['id'] in ids:
                raise ValueError('Unique nonempty member id required')
            ids.add(m['id'])
            if m.get('membership') not in MEMBERSHIP or m.get('maturity') not in ('working','frozen') or m.get('role') not in ROLES:
                raise ValueError('Explicit membership, maturity and role required')
            if m['membership']!='active':
                # History may no longer resolve. A still-live retired definition cannot be silently hidden.
                try:c=component(d,m['component_token'])
                except ValueError:c=None
                if c is not None and any(c==x for x in live):
                    raise ValueError('Retired/archived member still occurs in active assembly; retire occurrence first')
                self.exclusions.append({'id':m['id'],'reason':m['membership']});continue
            c=component(d,m['component_token'])
            if not any(c==x for x in live):raise ValueError('Selected component is history, not current assembly membership')
            if any(c==old for _,old in self.entries):raise ValueError('Duplicate component aliases in scope')
            if not isinstance(m.get('revision'),str) or not m['revision']:raise ValueError('Member revision is required')
            if check_revisions and c.revisionId!=m['revision']:raise ValueError('Stale scope revision: '+m['id'])
            self.entries.append((m,c))
        active={m['id'] for m,c in self.entries}
        self.target_ids=set(spec.get('targets',[]))
        self.relevant_ids=self.target_ids | set(spec.get('dependencies',[]))
        if not self.target_ids or not self.relevant_ids<=active:raise ValueError('Empty, retired or unresolved scope targets/dependencies')
        if spec['mode']=='full_design' and (len(self.entries)!=len(live) or self.relevant_ids!=active):
            raise ValueError('full_design must enumerate every live component as a target or dependency')
        for c in live:
            if not any(c==obj and m['id'] in self.relevant_ids for m,obj in self.entries):
                self.exclusions.append({'component_token':c.entityToken,'reason':'outside selected task/dependencies'})
        # Joint-connected definitions are relevant even if the caller forgot to declare them.
        for owner in live:
            for collection in ('joints','asBuiltJoints'):
                for j in each(getattr(owner,collection)):
                    peers=[]
                    for attr in ('occurrenceOne','occurrenceTwo'):
                        o=getattr(j,attr)
                        if o:peers.append(advanced.native(o.component))
                    if any(self.contains(c,targets=True) for c in peers):
                        for c in peers:
                            if not self.contains(c):self.gaps.append({'check':'dependency_scope','message':'Joint-connected component missing','component_token':c.entityToken})
        if spec.get('dependency_review')!='complete':
            self.gaps.append({'check':'dependency_review','message':'Caller must declare reviewed dependency set; MCP cannot discover every projection/derive/interface'})

    def contains(self,c,targets=False):
        ids=self.target_ids if targets else self.relevant_ids
        return any(c==obj and m['id'] in ids for m,obj in self.entries)
    def components(self):return [c for m,c in self.entries if m['id'] in self.relevant_ids]
    def member(self,c):return next((m for m,obj in self.entries if c==obj),None)
    def authored(self,c,modified=()):
        m=self.member(c)
        return bool(m and (m['role']=='authored' or m['id'] in modified or m.get('authored',False)))
    def report(self):
        def revision(c):
            try:return c.revisionId if c.isValid else None
            except Exception:return None
        return {'contract_version':VERSION,'mode':self.spec['mode'],'legacy_full_design':self.legacy,
                'milestone':self.spec.get('milestone','unspecified'),'targets':sorted(self.target_ids),'dependencies':sorted(self.relevant_ids-self.target_ids),
                'members':[dict(m,current_revision=revision(c)) for m,c in self.entries],
                'exclusions':self.exclusions,'evidence_gaps':list(self.gaps),
                'coverage':'whole design (legacy authoring checks)' if self.legacy else self.spec['mode'],
                'approval_status':'not_evaluated'}
    def current_spec(self):
        spec=copy.deepcopy(self.spec)
        for m in spec['members']:
            entry=next(((x,c) for x,c in self.entries if x['id']==m['id']),None)
            if entry and getattr(entry[1],'isValid',True):m['revision']=entry[1].revisionId
        return spec
    def check_export(self,entity):
        native=advanced.native(entity)
        if adsk.fusion.Component.cast(native):owner=native
        elif adsk.fusion.BRepBody.cast(native):owner=native.parentComponent
        else:raise ValueError('Checked export requires one native component or BRepBody')
        if not self.contains(owner,targets=True):raise ValueError('Export entity does not match scope targets')
        if not native.isValid:raise ValueError('Export entity is invalid')
        if adsk.fusion.Component.cast(native):
            if not owner.bRepBodies.count and not owner.occurrences.count:raise ValueError('Empty component export')
            # Exporting a parent would include all its descendants, regardless of visibility.
            for o in each(owner.allOccurrences):
                if not self.contains(advanced.native(o.component),targets=True):
                    raise ValueError('Component export includes an unselected descendant; select all exported parts or export a body')
        elif not native.faces.count:raise ValueError('Empty body export')
        return owner


def evidence_fingerprint(selection,member_ids):
    """Conservative BRep/placement/declared-parameter dependency signature, not a geometric proof.
    Ignores component name metadata; any BRep revision change invalidates. Mesh/sketch-only
    or missing records are unsupported, not silently fresh. Caller declares complete interfaces.
    """
    rows=[]
    if not member_ids or not set(member_ids)<=selection.relevant_ids:raise ValueError('Evidence members outside relevant scope')
    for m,c in selection.entries:
        if m['id'] not in member_ids:continue
        bodies=each(c.bRepBodies)
        if not bodies:raise ValueError('Geometry evidence fingerprint requires BRep bodies')
        if c.meshBodies.count:raise ValueError('Mesh evidence reuse is unsupported')
        rows.append({'id':m['id'],'bodies':sorted((b.entityToken,b.revisionId) for b in bodies),
                     'placements':[o.transform2.asArray() for o in each(selection.design.rootComponent.allOccurrences) if o.component==c]})
    params=[(p.name,p.expression) for p in each(selection.design.allParameters) if p.name in selection.spec.get('parameter_names',[])]
    return hashlib.sha256(json.dumps({'members':rows,'parameters':params},sort_keys=True).encode()).hexdigest()


def evidence(selection):
    """Caller evidence, freshness checked; never authenticate an approval or physical test."""
    gaps=list(selection.gaps);rows=[];spec=selection.spec
    required=list(spec.get('required_checks',[]))
    for m,c in selection.entries:
        if m['id'] in selection.relevant_ids and not selection.authored(c):
            required.append({'id':'interface_envelope:'+m['id'],'members':[m['id']]})
    supplied=spec.get('evidence',[])
    for need in required:
        if not isinstance(need,dict) or not need.get('id') or not need.get('members'):
            raise ValueError('required_checks need id and nonempty members')
        if not set(need['members'])<=selection.relevant_ids:raise ValueError('Check dependencies must be in relevant scope')
        hits=[e for e in supplied if e.get('id')==need['id']]
        row={'id':need['id'],'status':'unproven','provenance':'caller_reported'}
        if len(hits)==1:
            record=hits[0];deps=record.get('revisions',{})
            current={m['id']:c.revisionId for m,c in selection.entries if m['id'] in need['members']}
            fresh=deps==current
            if record.get('geometry_fingerprint'):
                try:fresh=set(deps)==set(current) and record['geometry_fingerprint']==evidence_fingerprint(selection,need['members'])
                except Exception:fresh=False
            if record.get('contradicted_by'):
                fresh=False
                row['blocker']='Caller evidence has an unresolved contradiction'
            if need.get('kind')=='appearance':
                from .cad_review import appearance
                fresh=appearance(record,need) and fresh
            if need.get('applicable') is False and need.get('reason') and record.get('status')=='not_applicable' and record.get('reason') and fresh:
                row.update(status='not_applicable',reason=record['reason'])
            elif record.get('status') in ('pass','fail') and record.get('source') and fresh:
                row.update(status=record['status'],source=record['source'])
        if row['status'] in ('unproven','fail'):gaps.append({'check':need['id'],'message':row['status']})
        rows.append(row)
    return rows,gaps


def health_snapshot(d):
    """Cheap global integrity sweep; no body topology, sketch dimensions or repeated full inspection."""
    rows=[];unknown=[]
    for c in live_components(d):
        for name in ('features','joints','asBuiltJoints'):
            try:
                entities=each(getattr(c,name))
            except Exception as exc:
                unknown.append({'component_token':c.entityToken,'collection':name,'message':str(exc)});continue
            for f in entities:
                try:
                    state=f.healthState;message=f.errorOrWarningMessage
                    if state in (adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState,adsk.fusion.FeatureHealthStates.WarningFeatureHealthState):
                        rows.append({'entity':f,'component':c,'state':state,'message':message,
                                     'severity':'error' if state==adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState else 'warning'})
                except Exception as exc:unknown.append({'component_token':c.entityToken,'collection':name,
                    'entity_token':getattr(f,'entityToken',None),'message':str(exc)})
    return rows,unknown

def health_report(d,selection,baseline=None):
    rows,unknown=health_snapshot(d);old=baseline[0] if baseline is not None else []
    groups={'new_errors':[],'relevant_preexisting':[],'unrelated_preexisting':[],'warnings':[]}
    for r in rows:
        existed=any(r['entity']==b['entity'] and r['state']==b['state'] and r['message']==b['message'] for b in old)
        info={'entity':advanced.ref(r['entity']),'component_token':r['component'].entityToken,'message':r['message'],'severity':r['severity']}
        if r['severity']=='warning':groups['warnings'].append(info);continue
        if baseline is not None and not existed:key='new_errors'
        elif selection.contains(r['component']):key='relevant_preexisting'
        else:key='unrelated_preexisting'
        groups[key].append(info)
    blocking=groups['new_errors']+groups['relevant_preexisting']
    old_unknown=baseline[1] if baseline is not None else []
    relevant_tokens={c.entityToken for c in selection.components()}
    unrelated_unknown=[u for u in unknown if u in old_unknown and u['component_token'] not in relevant_tokens]
    unknown=[u for u in unknown if u not in unrelated_unknown]
    evidence_rows,evidence_gaps=evidence(selection) if not selection.legacy else ([],[])
    evidence_status='fail' if any(e['status']=='fail' for e in evidence_rows) else 'unproven' if evidence_gaps else 'pass'
    return dict(groups,evidence=evidence_rows,evidence_gaps=evidence_gaps,evidence_status=evidence_status,validation_kind='feature_joint_integrity',feature_errors=blocking,inspection_gaps=unknown,unrelated_unavailable=unrelated_unknown,healthy=not blocking and not unknown and not groups['warnings'],
                validation_status='fail' if blocking else 'unproven' if unknown else 'pass',
                scope=selection.report(),approval_status='not_evaluated',
                limitation='Feature/joint integrity only. Functional evidence and approval are separate.')

class EditBoundary:
    """Prevent narrow calls; detect arbitrary Python changes afterward. No rollback/sandbox."""
    def __init__(self,d,selection,task,target):
        self.design=d;self.selection=selection;self.task=task or {};self.before=[];self.parameters={}
        self.occurrences=[]
        self.enabled=bool(task)
        if not task:return
        if task.get('version')!=VERSION:raise ValueError('task.version must be 1.0')
        for key in ('task_id','writer_id','baseline_id'):
            if not isinstance(task.get(key),str) or not task[key]:raise ValueError('task.'+key+' required')
        self.allowed=set(task.get('allowed_member_ids',[]));self.frozen=set(task.get('frozen_member_ids',[]))
        all_ids={m['id'] for m,c in selection.entries}
        if not self.allowed or not (self.allowed|self.frozen)<=all_ids:raise ValueError('Invalid permitted/frozen member set')
        if self.allowed & self.frozen:raise ValueError('Frozen and permitted edit sets overlap')
        for m,c in selection.entries:
            if m['maturity']=='frozen' and m['id'] in self.allowed:raise ValueError('Frozen part cannot be mutated; caller must resolve reopening authority first')
        self.require_component(target)
        self.before=[(c,c.revisionId,selection.member(c)) for c in live_components(d)]
        from . import preservation
        self.protected_states=[(c,preservation.component_state(c)) for c,_,m in self.before if not m or m['id'] not in self.allowed]
        self.parameters={p.name:p.expression for p in each(d.allParameters)}
        self.occurrences=[(o,o.component,tuple(o.transform2.asArray()),o.entityToken) for o in each(d.rootComponent.allOccurrences)]
    def require_component(self,c):
        if not self.enabled:return
        m=self.selection.member(c)
        if not m or m['id'] not in self.allowed:raise ValueError('Component outside permitted edit set')
    def require_parameter(self,name):
        if self.enabled and name not in self.task.get('allowed_parameter_names',[]):raise ValueError('Parameter outside permitted edit set')
    def post(self):
        if not self.enabled:return {'enforcement':'legacy_unbounded','approval_status':'not_evaluated'}
        from . import preservation
        changed=[];violations=[];attribution=[];current=live_components(self.design)
        for c,rev,m in self.before:
            valid=getattr(c,'isValid',False) and any(c==x for x in current)
            if not valid or c.revisionId!=rev:
                ident=m['id'] if m else None;changed.append(ident or c.entityToken)
                if not m or ident not in self.allowed:
                    old=next(s for obj,s in self.protected_states if obj==c)
                    comparison=preservation.compare(old,preservation.component_state(c)) if valid else {'status':'fail','changed':['deleted_component']}
                    attribution.append({'component_token':c.entityToken,'comparison':comparison,
                                        'classification':'revision_propagation' if comparison['status']=='pass' else 'changed_or_unproven'})
                    if comparison['status']!='pass':violations.append({'kind':'component','id':ident,'reason':'outside permitted set or frozen; '+comparison['status']})
        for c in current:
            if not any(c==old for old,_,_ in self.before):violations.append({'kind':'new_component','token':c.entityToken,'reason':'new definitions not permitted by contract 1.0; create components before acquiring task scope'})
        parameters={p.name:p for p in each(self.design.allParameters)}
        params={name:p.expression for name,p in parameters.items()};generated=[]
        for name in self.parameters.keys()|params.keys():
            if self.parameters.get(name)!=params.get(name) and name not in self.task.get('allowed_parameter_names',[]):
                owner=preservation.generated_owner(parameters[name]) if name not in self.parameters and name in parameters else None
                member=self.selection.member(owner) if owner else None
                if member and member['id'] in self.allowed:generated.append({'name':name,'owner_member_id':member['id']})
                else:violations.append({'kind':'parameter','name':name})
        now=each(self.design.rootComponent.allOccurrences)
        for o,c,matrix,token in self.occurrences:
            if not any(o==x for x in now) or preservation.placement_changed(matrix,o.transform2.asArray()):
                member=self.selection.member(c)
                if not member or member['id'] not in self.allowed:violations.append({'kind':'occurrence','token':token})
        for o in now:
            if not any(o==old for old,_,_,_ in self.occurrences):
                member=self.selection.member(o.component)
                if not member or member['id'] not in self.allowed:
                    violations.append({'kind':'new_occurrence','token':o.entityToken,'reason':'outside permitted set or frozen'})
        return {'changed_member_ids':changed,'violations':violations,'revision_attribution':attribution,'owned_generated_parameters':generated,
                'enforcement':'narrow_preconditions_and_posthoc_detection',
                'task_id':self.task['task_id'],'writer_id':self.task['writer_id'],'baseline_id':self.task['baseline_id'],
                'issue_id':self.task.get('issue_id'),'attempt':self.task.get('attempt'),
                'approval_reference':self.task.get('approval_reference'),'approval_status':'not_authenticated',
                'rollback_performed':False}

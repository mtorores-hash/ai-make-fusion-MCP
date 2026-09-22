"""Fill exact references from inspection before submitting. Do not guess tokens."""
def run(ctx):
    joint_ref={'token':'REPLACE_WITH_JOINT_TOKEN'}
    moving_body={'token':'REPLACE_WITH_MOVING_BODY_TOKEN','occurrence_token':'REPLACE_WITH_MOVING_OCCURRENCE'}
    fixed_body={'token':'REPLACE_WITH_FIXED_BODY_TOKEN','occurrence_token':'REPLACE_WITH_FIXED_OCCURRENCE'}
    joint=ctx.resolve(joint_ref)
    ctx.stage('idler_motion_check',0.1)
    samples=ctx.sample_motion(joint,list(range(0,91,5)),[(moving_body,fixed_body)],
                             motion='rotation',unit='deg',capture=True)
    clearances=[s['checks'][0]['distance']['distance_mm'] for s in samples['samples']]
    overlaps=[s for s in samples['samples'] if s['checks'][0]['interference']['count']]
    ctx.record('minimum_sampled_clearance_mm',min(clearances))
    ctx.record('poses_with_interference',len(overlaps))
    ctx.warn('Discrete 5-degree samples do not prove collision freedom between poses.')
    return samples

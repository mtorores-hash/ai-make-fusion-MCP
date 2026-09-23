"""Edit for your mechanism. Expected transforms must come from independent kinematics.

This intentionally refuses to run with unspecified transforms. Do not use measured
transform2 as its own expectation. All matrices use native cm in root assembly context.
"""
def run(ctx):
    joint=ctx.resolve({'token':'REPLACE_WITH_JOINT_TOKEN'})
    moving_occurrence=ctx.resolve({'token':'REPLACE_WITH_ROOT_CONTEXT_OCCURRENCE_TOKEN'})
    moving_body={'token':'REPLACE_WITH_MOVING_BODY_TOKEN','occurrence_token':'REPLACE_WITH_MOVING_OCCURRENCE'}
    fixed_body={'token':'REPLACE_WITH_FIXED_BODY_TOKEN','occurrence_token':'REPLACE_WITH_FIXED_OCCURRENCE'}
    def expected_world(position_deg):
        # Derive T_world = T_joint_frame * rotation(position) * T_body_in_joint_frame
        # from your independently established axis, pivot and reference placement.
        # Return [(moving_occurrence, T_world.asArray())]. Include other driven bodies too.
        raise NotImplementedError('Provide independent root-context kinematics for this mechanism')
    ctx.stage('idler_motion_check',0.1)
    samples=ctx.sample_motion(joint,list(range(0,91,5)),[(moving_body,fixed_body)],
                             motion='rotation',unit='deg',capture=True,
                             expected_world=expected_world,near_contact_mm=0.5,
                             max_depth=4,max_samples=300)
    ctx.record('minimum_sampled_clearance_mm',min(s['clearance_mm'] for s in samples['samples']))
    ctx.warn('Finite sampling leaves unresolved intervals; no continuous collision or physical fit claim.')
    return samples

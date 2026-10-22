"""Document-free workflow integration metadata; declarations are not test receipts."""


def describe():
    return {
        'version': '1.0',
        'caller_contract': '2.0',
        'scope_task_schema': '1.0',
        'engineering_schema': '1.0',
        'rules_version': '1.3.2',
        'qualification': 'implementation declaration; not native acceptance or approval',
        'controls': {
            'requirements_and_approvals': 'caller_owned',
            'dependency_completeness': 'caller_declared_not_inferred',
            'writer_guard': 'optimistic_single_use_token',
            'arbitrary_python': 'trusted_postcondition_detection_no_sandbox_or_rollback',
            'authoring_budgets': 'opt_in_task_authoring_no_policy_is_unbounded',
            'parameter_only_edit': 'explicit_boundary_and_zero_history_growth_budget_required',
            'appearance_evidence': 'caller_review_required_views_revision_and_capture_hashes',
            'solid_probe': 'declared_native_box_occupancy_not_attachment_or_strength_proof',
            'contradicted_evidence': 'explicit_contradicted_by_blocks_pass_and_reuse',
            'interrupted_authoring': 'observe_then_explicit_acknowledgement_preserves_budget',
            'geometry_checks': 'declared_scoped_checks_not_whole_part_certification',
            'finite_root_ligament_proof': 'not_implemented',
            'kept_tool_boolean_attribution': 'not_implemented',
            'mesh_package_correspondence': 'external_adapter_required',
            'effective_presets_and_emitted_paths': 'external_adapter_required',
            'physical_start_and_recording': 'external_authority_not_granted_by_mcp',
            'physical_results': 'caller_recorded_evidence',
        },
        'results': {
            'default': 'compact',
            'detail': 'immutable_report_pages_or_section_full',
            'omitted_detail_means_pass': False,
            'failed_job_authorizes_replay': False,
            'checked_export_is_manufacturing_approval': False,
        },
    }

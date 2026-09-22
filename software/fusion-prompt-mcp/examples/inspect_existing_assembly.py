"""Submit with checkpoint_before=False for this inspection-only example."""
def run(ctx):
    import json
    ctx.progress(0.1,'Inspect all component definitions, occurrences and topology')
    report=ctx.inspect(include_topology=True)
    path=ctx.path('full_assembly.json')
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    ctx.artifact(path)
    ctx.record('health',ctx.validate())
    return {'component_count':len(report['components']),'occurrence_count':len(report['occurrences']),
            'report':str(path),'warnings':report['warnings']}

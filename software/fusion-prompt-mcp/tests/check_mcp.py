"""Real MCP protocol test. Uses an isolated job directory; does not execute Fusion APIs."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def value(result):
    import json
    if result.structuredContent:
        return result.structuredContent
    return json.loads(result.content[0].text)

async def main():
    server=str(Path(__file__).resolve().parents[1]/'server.py')
    with tempfile.TemporaryDirectory() as home:
        bootstrap=('import sys; sys.path.insert(0,sys.argv[1]); import server; '
                   'from FusionPromptBridge.job_store import Store; '
                   'server.job_store=lambda:Store(sys.argv[2]); '
                   'from FusionPromptBridge.compatibility import identity; '
                   'original_call=server.call; '
                   'server.call=lambda operation,arguments=None: identity() if operation=="runtime_identity" else original_call(operation,arguments); '
                   'server.require_compatible_bridge=lambda:None; server.mcp.run(transport="stdio")')
        params=StdioServerParameters(command=sys.executable,args=['-c',bootstrap,str(Path(server).parent),home],
                                     env={'PYTHONPATH':os.pathsep.join(sys.path)})
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                result=await session.list_tools()
                expected={'inspect_design','new_design','rectangle_sketch','circle_sketch','extrude',
                          'set_parameter','export_model','fusion_capabilities','inspect_assembly','inspect_body',
                          'read_selection','fillet_edges','create_joint','run_model_script','job_status','job_result',
                          'list_jobs','cancel_job','inspect_full_assembly','select_geometry',
                          'measure_minimum_distance','check_interference','validate_model',
                          'get_modeling_rules','audit_modeling_hygiene','browse_cloud','inspect_document_state','cloud_operation','acquire_edit_token','release_edit_token','reconcile_cloud_job','retire_occurrences'}
                assert {t.name for t in result.tools}==expected
                rules=value(await session.call_tool('get_modeling_rules',{}))
                assert rules['rules_version']=='1.3.1' and 'Component first' in rules['text']
                capabilities=value(await session.call_tool('fusion_capabilities',{}))
                assert capabilities['compatible'] and capabilities['process_controls']['applies_to_loaded_pair']
                assert capabilities['process_controls']['rules_version']==rules['rules_version']
                assert capabilities['process_controls']['controls']['finite_root_ligament_proof']=='not_implemented'
                cached=value(await session.call_tool('get_modeling_rules',{'known_sha256':rules['sha256']}))
                assert cached['unchanged'] and 'text' not in cached
                source_tools={t.name:t for t in result.tools}
                for field in ('scope','task','accepted_reference_versions'):
                    assert field in source_tools['run_model_script'].inputSchema['properties']
                assert 'section' in source_tools['job_result'].inputSchema['properties']
                assert source_tools['inspect_document_state'].inputSchema['properties']['acquire_token']['default'] is False
                resource=await session.read_resource('fusion://modeling-rules')
                assert resource.contents[0].text==rules['text']
                assert (await session.call_tool('audit_modeling_hygiene',{})).isError
                assert (await session.call_tool('extrude',{'design_id':'test'})).isError
                assert (await session.call_tool('create_joint',{'design_id':'test','geometry_one':'a',
                            'geometry_two':'b','kind':'invalid'})).isError
                request={'operation_id':'mcp-test','document_id':'test','component_token':'root','units':'mm',
                         'script':'def run(ctx): return {"ok":True}'}
                first=await session.call_tool('run_model_script',request); assert not first.isError
                job=value(first); ident=job['job_id']; assert job['status']=='queued'
                duplicate=value(await session.call_tool('run_model_script',request)); assert duplicate['job_id']==ident
                conflict=await session.call_tool('run_model_script',dict(request,script='def run(ctx): return 2'))
                assert conflict.isError
                status=value(await session.call_tool('job_status',{'job_id':ident})); assert status['status']=='queued'
                cancelled=value(await session.call_tool('cancel_job',{'job_id':ident})); assert cancelled['status']=='cancelled'
                compact=value(await session.call_tool('job_result',{'job_id':ident}))
                assert compact['details_omitted'] and compact['detail']['immutable']
                full=value(await session.call_tool('job_result',{'job_id':ident,'section':'full'}))
                assert 'result' in full and full['status']=='cancelled'
                page=value(await session.call_tool('job_result',{'report_id':compact['detail']['report_id'],'section':'raw','limit':32768}))
                import hashlib
                assert hashlib.sha256(page['text'].encode()).hexdigest()==compact['detail']['sha256']
                same=value(await session.call_tool('job_result',{'job_id':ident,'after_revision':compact['revision']}))
                assert same['unchanged']
                readonly=dict(request,operation_id='read-test',mode='read_only',checkpoint_before=False,
                              script='def run(ctx): return ctx.inspect(False)')
                assert not (await session.call_tool('run_model_script',readonly)).isError
                assert (await session.call_tool('run_model_script',dict(readonly,operation_id='bad-read',
                        script='def run(ctx): return ctx.design.computeAll()'))).isError
                cloud_request=dict(operation_id='cloud-test',action='ensure_project',arguments={'hub_id':'h','name':'Test'})
                cloud=value(await session.call_tool('cloud_operation',cloud_request))
                assert cloud['status']=='queued'
                assert value(await session.call_tool('cloud_operation',cloud_request))['job_id']==cloud['job_id']
                assert (await session.call_tool('cloud_operation',dict(cloud_request,action='delete'))).isError
                print('PASS: real STDIO initialize; 32 tools; rules and document-free process controls; validation; isolated enqueue/status; duplicate protection; cancellation. Native identity/handshake explicitly stubbed in this offline harness; not native acceptance.')

asyncio.run(main())

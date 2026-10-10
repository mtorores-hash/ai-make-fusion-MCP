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
                   'server.job_store=lambda:Store(sys.argv[2]); server.mcp.run(transport="stdio")')
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
                assert rules['rules_version']=='1.1.0' and 'Component first' in rules['text']
                cached=value(await session.call_tool('get_modeling_rules',{'known_sha256':rules['sha256']}))
                assert cached['unchanged'] and 'text' not in cached
                source_tools={t.name:t for t in result.tools}
                for field in ('scope','task','accepted_reference_versions'):
                    assert field in source_tools['run_model_script'].inputSchema['properties']
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
                print('PASS: MCP initialize; 32 tools; modeling rules tool/resource; validation; persistent enqueue/status; duplicate protection; cancellation')

asyncio.run(main())

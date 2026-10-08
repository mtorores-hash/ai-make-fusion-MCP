"""Cloud workflow regression tests with API doubles, never native Fusion acceptance."""
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_advanced import Node, Collection, core, fusion
from FusionPromptBridge import cloud
from FusionPromptBridge.job_store import Store

class CloudTests(unittest.TestCase):
    def setUp(self):
        cloud.reset(); self.addCleanup(cloud.reset)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name)
        self.file=self.make_file()
        self.component=Node(name='housing',revisionId='r1')
        self.design=Node(allComponents=Collection([self.component]),allParameters=Collection())
        self.doc=Node(name='housing',isModified=False,isSaved=True,dataFile=self.file,
                      allDocumentReferences=Collection(),documentReferences=Collection(),save=Mock(return_value=True))
        self.app=Node(activeDocument=self.doc)
    def make_file(self,**changes):
        values=dict(id='stable-file-id',name='housing',versionId='version-1',versionNumber=1,
                    latestVersionNumber=1,isComplete=True,isReadOnly=False,isInUse=False,
                    parentProject=Node(id='p'),parentFolder=Node(id='folder'),refresh=Mock(return_value=True))
        values.update(changes);return Node(**values)
    def token(self):return cloud.inspect_state(self.app,self.design,'doc')['edit_token']
    def guard(self,token,**kw):return cloud.require_edit(self.app,self.design,'doc',token,**kw)
    def run_job(self,action,args):
        job=self.store.submit_cloud(dict(operation_id='op',action=action,arguments=args))
        cloud.start(self.store,self.store.claim('owner'),self.app,lambda:self.design,lambda:'doc')
        return job['job_id']
    def test_refresh_uses_required_synchronous_handler_and_fails_closed(self):
        self.token();self.file.refresh.assert_called_once_with(None)
        self.file.refresh.return_value=False
        with self.assertRaisesRegex(RuntimeError,'refresh failed'):self.token()
    def test_reinspection_invalidates_previous_token_even_without_edit(self):
        old=self.token();self.token()
        with self.assertRaisesRegex(ValueError,'edit_token'):self.guard(old)
    def test_first_save_uses_explicit_name_and_destination(self):
        self.doc.isSaved=False;self.doc.dataFile=None;self.doc.saveAs=Mock(return_value=True)
        destination=Node(id='parts')
        with patch.object(cloud,'destination',return_value=destination):
            ident=self.run_job('save',{'document_id':'doc','edit_token':self.token(),'name':'housing'})
        self.doc.saveAs.assert_called_once_with('housing',destination,'','')
        self.doc.dataFile=self.file;cloud.tick(self.store)
        self.assertEqual(self.store.status(ident)['status'],'succeeded')
    def test_component_copy_waits_for_future_and_does_not_replace_source(self):
        core.UploadStates=Node(UploadFailed=2,UploadFinished=1)
        future=Node(uploadState=0,dataFile=self.file)
        component=Node(saveCopyAs=Mock(return_value=future));destination=Node(id='parts')
        with patch.object(cloud,'destination',return_value=destination), \
             patch.object(cloud.advanced,'resolve',return_value=component), \
             patch.object(cloud.advanced,'editable'),patch.object(fusion,'Component',create=True):
            ident=self.run_job('save_component',{'document_id':'doc','edit_token':self.token(),
                                                'component_token':'housing','name':'housing'})
        component.saveCopyAs.assert_called_once_with('housing',destination,'','')
        cloud.tick(self.store);self.assertEqual(self.store.status(ident)['status'],'running')
        future.uploadState=1;cloud.tick(self.store)
        self.assertEqual(self.store.status(ident)['status'],'succeeded');self.doc.save.assert_not_called()
        self.assertIn('NOT replaced',self.store.result(ident)['result']['note'])
    def test_insert_requires_same_project_before_api_mutation(self):
        part=self.make_file(id='part',parentProject=Node(id='other'))
        self.app.data=Node(findFileById=lambda _:part)
        self.design.rootComponent=Node(occurrences=Node(addByInsert=Mock()))
        ident=self.run_job('insert',{'document_id':'doc','edit_token':self.token(),
                                    'version_id':'version-1','expected_version':1,'transform_cm':[1]*16})
        self.assertEqual(self.store.status(ident)['status'],'failed')
        self.design.rootComponent.occurrences.addByInsert.assert_not_called()
    def test_dirty_to_dirty_edit_is_detected(self):
        self.doc.isModified=True; token=self.token();self.component.revisionId='r2'
        with self.assertRaisesRegex(ValueError,'changed since inspection'):self.guard(token)
    def test_acknowledged_unsaved_state_is_preserved(self):
        self.doc.isModified=True;self.guard(self.token());self.doc.save.assert_not_called()
        self.assertTrue(self.doc.isModified)
    def test_token_is_single_use(self):
        token=self.token();self.guard(token)
        with self.assertRaisesRegex(ValueError,'edit_token'):self.guard(token)
    def test_cloud_version_change_blocks(self):
        token=self.token();self.file.latestVersionNumber=2
        with self.assertRaisesRegex(ValueError,'changed since inspection'):self.guard(token)
    def test_stale_readonly_processing_and_other_editor_fail_closed(self):
        for key,value in [('latestVersionNumber',2),('isReadOnly',True),('isComplete',False),('isInUse',True)]:
            with self.subTest(key=key):
                self.doc.dataFile=self.make_file(**{key:value})
                with self.assertRaises(ValueError):self.guard(self.token())
    def test_reference_dirty_and_stale_checks(self):
        ref=Node(dataFile=self.make_file(),version=1,isOutOfDate=True,referencedDocument=None)
        self.doc.allDocumentReferences=Collection([ref])
        with self.assertRaisesRegex(ValueError,'out of date'):self.guard(self.token())
        self.guard(self.token(),allow_stale_refs=True)
        ref.referencedDocument=Node(isModified=True)
        with self.assertRaisesRegex(ValueError,'unsaved'):self.guard(self.token(),allow_stale_refs=True)
    def test_cloud_checkpoint_preserves_identity_and_reference_versions(self):
        self.doc.allDocumentReferences=Collection([Node(dataFile=self.make_file(id='child'),version=1,
                                                       isOutOfDate=False,referencedDocument=None)])
        record=cloud.cloud_checkpoint(self.app,self.design,'doc')
        self.assertEqual(record['file']['id'],'stable-file-id')
        self.assertEqual(record['references'][0]['id'],'child')
        self.assertFalse(record['self_contained_archive']);self.doc.save.assert_not_called()
    def test_checkpoint_never_saves_unsaved_work_implicitly(self):
        self.doc.isModified=True
        with self.assertRaisesRegex(ValueError,'completed cloud save'):cloud.cloud_checkpoint(self.app,self.design,'doc')
        self.doc.save.assert_not_called()
    def test_duplicate_operation_and_changed_content(self):
        req=dict(operation_id='op',action='ensure_project',arguments={'hub_id':'h','name':'a'})
        one=self.store.submit_cloud(req);two=self.store.submit_cloud(req)
        self.assertEqual(one['job_id'],two['job_id'])
        with self.assertRaisesRegex(ValueError,'different content'):self.store.submit_cloud(dict(req,arguments={'name':'b'}))
    def test_restart_interrupts_cloud_job_without_replay(self):
        job=self.store.submit_cloud(dict(operation_id='op',action='save',arguments={}))
        self.store.claim('owner');self.store.recover()
        self.assertEqual(self.store.status(job['job_id'])['status'],'interrupted');self.assertIsNone(self.store.claim('new'))
    def test_save_is_pending_until_exact_new_version_complete(self):
        self.doc.isModified=True
        ident=self.run_job('save',{'document_id':'doc','edit_token':self.token()})
        self.assertEqual(self.store.status(ident)['status'],'running');self.assertTrue(self.store.pending())
        cloud.tick(self.store);self.assertEqual(self.store.status(ident)['status'],'running')
        self.doc.dataFile=self.make_file(versionNumber=2,latestVersionNumber=2,versionId='v2',isComplete=False)
        cloud.tick(self.store);self.assertEqual(self.store.status(ident)['status'],'running')
        self.doc.dataFile.isComplete=True;cloud.tick(self.store)
        result=self.store.result(ident)
        self.assertEqual(result['status'],'succeeded');self.assertTrue(result['result']['cloud_complete'])
        self.assertEqual(result['result']['file']['version'],2);self.doc.save.assert_called_once()
    def test_save_duplicate_does_not_call_api_again(self):
        self.doc.isModified=True;args={'document_id':'doc','edit_token':self.token()}
        ident=self.run_job('save',args)
        self.assertEqual(self.store.submit_cloud(dict(operation_id='op',action='save',arguments=args))['job_id'],ident)
        self.doc.save.assert_called_once()
    def test_save_existing_rejects_relocation(self):
        ident=self.run_job('save',{'document_id':'doc','edit_token':self.token(),'name':'different'})
        self.assertEqual(self.store.status(ident)['status'],'failed');self.doc.save.assert_not_called()
    def test_cancel_upload_reports_uncertainty(self):
        self.doc.isModified=True;ident=self.run_job('save',{'document_id':'doc','edit_token':self.token()})
        self.store.cancel(ident);cloud.tick(self.store)
        result=self.store.result(ident)
        self.assertEqual(result['status'],'cancelled');self.assertFalse(result['result']['cloud_complete'])
        self.assertIn('may still complete',result['result']['message'])
    def test_future_failure_is_reported(self):
        core.UploadStates=Node(UploadFailed=2,UploadFinished=1)
        job=self.store.submit_cloud(dict(operation_id='op',action='save_component',arguments={}))
        self.store.claim('owner')
        cloud._pending[job['job_id']]={'future':Node(uploadState=2),'started':cloud.time.monotonic(),'result':{}}
        cloud.tick(self.store);result=self.store.result(job['job_id'])
        self.assertEqual(result['status'],'failed');self.assertIn('upload failed',result['result']['message'])
    def test_names_reuse_unique_existing_and_reject_ambiguity(self):
        item=Node(id='p',name='Test');collection=Collection([item]);collection.add=Mock()
        self.assertIs(cloud.ensure_named(collection,'Test'),item);collection.add.assert_not_called()
        with self.assertRaisesRegex(ValueError,'Ambiguous'):cloud.ensure_named(Collection([item,item]),'Test')
    def test_open_refuses_dirty_target_without_closing(self):
        self.doc.isModified=True;self.app.documents=Collection([self.doc]);self.app.documents.open=Mock()
        self.app.data=Node(findFileById=lambda _:self.file)
        ident=self.run_job('open',{'version_id':'version-1','expected_version':1})
        self.assertEqual(self.store.status(ident)['status'],'failed');self.app.documents.open.assert_not_called()
        self.doc.save.assert_not_called()
    def test_selected_reference_update_pins_expected_version(self):
        child=self.make_file(id='child',latestVersionNumber=2)
        ref=Node(dataFile=child,version=1,isOutOfDate=True,referencedDocument=None)
        self.doc.documentReferences=self.doc.allDocumentReferences=Collection([ref])
        ident=self.run_job('update_reference',{'document_id':'doc','edit_token':self.token(),
                                              'file_id':'child','expected_latest_version':2})
        result=self.store.result(ident)
        self.assertEqual(result['status'],'succeeded');self.assertEqual(ref.version,2)
        self.assertEqual(result['result']['checkpoint']['references'][0]['referenced_version'],1)
        self.assertTrue(result['result']['requires_save'])
    def test_wrong_document_never_saves(self):
        ident=self.run_job('save',{'document_id':'other','edit_token':self.token()})
        self.assertEqual(self.store.status(ident)['status'],'failed');self.doc.save.assert_not_called()

if __name__=='__main__':unittest.main()

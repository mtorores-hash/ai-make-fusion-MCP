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
        self.app=Node(activeDocument=self.doc,data=Node(findFileById=lambda _:self.file))
    def make_file(self,**changes):
        values=dict(id='stable-file-id',name='housing',versionId='version-1',versionNumber=1,
                    latestVersionNumber=1,isComplete=True,isReadOnly=False,isInUse=False,
                    parentProject=Node(id='p'),parentFolder=Node(id='folder'),refresh=Mock(return_value=True))
        values.update(changes);file=Node(**values)
        file.latestVersion=file if file.versionNumber==file.latestVersionNumber else self.make_file(
            id=file.id,versionNumber=file.latestVersionNumber,latestVersionNumber=file.latestVersionNumber,versionId='v'+str(file.latestVersionNumber))
        return file
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
    def test_reinspection_preserves_unchanged_writer_token(self):
        old=self.token();self.assertEqual(old,self.token());self.guard(old)
    def test_first_save_uses_explicit_name_and_destination(self):
        self.doc.isSaved=False;self.doc.dataFile=None;self.doc.saveAs=Mock(return_value=True)
        destination=Node(id='folder')
        with patch.object(cloud,'destination',return_value=destination):
            ident=self.run_job('save',{'document_id':'doc','edit_token':self.token(),'name':'housing'})
        self.doc.saveAs.assert_called_once_with('housing',destination,'','')
        self.doc.dataFile=self.file;cloud.tick(self.store)
        self.assertEqual(self.store.status(ident)['status'],'succeeded')
    def test_component_copy_waits_for_future_and_does_not_replace_source(self):
        core.UploadStates=Node(UploadFailed=2,UploadFinished=1)
        future=Node(uploadState=0,dataFile=self.file)
        component=Node(saveCopyAs=Mock(return_value=future));destination=Node(id='folder')
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

    def test_observers_do_not_invalidate_writer_and_second_writer_cannot_take_over(self):
        first=cloud.inspect_state(self.app,self.design,'doc',True,'writer')
        observed=cloud.inspect_state(self.app,self.design,'doc',False)
        self.assertNotIn('edit_token',observed)
        with self.assertRaisesRegex(ValueError,'Another writer'):cloud.inspect_state(self.app,self.design,'doc',True,'other')
        cloud.require_edit(self.app,self.design,'doc',first['edit_token'],writer_id='writer')
        with self.assertRaises(ValueError):cloud.require_edit(self.app,self.design,'doc',first['edit_token'],writer_id='writer')
    def test_accepted_pin_survives_available_update_but_actual_change_rejects(self):
        child=self.make_file(id='child',latestVersionNumber=2)
        ref=Node(dataFile=child,version=1,isOutOfDate=True,referencedDocument=None)
        self.doc.allDocumentReferences=Collection([ref]);pins={'child':1}
        token=cloud.inspect_state(self.app,self.design,'doc',True,'writer',pins)['edit_token']
        child.latestVersionNumber=3
        cloud.require_edit(self.app,self.design,'doc',token,accepted_reference_versions=pins,writer_id='writer')
        token=cloud.inspect_state(self.app,self.design,'doc',True,'writer',pins)['edit_token']
        ref.version=2
        with self.assertRaisesRegex(ValueError,'changed since inspection'):
            cloud.require_edit(self.app,self.design,'doc',token,accepted_reference_versions=pins,writer_id='writer')
    def test_historical_read_allowed_but_target_overwrite_blocked(self):
        old=self.make_file(versionNumber=1,latestVersionNumber=2)
        self.app.data=Node(findFileById=lambda _:old)
        self.assertIs(cloud.get_file(self.app,{'version_id':'old','expected_version':1,'allow_historical':True}),old)
        self.doc.dataFile=old
        with self.assertRaisesRegex(ValueError,'Historical inspection'):self.guard(self.token())
    def test_dirty_stale_save_and_two_sequential_reference_updates(self):
        refs=[Node(dataFile=self.make_file(id='child'+str(i),latestVersionNumber=2),version=1,
                   isOutOfDate=True,referencedDocument=None) for i in (1,2)]
        self.doc.allDocumentReferences=self.doc.documentReferences=Collection(refs)
        self.doc.isModified=True
        def execute(action,op,**extra):
            pins={r.dataFile.id:r.version for r in refs}
            token=cloud.inspect_state(self.app,self.design,'doc',True,'writer',pins)['edit_token']
            args=dict(document_id='doc',edit_token=token,writer_id='writer',accepted_reference_versions=pins,**extra)
            job=self.store.submit_cloud(dict(operation_id=op,action=action,arguments=args))
            cloud.start(self.store,self.store.claim('owner'),self.app,lambda:self.design,lambda:'doc')
            return job['job_id']
        def save(op):
            previous=self.doc.dataFile.versionNumber;ident=execute('save',op)
            self.assertEqual(self.store.status(ident)['status'],'running')
            self.doc.isModified=False
            self.doc.dataFile=self.make_file(versionNumber=previous+1,latestVersionNumber=previous+1,versionId='v'+str(previous+1))
            cloud.tick(self.store);self.assertEqual(self.store.status(ident)['status'],'succeeded')
        save('preserve-manual')
        for i,ref in enumerate(refs):
            ident=execute('update_reference','update-'+str(i),file_id=ref.dataFile.id,expected_latest_version=2)
            result=self.store.result(ident)
            self.assertEqual(result['status'],'succeeded',result)
            self.assertEqual(ref.version,2)
            self.doc.isModified=True;save('save-update-'+str(i))
        self.assertEqual(self.doc.dataFile.versionNumber,4)
    def test_uncertain_save_blocks_next_mutation_and_late_version_is_reconciled(self):
        self.doc.isModified=True;ident=self.run_job('save',{'document_id':'doc','edit_token':self.token()})
        self.store.cancel(ident);cloud.tick(self.store)
        with self.assertRaisesRegex(ValueError,'reconciliation'):self.store.assert_no_uncertain_cloud()
        late=self.make_file(versionNumber=2,latestVersionNumber=2,versionId='v2')
        self.app.data=Node(findFileById=lambda _:late)
        observed=cloud.reconcile(self.store,self.app,ident,'v2')
        self.assertTrue(observed['reconciliation_required'])
        with self.assertRaises(ValueError):self.store.assert_no_uncertain_cloud()
        cloud.reconcile(self.store,self.app,ident,'v2','Checked Fusion history and the intended edits in this version')
        self.store.assert_no_uncertain_cloud()
        self.assertEqual(self.store.status(ident)['status'],'cancelled')
        self.assertFalse(self.store.result(ident)['result']['uncertain']);self.doc.save.assert_called_once()
    def test_reconciliation_rejects_wrong_file_and_wrong_version(self):
        self.doc.isModified=True;ident=self.run_job('save',{'document_id':'doc','edit_token':self.token()})
        self.store.cancel(ident);cloud.tick(self.store)
        for file in [self.make_file(id='wrong',versionNumber=2,latestVersionNumber=2),self.make_file()]:
            self.app.data=Node(findFileById=lambda _:file)
            with self.assertRaises(ValueError):cloud.reconcile(self.store,self.app,ident,'candidate','checked')
    def test_completed_pin_set_does_not_bypass_dirty_referenced_document(self):
        ref=Node(dataFile=self.make_file(id='child',latestVersionNumber=2),version=1,isOutOfDate=True,
                 referencedDocument=Node(isModified=True))
        self.doc.allDocumentReferences=Collection([ref]);pins={'child':1}
        token=cloud.inspect_state(self.app,self.design,'doc',True,'writer',pins)['edit_token']
        with self.assertRaisesRegex(ValueError,'unsaved'):
            cloud.require_edit(self.app,self.design,'doc',token,accepted_reference_versions=pins,writer_id='writer')

if __name__=='__main__':unittest.main()

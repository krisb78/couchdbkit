# -*- coding: utf-8 -
#
# This file is part of couchdbkit released under the MIT license. 
# See the NOTICE for more information.
#
__author__ = 'benoitc@e-engura.com (Benoît Chesneau)'

import base64
import os
import shutil
import tempfile
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from restkit import ResourceNotFound, RequestFailed

from couchdbkit import *
from couchdbkit.utils import *


class LoaderTestCase(unittest.TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.template_dir = os.path.join(os.path.dirname(__file__), 'data/app-template')
        self.app_dir = os.path.join(self.tempdir, "couchdbkit-test")
        shutil.copytree(self.template_dir, self.app_dir)
        write_content(os.path.join(self.app_dir, "_id"),
                "_design/couchdbkit-test")
        self.server = Server()
        self.db = self.server.create_db('couchdbkit_test')
        
    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        os.rmdir(self.tempdir)
        del self.server['couchdbkit_test']
                
    def testGetDoc(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue(isinstance(design_doc, dict))
        self.assertTrue('_id' in design_doc)
        self.assertTrue(design_doc['_id'] == "_design/couchdbkit-test")
        self.assertTrue('lib' in design_doc)
        self.assertTrue('helpers' in design_doc['lib'])
        self.assertTrue('template' in design_doc['lib']['helpers'])
        
    def testGetDocView(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue('views' in design_doc)
        self.assertTrue('example' in design_doc['views'])
        self.assertTrue('map' in design_doc['views']['example'])
        self.assertTrue('emit' in design_doc['views']['example']['map'])
        
    def testGetDocCouchApp(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue('couchapp' in design_doc)
        
    def testGetDocManifest(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue('manifest' in design_doc['couchapp'])
        self.assertTrue('lib/helpers/template.js' in design_doc['couchapp']['manifest'])
        self.assertTrue('foo/' in design_doc['couchapp']['manifest'])
        self.assertTrue(len(design_doc['couchapp']['manifest']) == 16)
        
        
    def testGetDocAttachments(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue('_attachments' in design_doc)
        self.assertTrue('index.html' in design_doc['_attachments'])
        self.assertTrue('style/main.css' in design_doc['_attachments'])
        
        content = design_doc['_attachments']['style/main.css']
        self.assertTrue(base64.b64decode(content['data']) == "/* add styles here */")
        
    def testGetDocSignatures(self):
        l = FileSystemDocsLoader(self.tempdir)
        design_doc = l.get_docs()[0]
        self.assertTrue('signatures' in design_doc['couchapp'])
        self.assertTrue(len(design_doc['couchapp']['signatures']) == 2)
        self.assertTrue('index.html' in design_doc['couchapp']['signatures'])
        signature =  design_doc['couchapp']['signatures']['index.html']
        fsignature = sign_file(os.path.join(self.app_dir, '_attachments/index.html'))
        self.assertTrue(signature==fsignature)
        
    def _sync(self, atomic=True):
        l = FileSystemDocsLoader(self.tempdir)
        l.sync(self.db, atomic=atomic, verbose=True)
        # any design doc created ?
        design_doc = None
        try:
            design_doc = self.db['_design/couchdbkit-test']
        except ResourceNotFound:
            pass
        self.assertTrue(design_doc is not None)
        

        # should create view
        self.assertTrue('function' in design_doc['views']['example']['map'])
        # should not create empty views
        self.assertFalse('empty' in design_doc['views'])
        self.assertFalse('wrong' in design_doc['views'])
        
        # should use macros
        self.assertTrue('stddev' in design_doc['views']['example']['map'])
        self.assertTrue('ejohn.org' in design_doc['shows']['example-show'])
        
        # should have attachments
        self.assertTrue('_attachments' in design_doc)
        
        # should create index
        self.assertTrue(design_doc['_attachments']['index.html']['content_type'] == 'text/html')
        
        # should create manifest
        self.assertTrue('foo/' in design_doc['couchapp']['manifest'])
        
        # should push and macro the doc shows
        self.assertTrue('Generated CouchApp Form Template' in design_doc['shows']['example-show'])
        
        # should push and macro the view lists
        self.assertTrue('Test XML Feed' in design_doc['lists']['feed'])
        
        # should allow deeper includes
        self.assertFalse('"helpers"' in design_doc['shows']['example-show'])
        
        # deep require macros
        self.assertFalse('"template"' in design_doc['shows']['example-show'])
        self.assertTrue('Resig' in design_doc['shows']['example-show'])
        
    def testSync(self):
        self._sync()
        
    def testSyncNonAtomic(self):
        self._sync(atomic=False)
        
if __name__ == '__main__':
    unittest.main()
        
        



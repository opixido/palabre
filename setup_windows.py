#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from distutils.core import setup
import py2exe
import glob

setup(name = "Palabre",
      console=[{"script":"Palabre.py"
               ,
               "icon_resources": [(1, "palabre.ico")] }],
      
      version = "0.6b",
      description = "XML Socket Python Server",
      long_description = "Flash XML Multiuser Socket Server :-)",
      author = "Célio Conort",
      author_email = "palabre-dev@lists.tuxfamily.org",
      url = "http://palabre.gavroche.net/",
      license = "GPL, see COPYING for details",
      data_files=[('etc', ['etc/palabre.conf']),('modules',glob.glob('modules\*.py'))],
      options={"py2exe": {"packages": ["adodb"]}}
      

     )

#    packages=['adodb'],
#py_modules = ['adodb.adodb','adodb.adodb_mysql','MySQLdb',
#'adodb.adodb_access','adodb.adodb_mxodbc','adodb_mxoracle','adodb_oci8','adodb_odbc','adodb_odbc_mssql', 'adodb_postgres','adodb_sqlite','adodb_vfp']
#      ,packages=['MySQLdb']

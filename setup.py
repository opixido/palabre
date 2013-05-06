#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from distutils.core import setup


setup(name = "palabre",
      version = "0.6b",
      description = "XML Socket Python Server",
      long_description = "Flash XML Multiuser Socket Server",
      author = "Célio Conort",
      author_email = "palabre-dev@lists.tuxfamily.org",
      url = "http://palabre.gavroche.net/",
      license = "GPL, see COPYING for details",
      platforms = "Linux",
      packages = ["palabre","modules"],
      scripts = ["scripts/palabre","setup.py"],
      data_files = [('',['Palabre.py']),
                    ("/etc", ["etc/palabre.conf"]        
                     ),
                    ("doc",["doc/README.txt"]),
                    ("./",["AUTHORS","COPYING","MANIFEST","MANIFEST.in","PKG-INFO"]),
		    ("/usr/local/share/doc/palabre", ["doc/README.txt"])
		 		   ]
     )


# -*- coding: utf-8 -*-

# Barom -- A utility for tracking altitude/predicting weather
#
# Copyright (C) 2010 Benjamin Deering <ben_deering@swissmail.org>
# http://jeepingben.homelinux.net/wax/
#
# This file is part of barom.
#
# barom is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Wax-chooser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import glob
from barom.const import APP_VERSION
from distutils.core import setup

def main():
    image_files = glob.glob("data/images/*.png")
    setup(name         = 'barom',
          version      = APP_VERSION,
          description  = 'A utility for tracking altitude/predicting weather',
          author       = 'Benjamin Deering',
          author_email = 'ben_deering@swissmail.org',
          url          = 'http://jeepingben.homelinux.net/barom/',
          classifiers  = [
            'Development Status :: 5 - Production/Stable',
            'Environment :: X11 Applications',
            'Intended Audience :: End Users/Phone UI',
            'License :: GNU General Public License (GPL)',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Topic :: Desktop Environment',
            ],
          packages     = ['barom'],
          scripts      = ['barom/barom'],
          data_files   = [
            ('share/applications', ['data/barom.desktop']),
            ('share/pixmaps', ['data/barom.png']),
            ('share/barom', ['README']),
	    ('share/barom/images', image_files )
            ]
          )

if __name__ == '__main__':
    main()

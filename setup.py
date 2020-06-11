#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS1-SRW'
VERSION = '1.1.46'
ISRELEASED = False

DESCRIPTION = 'SRW in OASYS'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Luca Rebuffi'
AUTHOR_EMAIL = 'lrebuffi@anl.gov'
URL = 'https://github.com/lucarebuffi/OASYS-SRW'
DOWNLOAD_URL = 'https://github.com/lucarebuffi/OASYS-SRW'
LICENSE = 'GPLv3'

KEYWORDS = (
    'waveoptics',
    'simulator',
    'oasys1',
)

CLASSIFIERS = (
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'oasys1>=1.2.35',
    'wofrysrw>=1.1.6',
    'scikit-image'
)


PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.srw.widgets.light_sources":["icons/*.png", "icons/*.jpg", "misc/*.png"],
    "orangecontrib.srw.widgets.optical_elements":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.tools":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.native":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.loop_management": ["icons/*.png", "icons/*.jpg"],
    "orangecontrib.srw.widgets.scanning": ["icons/*.png", "icons/*.jpg"],
}

NAMESPACE_PACAKGES = ["orangecontrib", "orangecontrib.srw", "orangecontrib.srw.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("SRW = orangecontrib.srw", ),
    'oasys.widgets' : (
        "SRW Light Sources = orangecontrib.srw.widgets.light_sources",
        "SRW Optical Elements = orangecontrib.srw.widgets.optical_elements",
        "SRW Tools = orangecontrib.srw.widgets.tools",
        "SRW Basic Loops = orangecontrib.srw.widgets.loop_management",
        "SRW Scanning Loops = orangecontrib.srw.widgets.scanning",
        "SRW Native = orangecontrib.srw.widgets.native",
    ),
    'oasys.menus' : ("srwmenu = orangecontrib.srw.menu",)
}

if __name__ == '__main__':
    try:
        import PyMca5, PyQt4

        raise NotImplementedError("This version of SRW doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: https://www.aps.anl.gov/Science/Scientific-Software/OASYS")
    except:
        setup(
              name = NAME,
              version = VERSION,
              description = DESCRIPTION,
              long_description = LONG_DESCRIPTION,
              author = AUTHOR,
              author_email = AUTHOR_EMAIL,
              url = URL,
              download_url = DOWNLOAD_URL,
              license = LICENSE,
              keywords = KEYWORDS,
              classifiers = CLASSIFIERS,
              packages = PACKAGES,
              package_data = PACKAGE_DATA,
              setup_requires = SETUP_REQUIRES,
              install_requires = INSTALL_REQUIRES,
              entry_points = ENTRY_POINTS,
              namespace_packages=NAMESPACE_PACAKGES,
              include_package_data = True,
              zip_safe = False,
              )

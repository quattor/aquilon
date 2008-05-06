"""
 Terminology note: it's *packages* that reside in
subdirectories, and require an __init__.py file.  Modules are simply
*.py files that reside somewhere along the Python path.  Packages are a
way to group related modules together.

"""
#import os,sys
#thisdir = os.path.dirname(__file__)
#libdir  = os.path.join(thisdir,'../..')
#if libdir not in sys.path:
#    sys.path.insert(0,libdir)

#__all__ = []
#for subpackage in ['utils', 'DB']:
#    try:
#        exec 'import ' + subpackage
#        __all__.append( subpackage )
#    except ImportError:
#        pass

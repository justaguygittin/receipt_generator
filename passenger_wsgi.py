import sys
import os

project_home = '/home/gsrikari/SE/receipt_generator'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
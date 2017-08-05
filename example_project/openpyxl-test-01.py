# -*- coding: utf-8 -*-
import os,sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')
django.setup()

from django.conf import settings
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import os
import re
from io import BytesIO

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
	
static_root = getattr( settings, 'STATIC_ROOT', '' )
static_url = getattr( settings, 'STATIC_URL', '' )
app_url = 'http://reportbot.5tring.com:4000'
tmp_root = '/media/djmedia/mr_forgot/tmp'
xlsx_root = 'xlsx'
filename_in = 'cm-template.xlsx'
filename_out = 'test-photo.xlsx'
fn_in = os.path.join(static_root,xlsx_root,filename_in)
url_in = app_url + os.path.join( static_url, xlsx_root,filename_in )
fn_out = os.path.join(tmp_root,xlsx_root,filename_out)
os.path.exists(fn_in)

print( 'url_in='+url_in)
image_data = BytesIO(urlopen(url_in).read())
#ws.insert_image('B2', img_url, {'image_data':image_data})

img_url = "http://reportbot.5tring.com:4000/media/photologue/photos/image1.png"

wb = load_workbook( image_data )

ws = wb.active

i = 0
for row in ws.rows:
 for cell in row:
   if cell.value:
    print(cell.column+ str(cell.row) + ":" + cell.value)
    i = i + 1
	
fn_out_path, filename = os.path.split(fn_out)
print( "fn_out_path={}, filename={}".format( fn_out_path, filename ) )
if not os.path.exists( fn_out_path ): 
    os.mkdir( fn_out_path )

# Insert Logo on every page
print ('insert image {}'.format( img_url ) )
image_data = BytesIO(urlopen(img_url).read())
img_width = 151
img_height = 134
img = Image( image_data, size=[img_width,img_height] )
print(dir(img.drawing))
#img.drawing.width = 152
#img.drawing.height = 134
ws.add_image( img, 'B1' )

# regex find all template tags
# replace tags with database field
from photologue.models import PhotoGroup, Photo
q_pg = PhotoGroup.objects.get( id = 6 )
fields_pg = q_pg._meta.get_fields()

pattern = r'^{{(?P<name>\w+)}}$'
non_db_field = ['page_num', 'page_total','serial_no']
for cell in ws.get_cell_collection():
    if cell.value:
        res = re.match( pattern, cell.value )
        if res:
            db_field = res.group('name')
            if db_field not in non_db_field:
                db_value = eval( "q_pg.{}".format( db_field ) )
            else:
                db_value == 'non db_value FIXME'
            cell.value = db_value


# save and exit

print( 'saving {}'.format(fn_out))
wb.save( fn_out )

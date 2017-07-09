import os,sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'example_project.settings')
django.setup()

from photologue.models import Photo
from HTMLParser import HTMLParser

#PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])
#sys.path.append(os.path.join(PROJECT_PATH, ".."))

class PrettyHTML( HTMLParser ):
	def handle_starttag( self, tag, attrs ):
		print( "startTag:", tag )
		print( "startAttrs", attrs )
	def handle_endtag( self, tag ):
		print( "endTag:", tag )
	def handle_data( self, data ):
		print( "data:", data )

c1 = Photo.objects.filter( slug="sc170701-60" )[0]
parser = PrettyHTML()
parser.feed( c1.captionCK ) 

import zipfile
try:
	from zipfile import BadZipFile
except ImportError:
	# Python 2.
	from zipfile import BadZipfile as BadZipFile

from django.forms import ModelForm
from django.forms.widgets import TextInput
from .models import DepartmentItem, PhotoGroup, InstanceMessage, \
				    InventoryType, InventoryItem

import logging
import os
from io import BytesIO

try:
	import Image
except ImportError:
	from PIL import Image


from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils.encoding import force_text
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile

from .models import Gallery, Photo

logger = logging.getLogger('photologue.forms')


class UploadZipForm(forms.Form):
	zip_file = forms.FileField()

	title = forms.CharField(label=_('Title'),
							max_length=250,
							required=False,
							help_text=_('All uploaded photos will be given a title made up of this title + a '
										'sequential number.<br>This field is required if creating a new '
										'gallery, but is optional when adding to an existing gallery - if '
										'not supplied, the photo titles will be creating from the existing '
										'gallery name.'))
	gallery = forms.ModelChoiceField(Gallery.objects.all(),
									 label=_('Gallery'),
									 required=False,
									 help_text=_('Select a gallery to add these images to. Leave this empty to '
												 'create a new gallery from the supplied title.'))
	caption = forms.CharField(label=_('Caption'),
							  required=False,
							  help_text=_('Caption will be added to all photos.'))
	description = forms.CharField(label=_('Description'),
								  required=False,
								  help_text=_('A description of this Gallery. Only required for new galleries.'))
	is_public = forms.BooleanField(label=_('Is public'),
								   initial=True,
								   required=False,
								   help_text=_('Uncheck this to make the uploaded '
											   'gallery and included photographs private.'))

	def clean_zip_file(self):
		"""Open the zip file a first time, to check that it is a valid zip archive.
		We'll open it again in a moment, so we have some duplication, but let's focus
		on keeping the code easier to read!
		"""
		zip_file = self.cleaned_data['zip_file']
		try:
			zip = zipfile.ZipFile(zip_file)
		except BadZipFile as e:
			raise forms.ValidationError(str(e))
		bad_file = zip.testzip()
		if bad_file:
			zip.close()
			raise forms.ValidationError('"%s" in the .zip archive is corrupt.' % bad_file)
		zip.close()  # Close file in all cases.
		return zip_file

	def clean_title(self):
		title = self.cleaned_data['title']
		if title and Gallery.objects.filter(title=title).exists():
			raise forms.ValidationError(_('A gallery with that title already exists.'))
		return title

	def clean(self):
		cleaned_data = super(UploadZipForm, self).clean()
		if not self['title'].errors:
			# If there's already an error in the title, no need to add another
			# error related to the same field.
			if not cleaned_data.get('title', None) and not cleaned_data['gallery']:
				raise forms.ValidationError(
					_('Select an existing gallery, or enter a title for a new gallery.'))
		return cleaned_data

	def save(self, request=None, zip_file=None):
		if not zip_file:
			zip_file = self.cleaned_data['zip_file']
		zip = zipfile.ZipFile(zip_file)
		count = 1
		current_site = Site.objects.get(id=settings.SITE_ID)
		if self.cleaned_data['gallery']:
			logger.debug('Using pre-existing gallery.')
			gallery = self.cleaned_data['gallery']
		else:
			logger.debug(
				force_text('Creating new gallery "{0}".').format(self.cleaned_data['title']))
			gallery = Gallery.objects.create(title=self.cleaned_data['title'],
											 slug=slugify(self.cleaned_data['title']),
											 description=self.cleaned_data['description'],
											 is_public=self.cleaned_data['is_public'])
			gallery.sites.add(current_site)
		for filename in sorted(zip.namelist()):

			logger.debug('Reading file "{0}".'.format(filename))

			if filename.startswith('__') or filename.startswith('.'):
				logger.debug('Ignoring file "{0}".'.format(filename))
				continue

			if os.path.dirname(filename):
				logger.warning('Ignoring file "{0}" as it is in a subfolder; all images should be in the top '
							   'folder of the zip.'.format(filename))
				if request:
					messages.warning(request,
									 _('Ignoring file "{filename}" as it is in a subfolder; all images should '
									   'be in the top folder of the zip.').format(filename=filename),
									 fail_silently=True)
				continue

			data = zip.read(filename)

			if not len(data):
				logger.debug('File "{0}" is empty.'.format(filename))
				continue

			photo_title_root = self.cleaned_data['title'] if self.cleaned_data['title'] else gallery.title

			# A photo might already exist with the same slug. So it's somewhat inefficient,
			# but we loop until we find a slug that's available.
			while True:
				photo_title = ' '.join([photo_title_root, str(count)])
				slug = slugify(photo_title)
				if Photo.objects.filter(slug=slug).exists():
					count += 1
					continue
				break

			photo = Photo(title=photo_title,
						  slug=slug,
						  caption=self.cleaned_data['caption'],
						  is_public=self.cleaned_data['is_public'])

			# Basic check that we have a valid image.
			try:
				file = BytesIO(data)
				opened = Image.open(file)
				opened.verify()
			except Exception:
				# Pillow (or PIL) doesn't recognize it as an image.
				# If a "bad" file is found we just skip it.
				# But we do flag this both in the logs and to the user.
				logger.error('Could not process file "{0}" in the .zip archive.'.format(
					filename))
				if request:
					messages.warning(request,
									 _('Could not process file "{0}" in the .zip archive.').format(
										 filename),
									 fail_silently=True)
				continue

			contentfile = ContentFile(data)
			photo.image.save(filename, contentfile)
			photo.save()
			photo.sites.add(current_site)
			gallery.photos.add(photo)
			count += 1

		zip.close()

		if request:
			messages.success(request,
				 _('The photos have been added to gallery "{0}".').format(
					 gallery.title),
				 fail_silently=True)

class DepartmentItemForm(ModelForm):
	class Meta:
		model = DepartmentItem
		fields = '__all__'
		widgets = {
			'color' : TextInput(attrs={'type': 'color'}),
			'report_color' : TextInput(attrs={'type': 'color'})
			}

class DailyReportItemForm(ModelForm):
	class Meta:
		model = DepartmentItem
		fields = '__all__'
		widgets = {
			'color' : TextInput(attrs={'type': 'color'}),
		}

class PhotoUploadForm(forms.Form):
	date = forms.CharField(max_length=50)
	time = forms.CharField(max_length=50)
	from_name = forms.CharField(max_length=50)
	my_file = forms.FileField()
	
	def save(self, request=None): 
		def handle_photo_upload(f):
			filepath = os.path.join('/tmp/',f.name )
			with open( filepath, 'wb+' ) as destination:
				for chunk in f.chunks():
					destination.write(chunk)
				destination.close()

		if request:
			print( u"PhotoUploadForm.save() request={}".format(request) ) 
			print( u"PhotoUploadForm.save() request={}".format(request) ) 
			try:
				handle_photo_upload( request.FILES['my_file'] ) 
			except:
				print( "handle_photo_upload fail" )
			try:
				filepath = os.path.join('/tmp',request.FILES['my_file'].name)
			except:
				print( "os.path.join fail" )
			try:
				photo_file_handle = open( filepath, "rb" )
				photo_data = photo_file_handle.read() 
				photo_file_handle.close()
			except:
				print( "handle_photo_upload Exception {}".format( filepath ) )
			print( "photo_data len({})".format( len(photo_data) ) ) 

			try:
				file = BytesIO(photo_data)
				opened = Image.open(file)
				opened.verify()
			except Exception:
				print( "photo uplaod {} is not valid".format(filepath) )

			titlefilename = request.FILES['my_file'].name
			print( "photo begin {}".format(titlefilename) )
			try:
				ph = Photo( title=titlefilename, slug=slugify(titlefilename) )
			except:
				print( 'photo begin error' )
			print( "photo contentfile" )
			contentfile = ContentFile(photo_data)
			print( "photo photo image save" )
			ph.image.save(titlefilename, contentfile)
			print( "photo save" )
			ph.save()
			print( "photo site" )
			ph.sites.add(Site.objects.get(id=settings.SITE_ID))

class PhotoGroupCMForm( forms.ModelForm ):
	class Meta:
		model = PhotoGroup
		fields = [
		    'name',
			'serial_no', 'contact_person', 'contact_number',
			'date_of_service', 
			'place_or_system', 'department_item', 
			'problem_description', 'service_provided', 'parts_replaced', 'remark',
			'conclusion', 'serviced_by', 'serviced_date', 'inspected_by',
			'inspection_date',
		]
		widgets = {
			'date_of_service': forms.DateInput(attrs={'class': 'datepicker'}),
			'serviced_date': forms.DateInput(attrs={'class': 'datepicker'}),
			'inspection_date': forms.DateInput(attrs={'class': 'datepicker'}),
			#'name': forms.TextInput(attrs={'size': '90%'}),
		#	'service_provided': forms.Textarea(attrs={'cols':'90%', 'rows':40}),
			}

class PhotoGroupPMForm( forms.ModelForm ):
	auto_id = True
	class Meta:
		model = PhotoGroup
		fields = [
			'name',
			'pmcheck1', 'pmcheck2', 'pmcheck3', 'pmcheck4', 'pmcheck5',
			'pmcheck6', 'pmcheck7', 'pmcheck8', 'pmcheck9', 'pmcheck10',
			'pmcheck11', 'pmcheck12', 'pmcheck13',  
			'report_date',
			'serial_no', 
			'date_of_service', 'place_or_system', 'department_item', 
			'problem_description', 'remark',
			'serviced_by',
		  ]
		widgets = {
			'report_date': forms.DateInput(attrs={'class': 'datepicker'}),
			'serviced_date': forms.DateInput(attrs={'class': 'datepicker'}),
			'inspection_date': forms.DateInput(attrs={'class': 'datepicker'}),
			}
	#pmcheck1 = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class':'primary','id': 'myonoffswitch'}))
	
# Inventory


class InventoryTypeForm( forms.ModelForm):
	class Meta:
		model = InventoryType
		fields = ['name', 'description', 'date_added']

class InventoryItemForm( forms.ModelForm ):
	class Meta:
		model = InventoryItem
		fields = ['name', 'serial_no', 'description',
			      'inventory_type', 'checkin_datetime',
				  'checkout_datetime', 'checked_out']

# Instance Message (IM) / Forum

class InstanceMessageForm( forms.ModelForm ):
	class Meta:
		model = InstanceMessage
		exclude = [ 'media' ]
		

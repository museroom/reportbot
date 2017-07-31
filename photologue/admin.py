from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib import messages
from django.utils.translation import ungettext, ugettext_lazy as _
from django.utils.encoding import force_unicode
from django.shortcuts import render
from django.contrib.admin import helpers
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.admin import widgets, DateFieldListFilter
from django.contrib.admin.widgets import FilteredSelectMultiple 
from django.http import HttpResponse

import tempfile, zipfile
from datetime import datetime, timedelta
from utils.logger import logger

from .models import Gallery, Photo, PhotoEffect, PhotoSize, \
		Watermark, Department, DepartmentItem, DailyReportItem, DailyReport, \
		Company, PhotoGroup, Profile
from django.forms import Textarea
from django.db import models
from .forms import UploadZipForm, DepartmentItemForm, DailyReportItemForm
						 


MULTISITE = getattr(settings, 'PHOTOLOGUE_MULTISITE', False)

# Daily Report Admin Items

class ProfileAdmin( admin.ModelAdmin ):
	model = Profile

admin.site.register(Profile, ProfileAdmin)

class CompanyAdmin( admin.ModelAdmin ):
	extra = 0
	model = Company

class DepartmentItemInline(admin.TabularInline):
	extra = 0
	model = DepartmentItem
	form = DepartmentItemForm

class DepartmentAdmin(admin.ModelAdmin):
	inlines = [DepartmentItemInline]

class DepartmentItemAdmin(admin.ModelAdmin):
	extra = 0
	form = DepartmentItemForm

admin.site.register(Company, CompanyAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(DepartmentItem, DepartmentItemAdmin)

class DailyReportItemInline( admin.StackedInline ):

	list_per_page = 10

	model = DailyReportItem

	formfield_overrides = {
		models.TextField: {'widget': Textarea(attrs={'rows':3, 'cols':39})},
	}
#	fields= ( 'daily_report_item', ('reportRowID', 'photoCol'),
#						('time_start', 'time_stop'),
#					'statusCK', 'planCK', )
	fields = ( ( 'daily_report', 'department_item' ),
						 #( 'time_start', 'time_stop' ),
						 ( 'reportRowID', 'reportOrder', ), #'photoCol',),
						 ( 'statusCK', 'planCK' ),
						 ( 'status_TOC_CK', 'plan_TOC_CK' ),
#						 ( 'photos' ),
						 )
#	fields = ( ( 'daily_report', 'daily_report_item' ),
#						 ( 'report_date', 'time_start', 'time_stop' ),
#						 ( 'reportRowID', 'reportOrder', 'photoCol',
#						   'rowTableId', 'colTableId', 
#							 'rowItemName', 'colItemName',
#							 'rowStatus', 'colStatus',
#							 'rowPlan', 'colPlan',
#							 'rowTime', 'colTime',
#							 'rowDirection', 'colDirection'),
#						 ( 'statusCK', 'planCK' ),
#						 )
	extra = 0


class DailyReportAdmin( admin.ModelAdmin):

	list_per_page = 10
	inlines = [DailyReportItemInline]
	actions = [
		'clone_report',
		'test_user_action'
	]

	def test_user_action(modeladmin, request, queryset):
		print( "modeladmin ={}\nrequest={}\nqueryset={}\n".format(
					modeladmin, request, queryset
				))
		print( "request user ={}".format( request.user.profile ) )
		print( "request company ={}".format( request.user.profile.company ) )
		print( "request active_report ={}".format( request.user.profile.active_report ) )
		msg = ungettext(
				"Successfully tested action",
				"Successfully tested actions",
				len( queryset )
			)
		messages.success( request, msg )

	def clone_report(modeladmin, request, queryset):
		for q in queryset:
			logger( "clone_report {}".format(q) )
			# find yesterday report
			qset_daily_report_item = DailyReportItem.objects.filter( daily_report=q )
			daily_report_latest = q #DailyReport.objects.order_by('-report_date')[0]
			# update report_date
			#daily_report_latest.report_date = timezone.make_aware( datetime.now() ) 
			daily_report_latest.report_date = q.report_date
			# pk=None
			daily_report_latest.title = daily_report_latest.title + "_clone"
			daily_report_latest.pk = None
			# save()
			daily_report_latest.save()
			for q_daily_report_item in qset_daily_report_item:
				#q_daily_report_item.report_date  = timezone.make_aware( datetime.now() )
				q_daily_report_item.report_date = timezone.localtime()
				q_daily_report_item.daily_report = daily_report_latest
				q_daily_report_item.pk = None
				q_daily_report_item.save()
			# find Photos that require followup
			#photo_admin = PhotoAdmin(request,queryset)
			#photo_admin.autofill_related_daily_report_item()
			today = timezone.localtime()
			qset_photo = Photo.objects.filter( follow_up_date_end__gt = today )
			logger( "clone_report qset_photo len={}".format( len(qset_photo) ) )
			for q_photo in qset_photo:
				q_daily_report_item =	q_photo.get_related_daily_report_item()
				if q_daily_report_item != None:
					q_photo.daily_report_item.add( q_daily_report_item )
					q_photo.save()
			# Extent follow up by +1 date
			qset_photo_followup = Photo.objects.filter(
				follow_up_date_end__gt = timezone.localtime() )
			logger( '{} photos to followup, +1 date'.format( 
				len( qset_photo_followup) ) )
			qset_photo_followup.update( follow_up_date_end = \
				timezone.localtime() + timezone.timedelta(1,0,0) )
		msg = ungettext(
				"Successfully cloned report",
				"Successfully cloned reports",
				len( queryset )
			)
		messages.success( request, msg )



class DailyReportItemAdmin(admin.ModelAdmin): #list_per_page = 10

	form = DailyReportItemForm
	list_per_page = 50

	fieldsets = (  ('', {
							'fields': (
								( "daily_report", "department_item", ),
								("statusCK", "planCK"),
								("status_TOC_CK", "plan_TOC_CK"),
								"report_date", 
										 )
						}),
						( '', {
							'fields': (
								("time_start", "time_stop"),
								("color","reportRowID", "reportOrder"),
							)
						}), 
					)
	list_display = ( "__str__",
						"daily_report", "department_item",
						"time_start", "time_stop", 
#									"tableTemplate", "rowDirection", "colDirection",
#									"daily_report",
						)
	list_editable = (
#									"tableTemplate", "rowDirection", "colDirection",
									"time_start", "time_stop", 
									#"daily_report", "daily_report_item", #"tableTemplate",
									)
	search_fields = ["department_item__name", 
						  ]
	
#	raw_id_fields = ('slug','title',) 
#admin.site.register(DailyReport)
admin.site.register(DailyReportItem, DailyReportItemAdmin)
admin.site.register(DailyReport, DailyReportAdmin)
	
class PhotoGroupAdminForm( forms.ModelForm):

	filter_horizontal = ['photo']

	class Meta:
		model = Gallery
		if MULTISITE:
			exclude = []
		else:
			exclude = ['sites']

	if MULTISITE:
		filter_horizontal = ['sites']
	if MULTISITE:
		actions = [
			'add_to_current_site',
			'add_photos_to_current_site',
			'remove_from_current_site',
			'remove_photos_from_current_site'
		]
	
class PhotoGroupAdmin( admin.ModelAdmin ):

	list_display = ('name', 'date_added' ) 
	#filter_horizontal = ['photos',]
	form = PhotoGroupAdminForm
	fields = ( #'date_added', 
			  'name', 
		       #'company', 'department', 
			  'contact_person', 'contact_number', 'date_of_service',
			  'place_or_system', 'department_item', 'problem_description', 
			  'service_provided', 'parts_replaced', 'remark', 'conclusion', 
			  'serviced_by', 'serviced_date', 'inspected_by', 'inspection_date',
			  )

	def get_form( self, request, obj=None, **kwargs):
		if( obj != None ):
			request.current_object = obj
		return super(PhotoGroupAdmin, self).get_form(request, obj, **kwargs)

	def formfield_for_manytomany(self, db_field, request, **kwargs):
		""" Set the current site as initial value. """
		if db_field.name == "photos":
			print( "{} formfield = photo, request={}".format( self , request) )
			print( u"request.current_object.date_added.date = {}".format(
				request.current_object.date_added.date()) )
			obj = request.current_object
			dt_report = obj.date_added
			dt_range = 4
			dt_from = dt_report - timezone.timedelta(dt_range,0,0)
			dt_to	= dt_report + timezone.timedelta(dt_range,0,0)
			qset = Photo.objects.filter( 
				department_item__department__company  = request.user.profile.company ).filter( 
										date_added__date__gt = dt_from.date() ).filter(
										date_added__date__lt = dt_to.date() ) 
					#date_added__date = request.current_object.date_added.date() )
			kwargs['queryset'] = qset
		vertial = True
		kwargs['widget'] = widgets.FilteredSelectMultiple(
			db_field.verbose_name,
			vertial,
			)
		return super(PhotoGroupAdmin, self).formfield_for_manytomany(
												db_field, request, **kwargs)
	#	return super(PhotoGroupAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

admin.site.register(PhotoGroup, PhotoGroupAdmin)

class GalleryAdminForm(forms.ModelForm):

	class Meta:
		model = Gallery
		if MULTISITE:
			exclude = []
		else:
			exclude = ['sites']

	if MULTISITE:
		filter_horizontal = ['sites']
	if MULTISITE:
		actions = [
			'add_to_current_site',
			'add_photos_to_current_site',
			'remove_from_current_site',
			'remove_photos_from_current_site'
		]


class GalleryAdmin(admin.ModelAdmin):
	list_display = ('title', 'date_added', 'photo_count', 'is_public')
	list_filter = ['date_added', 'is_public']
#	fields = ( 'title', 'date_added', 'slug' )
	if MULTISITE:
		list_filter.append('sites')
	date_hierarchy = 'date_added'
	prepopulated_fields = {'slug': ('title',)}
	form = GalleryAdminForm
	if MULTISITE:
		filter_horizontal = ['sites']
	if MULTISITE:
		actions = [
			'add_to_current_site',
			'add_photos_to_current_site',
			'remove_from_current_site',
			'remove_photos_from_current_site'
		]

	def formfield_for_manytomany(self, db_field, request, **kwargs):
		""" Set the current site as initial value. """
		if db_field.name == "sites":
			kwargs["initial"] = [Site.objects.get_current()]
		return super(GalleryAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

	def save_related(self, request, form, *args, **kwargs):
		"""
		If the user has saved a gallery with a photo that belongs only to
		different Sites - it might cause much confusion. So let them know.
		"""
		super(GalleryAdmin, self).save_related(request, form, *args, **kwargs)
		orphaned_photos = form.instance.orphaned_photos()
		if orphaned_photos:
			msg = ungettext(
				'The following photo does not belong to the same site(s)'
				' as the gallery, so will never be displayed: %(photo_list)s.',
				'The following photos do not belong to the same site(s)'
				' as the gallery, so will never be displayed: %(photo_list)s.',
				len(orphaned_photos)
			) % {'photo_list': ", ".join([photo.title for photo in orphaned_photos])}
			messages.warning(request, msg)

	def add_to_current_site(modeladmin, request, queryset):
		current_site = Site.objects.get_current()
		current_site.gallery_set.add(*queryset)
		msg = ungettext(
			"The gallery has been successfully added to %(site)s",
			"The galleries have been successfully added to %(site)s",
			len(queryset)
		) % {'site': current_site.name}
		messages.success(request, msg)
	add_to_current_site.short_description = \
		_("Add selected galleries to the current site")

	def remove_from_current_site(modeladmin, request, queryset):
		current_site = Site.objects.get_current()
		current_site.gallery_set.remove(*queryset)
		msg = ungettext(
			"The gallery has been successfully removed from %(site)s",
			"The selected galleries have been successfully removed from %(site)s",
			len(queryset)
		) % {'site': current_site.name}
		messages.success(request, msg)

	remove_from_current_site.short_description = \
		_("Remove selected galleries from the current site")

	def add_photos_to_current_site(modeladmin, request, queryset):
		photos = Photo.objects.filter(galleries__in=queryset)
		current_site = Site.objects.get_current()
		current_site.photo_set.add(*photos)
		msg = ungettext(
			'All photos in gallery %(galleries)s have been successfully added to %(site)s',
			'All photos in galleries %(galleries)s have been successfully added to %(site)s',
			len(queryset)
		) % {
			'site': current_site.name,
			'galleries': ", ".join(["'{0}'".format(gallery.title)
									for gallery in queryset])
		}
		messages.success(request, msg)

		add_photos_to_current_site.short_description = \
		_("Add all photos of selected galleries to the current site")

	def remove_photos_from_current_site(modeladmin, request, queryset):
		photos = Photo.objects.filter(galleries__in=queryset)
		current_site = Site.objects.get_current()
		current_site.photo_set.remove(*photos)
		msg = ungettext(
			'All photos in gallery %(galleries)s have been successfully removed from %(site)s',
			'All photos in galleries %(galleries)s have been successfully removed from %(site)s',
			len(queryset)
		) % {
			'site': current_site.name,
			'galleries': ", ".join(["'{0}'".format(gallery.title)
									for gallery in queryset])
		}
		messages.success(request, msg)

	remove_photos_from_current_site.short_description = \
		_("Remove all photos in selected galleries from the current site")

admin.site.register(Gallery, GalleryAdmin)


class PhotoAdminForm(forms.ModelForm):

	class Meta:
		model = Photo
		if MULTISITE:
			exclude = []
		else:
			exclude = ['sites']


class PhotoAdmin(admin.ModelAdmin):
	list_display = ( 'title', 
							'thumbnail_admin',
							'department_item',	
							'tags',
							'date_added',
									)
	list_editable = ( 'department_item',
							 'tags',
							 #'follow_up_date_end',
						)
	list_filter = [ 'date_added', 'department_item']
	if MULTISITE:
		list_filter.append('sites')
	search_fields = ['title', 'slug', 'caption', 
						  'department_item__department__name',
						  'department_item__name',
						  'department_item__tags',
						  'department_item__name',
						  'department_item__name_long',
						  'tags',
						  ]
	list_per_page = 20
	prepopulated_fields = {'slug': ('title',)}
#	save_on_top = True
	fieldsets = (
				( '', {
					'fields': ('image', 'thumbnail_admin', 'title', 
								( 'department_item','department',),
								('date_taken', 'date_added',), 'slug',
								 )
				}),
				(	'', {
					'fields': ( 'caption', 'is_public',
									'daily_report_item'
								 )
				}),

				)

#	readonly_fields = ('admin_thumbnail',)
	readonly_fields = ('thumbnail_admin',)

	form = PhotoAdminForm
	
	actions = ['set_company_CoD',
				  'set_company_SC',
			   'fill_related_daily_report_item',
				  'create_new_group',
				  'download_photos',
				  ]

	if MULTISITE:
		filter_horizontal = ['sites']
	if MULTISITE:
		actions.append('add_photos_to_current_site')
		actions.append('remove_photos_from_current_site')


	def get_form( self, request, obj=None, **kwargs):
		if( obj != None ):
			request.current_object = obj
		return super(PhotoAdmin, self).get_form(request, obj, **kwargs)

	def formfield_for_manytomany(self, db_field, request, **kwargs):
#		""" daily_report_item for photo """
#		if db_field.name == "daily_report_item" and \
#				hasattr(request, 'current_object'):
#			yesterday = datetime.today() - timedelta(1)
#			instance = request.current_object
#			if( instance.report_item != None ):
#				#print( "DEBUG: Department hasattr" )
#				department = Department.objects.get( name=instance.report_item.department )
#				kwargs["queryset"] = DailyReportItem.objects.filter(
#					  report_date__gt = timezone.make_aware(yesterday)	).filter(
#										 daily_report_item__department = department  ).order_by(
#										 "-report_date" )
#			else:
#				#print( "ERROR: Department not set" )
#				kwargs["queryset"] = DailyReportItem.objects.filter(
#					  report_date__gt = timezone.make_aware(yesterday) )
		""" Set the current site as initial value. """
		if db_field.name == "sites":
			kwargs["initial"] = [Site.objects.get_current()] 
		return super(PhotoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
	
	def formfield_for_foreignkey( self, db_field, request, **kwargs):
		if db_field.name == "department_item":
			user_company = request.user.profile.company
			#user_department = request.user.profile.department
			if user_company.name != "Any": 
				kwargs["queryset"] = DepartmentItem.objects.filter( 
						department__company = request.user.profile.company )
			else:
				kwargs["queryset"] = DepartmentItem.objects.all()
		return super( PhotoAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs ) 

	def reset_photo_department( modeladmin, request, queryset ):
		queryset.update( department = Department.objects.get( name = "Other" ) )

	def download_photos( modeladmin, request, queryset):
		with tempfile.SpooledTemporaryFile() as tmp:
			with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
				for photo in queryset:
					#projectUrl = str(item.cv) + ''
					date_time = photo.date_added.astimezone( 
									timezone.get_default_timezone( ) 
									).strftime( "%y%m%d-%H%M%S" )
					fileNameInZip = '{2}_{1}_{0}.jpg'.format(
									photo.slug, photo.department_item.name, 
									date_time )
					archive.write(photo.image.path,fileNameInZip)
				tmp.seek(0)
				response = HttpResponse(tmp.read())
				response.content_type = 'application/x-zip-compressed'
				response['Content-Disposition'] = 'attachment; filename="reportbot.zip"'
				return response	

	def create_new_group( modeladmin, request, queryset):
		if queryset == None:
			messages.success( request, 'no photo selected.' )
			return
		photo_date_time = queryset[0].date_added.astimezone( timezone.get_default_timezone()) 
		groupname = u"{2}_{0}_{1}_auto".format(photo_date_time.strftime( "%y%m%d-%H%M%S" ),
											queryset[0].department_item.name,
											queryset[0].department_item.department.company.name )
		new_photo_group = PhotoGroup( name=groupname, date_added=photo_date_time )
		new_photo_group.save()
		for q_photo in queryset:
			new_photo_group.photos.add( q_photo )

		msg = ungettext(
			'The photo has been successfully added to new group',
			'The photos have been successfully added to new group',
			len(queryset)
		)
		messages.success( request, msg )

	def fill_related_daily_report_item( modeladmin, request, queryset ):
		for q_photo in queryset:
			q_daily_report_item = q_photo.get_related_daily_report_item()
			if q_daily_report_item != None:
				q_photo.daily_report_item.add( q_daily_report_item )
				q_photo.save()
		msg = ungettext(
			'The photo has been successfully updated related daily report item',
			'The photos have been successfully updated related daily report items',
			len(queryset)
		)
		messages.success( request, msg )
			
	def autofill_related_daily_report_item():
		# Find all photo with follow up end > today
		today = timezone.localtime()
		qset_photo = Photo.objects.filter( follow_up_date_end__gt = today )
		for q_photo in qset_photo:
			q_daily_report_item =	q_photo.get_related_daily_report_item()
			if q_daily_report_item != None:
				q_photo.daily_report_item.add( q_daily_report_item )
				q_photo.save()
			

	def add_photos_to_current_site(modeladmin, request, queryset):
		current_site = Site.objects.get_current()
		current_site.photo_set.add(*queryset)
		msg = ungettext(
			'The photo has been successfully added to %(site)s',
			'The selected photos have been successfully added to %(site)s',
			len(queryset)
		) % {'site': current_site.name}
		messages.success(request, msg)

	add_photos_to_current_site.short_description = \
		_("Add selected photos to the current site")

	def remove_photos_from_current_site(modeladmin, request, queryset):
		current_site = Site.objects.get_current()
		current_site.photo_set.remove(*queryset)
		msg = ungettext(
			'The photo has been successfully removed from %(site)s',
			'The selected photos have been successfully removed from %(site)s',
			len(queryset)
		) % {'site': current_site.name}
		messages.success(request, msg)

	remove_photos_from_current_site.short_description = \
		_("Remove selected photos from the current site")

	def get_urls(self):
		urls = super(PhotoAdmin, self).get_urls()
		custom_urls = [
			url(r'^upload_zip/$',
				self.admin_site.admin_view(self.upload_zip),
				name='photologue_upload_zip')
		]
		return custom_urls + urls

	def response_change(self, request, obj):
		print( "DEBUG: response_change {}:{}".format( request.POST, self ) )
		"""
		Determines the HttpResponse for the change_view stage.
		"""
		if request.POST.has_key("_viewnext"):
				msg = (_('The %(name)s "%(obj)s" was changed successfully.') %
							 {'name': force_unicode(obj._meta.verbose_name),
								'obj': force_unicode(obj)})
				next = obj.__class__.objects.filter(id__gt=obj.id).order_by('id')[:1]
				if next:
						self.message_user(request, msg)
#						return HttpResponseRedirect("../%s/" % next[0].pk)
						return HttpResponseRedirect("../../%s/" % next[0].pk)
		return super(PhotoAdmin, self).response_change(request, obj)

	def upload_zip(self, request):

		context = {
			'title': _('Upload a zip archive of photos'),
			'app_label': self.model._meta.app_label,
			'opts': self.model._meta,
			'has_change_permission': self.has_change_permission(request)
		}

		# Handle form request
		if request.method == 'POST':
			form = UploadZipForm(request.POST, request.FILES)
			if form.is_valid():
				form.save(request=request)
				return HttpResponseRedirect('..')
		else:
			form = UploadZipForm()
		context['form'] = form
		context['adminform'] = helpers.AdminForm(form,
												 list([(None, {'fields': form.base_fields})]),
												 {})
		return render(request, 'admin/photologue/photo/upload_zip.html', context)


admin.site.register(Photo, PhotoAdmin)


class PhotoEffectAdmin(admin.ModelAdmin):
	list_display = ('name', 'description', 'color', 'brightness',
					'contrast', 'sharpness', 'filters', 'admin_sample')
	fieldsets = (
		(None, {
			'fields': ('name', 'description')
		}),
		('Adjustments', {
			'fields': ('color', 'brightness', 'contrast', 'sharpness')
		}),
		('Filters', {
			'fields': ('filters',)
		}),
		('Reflection', {
			'fields': ('reflection_size', 'reflection_strength', 'background_color')
		}),
		('Transpose', {
			'fields': ('transpose_method',)
		}),
	)

admin.site.register(PhotoEffect, PhotoEffectAdmin)


class PhotoSizeAdmin(admin.ModelAdmin):
	list_display = ('name', 'width', 'height', 'crop', 'pre_cache', 'effect', 'increment_count')
	fieldsets = (
		(None, {
			'fields': ('name', 'width', 'height', 'quality')
		}),
		('Options', {
			'fields': ('upscale', 'crop', 'pre_cache', 'increment_count')
		}),
		('Enhancements', {
			'fields': ('effect', 'watermark',)
		}),
	)

admin.site.register(PhotoSize, PhotoSizeAdmin)


class WatermarkAdmin(admin.ModelAdmin):
	list_display = ('name', 'opacity', 'style')


admin.site.register(Watermark, WatermarkAdmin)

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

from datetime import datetime, timedelta

from .models import Gallery, Photo, PhotoEffect, PhotoSize, \
	Watermark, Department, ReportItem, DailyReportItem, DailyReport, \
	TestingClass
from .forms import UploadZipForm

MULTISITE = getattr(settings, 'PHOTOLOGUE_MULTISITE', False)

# Daily Report Admin Items

class ReportItemInline(admin.StackedInline):
	extra = 0
	model = ReportItem

class DepartmentAdmin(admin.ModelAdmin):
	inlines = [ReportItemInline]
	
admin.site.register(Department, DepartmentAdmin)
admin.site.register(ReportItem)

class DailyReportItemInline( admin.StackedInline ):

	list_per_page = 10

	model = DailyReportItem

#	fields= ( 'report_daily_item', ('reportRowID', 'photoCol'),
#						('time_start', 'time_stop'),
#					'statusCK', 'planCK', )
	fields = ( ( 'report_daily', 'report_daily_item' ),
						 #( 'time_start', 'time_stop' ),
						 ( 'reportRowID', 'reportOrder', ), #'photoCol',),
						 ( 'statusCK', 'planCK' ),
						 ( 'status_TOC_CK', 'plan_TOC_CK' ),
						 )
#	fields = ( ( 'report_daily', 'report_daily_item' ),
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

	inlines = [DailyReportItemInline]
	actions = [
		'clone_report'
	]

	def clone_report(modeladmin, request, queryset):
		for q in queryset:
			# find yesterday report
			qset_report_daily_item = DailyReportItem.objects.filter( report_daily = q )
			report_daily_latest = q #DailyReport.objects.order_by('-report_date')[0]
			# update report_date
			report_daily_latest.report_date = timezone.make_aware( datetime.now() ) 
			# pk=None
			report_daily_latest.title = report_daily_latest.title + "_latest"
			report_daily_latest.pk = None
			# save()
			report_daily_latest.save()
			for q_report_daily_item in qset_report_daily_item:
				q_report_daily_item.report_date  = timezone.make_aware( datetime.now() )
				q_report_daily_item.report_daily = report_daily_latest
				q_report_daily_item.pk = None
				q_report_daily_item.save()


class DailyReportItemAdmin(admin.ModelAdmin): #list_per_page = 10

	list_per_page = 10

	list_display = ( "__str__",
									"report_daily", "report_daily_item",
									"time_start", "time_stop", 
#									"tableTemplate", "rowDirection", "colDirection",
#									"report_daily",
									)
	list_editable = (
#									"tableTemplate", "rowDirection", "colDirection",
									"time_start", "time_stop", 
									#"report_daily", "report_daily_item", #"tableTemplate",
									)
	search_fields = ["report_date","report_daily_item__name"]
	
#	raw_id_fields = ('slug','title',) 
#admin.site.register(DailyReport)
admin.site.register(DailyReportItem, DailyReportItemAdmin)
admin.site.register(DailyReport, DailyReportAdmin)
admin.site.register( TestingClass )
	
class GalleryAdminForm(forms.ModelForm):

	class Meta:
		model = Gallery
		if MULTISITE:
			exclude = []
		else:
			exclude = ['sites']


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
	list_display = ( 'title', 'admin_thumbnail',
									'report_item',  'date_added'
									)
	list_editable = ( 'report_item',
									)
	list_filter = ['date_added', 'is_public']
	if MULTISITE:
		list_filter.append('sites')
	search_fields = ['title', 'slug', 'caption']
	list_per_page = 10
	prepopulated_fields = {'slug': ('title',)}
#	save_on_top = True
#	fieldsets = (
#				( 'Information', {
#					'fields': ('admin_thumbnail', 'title', 
#								'department', 'report_item',
#								'date_taken', 'date_added', 'slug',
#								 )
#				}),
#				(	'Information2', {
#					'fields': ( 'caption', 'is_public',
#								 )
#				}),
#
#				)

#	readonly_fields = ('admin_thumbnail',)

	form = PhotoAdminForm
	
	actions = ['reset_photo_department']

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
#                     report_date__gt = timezone.make_aware(yesterday)  ).filter(
#										 report_daily_item__department = department  ).order_by(
#										 "-report_date" )
#			else:
#				#print( "ERROR: Department not set" )
#				kwargs["queryset"] = DailyReportItem.objects.filter(
#                     report_date__gt = timezone.make_aware(yesterday) )
		""" Set the current site as initial value. """
		if db_field.name == "sites":
			kwargs["initial"] = [Site.objects.get_current()] 
		return super(PhotoAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

	def reset_photo_department( modeladmin, request, queryset ):
		queryset.update( department = Department.objects.get( name = "Other" ) )


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

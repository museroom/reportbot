import warnings 
import os
from io import BytesIO

try:
	import Image
except ImportError:
	from PIL import Image

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views.generic.dates import ArchiveIndexView, DateDetailView,  \
	DayArchiveView, MonthArchiveView, \
	YearArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.base import RedirectView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.base import ContentFile

from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Photo, Gallery, DailyReportItem, DepartmentItem, \
	Department, DailyReport, PhotoGroup, Profile, Company, \
	PhotoGroupImage, PhotoGroupImageClass

from .forms import PhotoUploadForm
import time, datetime
from HTMLParser import HTMLParser

from utils.logger import logger

# Json Query.
def JsonPhotoQuery( request, report_item, date_and_time ):
	today = time.strftime( "%y%m%d", time.localtime() ) 
	today = "170706"
	logger( "[JsonPhotoQuery] report_item = {}/ date_and_time = {}".format(
				report_item, date_and_time ) )
	qset = Photo.objects.filter( 
		daily_report_item__pk = int(date_and_time))
	rsp = []
	for thumbSet in qset:
		rsp.append( {"image":thumbSet.get_report_url()} ) 
	#return JsonResponse(list(qset.values('image')), safe=False)
	return JsonResponse(dict(photos=rsp)) #, safe=False)

def JsonTableMapQuery( request, date_and_time ):
	logger( "JsonTableMapQuery {}".format( 
		date_and_time ), 'DEBUG' )
	qset = DailyReportItem.objects.filter( 
							daily_report__title = date_and_time
							).order_by('reportOrder')
	rspGroup = []
	rsp=[]
	for item in qset:
		#rsp = []
		rsp.append( {"order":str(item.reportOrder),
								 "name":item.department_item.name,
								 "pk":str(item.pk),
								 "template":item.tableTemplate,
								 "row_photo":item.photoCol,
								 })
		
		#rsp.append( { "name":item.daily_report_item.name, 
		#rspGroup.append( rsp )
	logger( dict(log=rsp), is_json=True )
	return JsonResponse(dict(tableMap=rsp)) #, safe= False )
		
def JsonReportItemQuery( request, report_pk ):
	logger( "JsonReportItemQuery {}:{}".format( 
		report_pk, 
		DailyReportItem.objects.get( pk=report_pk )
		),
		'DEBUG' 
	)

	HTMLrsp = []
	
	class PrettyHTML( HTMLParser ):
		def handle_starttag( self, tag, attrs ):
			#logger( "start tag:{}".format(tag))
			#logger( "start attrs{}".format(attrs))
			HTMLrsp.append( {"startTag":tag} )
			HTMLrsp.append( {"startAttrs":mark_safe(attrs)} )
		def handle_endtag( self, tag ):
			#logger( "end tag:{}".format(tag))
			HTMLrsp.append( {"endTag":tag} )
		def handle_data( self, data ):
			#logger( "data:{}".format(data))
			HTMLrsp.append( {"data":data} )
			

#	qset = DailyReportItem.objects.filter(
#							daily_report__title = date_and_time
#							).filter( 
#								daily_report_item__name = report_item )
	qset = DailyReportItem.objects.get( pk = report_pk )

	#today = time.strftime( "%y%m%d", time.localtime() ) 
	#today = "170703"
	#qset = DailyReportItem.objects.filter( 
	#										daily_report_item__name = report_item )\
	#										.filter( title__contains = today )
	# parse CKHtml into json

	HTMLstatus = []
	HTMLplan = []
	HTMLstatus_toc = []
	HTMLplan_toc = []
	parser = PrettyHTML()
	
	rsp = []
	rspGroup = []

	HTMLrsp = []
	#logger( "statusCKtext:{}".format(qset.statusCK) )
	qset.statusCK = qset.statusCK.replace("&nbsp;"," ")
	parser.feed( qset.statusCK )
	HTMLstatus = HTMLrsp
	HTMLrsp = []
	qset.planCK = qset.planCK.replace("&nbsp;"," ")
	parser.feed( qset.planCK )
	HTMLplan = HTMLrsp
	HTMLrsp = []
	qset.status_TOC_CK = qset.status_TOC_CK.replace("&nbsp;"," ")
	parser.feed( qset.status_TOC_CK )
	HTMLstatus_toc = HTMLrsp
	HTMLrsp = []
	qset.plan_TOC_CK = qset.plan_TOC_CK.replace("&nbsp;"," ")
	parser.feed( qset.plan_TOC_CK )
	HTMLplan_toc = HTMLrsp

	# if TOC content empty, copy from table HTML text for lazy ass
	if len(HTMLstatus_toc) == 0:
		HTMLstatus_toc = HTMLstatus
	if len(HTMLplan_toc) == 0:
		HTMLplan_toc = HTMLplan

	#rspGroup.append ({
	rspGroup={
		"time_start":str(qset.time_start)[0:5],
		"time_stop" :str(qset.time_stop)[0:5],
		"name":qset.__str__(),
		"statusCK" : HTMLstatus, #,set[0].statusCK,
		"planCK" : HTMLplan, #qset.planCK
		"status_toc_CK": HTMLstatus_toc,
		"plan_toc_CK": HTMLplan_toc,
		"photoCol":qset.photoCol,
		"reportRowID":qset.reportRowID,
		"reportRowID":qset.reportRowID,
		"photoCol":qset.photoCol,
		"reportOrder":qset.reportOrder,
		"rowTableId":qset.rowTableId,
		"colTableId":qset.colTableId,
		"rowItemName":qset.rowItemName,
		"colItemName":qset.colItemName,
		"rowStatus":qset.rowStatus,
		"colStatus":qset.colStatus,
		"rowPlan":qset.rowPlan,
		"colPlan":qset.colPlan,
		"rowTime":qset.rowTime,
		"colTime":qset.colTime,
		"rowDirection":qset.rowDirection,
		"colDirection":qset.colDirection,
		"pk":qset.pk,
		"department":qset.department_item.department.name,
		"daily_report_item":qset.department_item.name,
		"direction":qset.department_item.location,
		"name_long":qset.department_item.name_long, 
		#});
		}
	logRspGroup = rspGroup
#	for field in ('statusCK', 'planCK', 'status_toc_CK',  'plan_toc_CK' ):
		#logRspGroup[field] = mark_safe( rspGroup[field] )
#		logRspGroup[0][field] = mark_safe( rspGroup[0][field] )
#	logRspGroup['statusCK'] = mark_safe( rspGroup['statusCK'] )
#	logRspGroup['planCK'] = mark_safe( rspGroup['planCK'] )
#	logRspGroup['status_toc_CK'] = mark_safe( rspGroup['status_toc_CK'] )
#	logRspGroup['plan_toc_CK'] = mark_safe( rspGroup['plan_toc_CK'] )
	#return JsonResponse(list(qset.values('image')), safe=False)
	#return JsonResponse(HTMLrsp, safe=False)
	logger( logRspGroup, is_json=True )
	return JsonResponse(dict(reportItems=rspGroup) ) #, safe=False)


# ReportItem / Daily Report Views
class DailyReportDateView(object):
	queryset = Photo.objects.all()
	date_field = 'date_added'
	allow_empty = True

# PhotoGroup / Monthly Report Views
class PhotoGroupDetailView(object):
	queryset = PhotoGroup.objects.all()
	date_field = 'date_added'
	allow_empty = True


# Photo Select Pop Views
class PhotoSelectListView(ListView): 
	model = Photo,
	template_name = "photologue/photoselect_list.html"
	
	def get_context_data( self, **kwargs):
		context = super( PhotoSelectListView, self).get_context_data(**kwargs)
		date_time = timezone.datetime.strptime(  
						"{}-{}-{}".format(
							self.kwargs['year'], 
							self.kwargs['month'],
							self.kwargs['day'] ),"%Y-%m-%d")
		date_time_prev = date_time - timezone.timedelta(1,0,0)
		date_time_next = date_time + timezone.timedelta(1,0,0)
		target = self.kwargs['target']
		pk = self.kwargs['pk']
		context['date_prev'] = date_time_prev
		context['date_prev_url'] = reverse( 'photologue:photo-select-popup-list',
											kwargs={'year':date_time_prev.year,
													'month':date_time_prev.month,
													'day':date_time_prev.day,
													'target':target,
													'pk':pk} )

		context['date_report'] = date_time
		context['date_next'] = date_time_next
		context['date_next_url'] = reverse( 'photologue:photo-select-popup-list',
											kwargs={'year':date_time_next.year,
													'month':date_time_next.month,
													'day':date_time_next.day,
													'target':target,
													'pk':pk} )
		context['active_photogroup']=self.request.user.profile.active_report
		if target == 'photogroup':
			context['target_photo_group'] = target
		elif target == 'dailyreport':
			context['target_daily_report'] = target
		context['pk'] = pk
		user_profile = self.request.user.profile
		context['department_item_list'] = DepartmentItem.objects.filter(
				department__company = user_profile.company )
		context['daily_report_item_list'] = DailyReportItem.objects.filter(
				department_item__department__company = 
				self.request.user.profile.company ).filter( 
						daily_report = user_profile.active_report )

		return context


	def get_queryset(self):
		date_time = timezone.datetime.strptime(  
						"{}-{}-{}".format(
							self.kwargs['year'], 
							self.kwargs['month'],
							self.kwargs['day'] ),"%Y-%m-%d")
		qset = Photo.objects.filter( date_added__date = date_time.date() )
		#.filter( department_item__department__company = self.request.user.profile.company )
#		qset_nodate = Photo.objects.filter( date_added__date = date_time.date()).filter( department_item = None )
#		qset += qset_nodate

		return qset

class MonthlyReportListView( LoginRequiredMixin, ListView ):
	login_url = '/login'
	model = PhotoGroup
	template_name="photologue/monthlyreport_list.html"

	def get_queryset(self):
		qset = PhotoGroup.objects.all().order_by(
				"date_of_service" )
		return qset



class MonthlyReportDetailView(LoginRequiredMixin, DetailView ):
	login_url = '/login' 
	model = PhotoGroup
	template_name="photologue/monthlyreport_detail.html"
	def get_context_data( self, **kwargs):
		obj = kwargs['object']
		print( "debug: MonthlyReportDetailView:Obj:photogroup={}".format(obj) )
		q_profile = Profile.objects.get( pk = self.request.user.profile.pk )
		q_profile.active_photogroup = obj 
		q_profile.save()
		date_time = obj.date_added
		context = super( MonthlyReportDetailView, self).get_context_data(**kwargs)
		context['var1'] = 'value1'
		context['add_photo_url'] = reverse( 'photologue:photo-select-popup-list',
					kwargs={'year':date_time.year, 'month':date_time.month, 'day':date_time.day,
							'target':'photogroup', 'pk':obj.pk} )
		context['edit_record_url'] = reverse( 'admin:photologue_photogroup_change', args=[obj.id] )
		q_profile = Profile.objects.get( pk = self.request.user.profile.pk )
		q_profile.active_photogroup = obj
		q_profile.save()
		context['active_photogroup'] = q_profile.active_photogroup
		context['select_company'] = Company.objects.all()
		context['select_department'] = Department.objects.all()
		context['target_photo_group'] = self
		return context


class DailyReportListView(DailyReportDateView, ArchiveIndexView ):
	#date_and_time = timezone.localtime().strftime("%y%m%d-%H%M")
	#paginate_by = 5

	template_name = "photologue/dailyreport_edit.html"

	def get_queryset(self):
		print( 'reportitemlistview queryset={0}'.format( self.kwargs ) )
		if self.kwargs.has_key( 'date_and_time' ):
			print( 'reportitemlistview dateandtime={0}'.format( self.kwargs['date_and_time'] ) )
			date_and_time = self.kwargs['date_and_time']
		else:
			print( 'dateandtime set to today' )
			date_and_time = '2017-07-26-1930'

		print( "date_and_time = {}".format(date_and_time))
			
		#return Department.objects.all()
		d = Photo
		qset = d.objects.filter( daily_report_item__daily_report__title = date_and_time ).order_by( 'daily_report_item__reportOrder' ) 
#		return { 'object_list' : qset } #, 'date_and_time':date_and_time }
		return qset

#class DailyReportListView(ListView):
#	queryset = DailyReport.objects.all()
#	paginate_by = 20

class DailyReportDetailView( DetailView):
	queryset = DailyReport.objects.all()


class DailyReportDetailView(DailyReportDateView, DateDetailView):
	pass


class DailyReportArchiveIndexView(DailyReportDateView, ArchiveIndexView):
	pass


class DailyReportDayArchiveView(LoginRequiredMixin, DailyReportDateView, DayArchiveView):
	login_url = '/login/'
	template_name = "photologue/dailyreport_edit.html"
	date_and_time = timezone.localtime()
	def get_context_data( self, **kwargs):
		print("debug: active report={}".format(self.request.user.profile.active_report))
		context = super(DayArchiveView, self).get_context_data(**kwargs)
		context['daily_report'] = DailyReport.objects.all()
		context['active_report'] = self.request.user.profile.active_report.title
		if self.kwargs.has_key('year'):
			print( "debug: dailyrepot_edit using redirect date" )
			date_and_time = "{}-{}-{}-1930".format(
								self.kwargs['year'],
								self.kwargs['month'],
								self.kwargs['day'] )
			report_dt = timezone.make_aware(timezone.datetime.strptime( "{}-{}-{}".format( 
								self.kwargs['year'], self.kwargs['month'], self.kwargs['day']),
								"%Y-%m-%d" ))
			#context['is_active'] = True
		else:
			report_dt = self.request.user.profile.active_report.report_date.astimezone(
								timezone.get_default_timezone())
			date_and_time = report_dt.strftime( "%Y-%m-%d-%H%M" ) 
			#context['is_active'] = False
		if DailyReport.objects.get( 
				report_date__date = report_dt.date() ) == self.request.user.profile.active_report:
			context['is_active'] = True
		else:
			context['is_active'] = False
					
		print("date_and_time={}".format(report_dt))

		qset = Photo.objects.filter( 
			daily_report_item__daily_report__report_date__date = report_dt.date()).order_by(
					'daily_report_item__reportOrder' )
		context['photo_list'] = qset
		print( "debug: dailyreport_edit report_dt={}".format( report_dt ) )
		qset = DailyReportItem.objects.filter( daily_report__report_date__date = report_dt.date()).order_by(
					'reportOrder' )
		context['daily_report_item_list'] = qset 
		return context

	pass


class DailyReportMonthArchiveView(DailyReportDateView, MonthArchiveView):
	pass 

class DailyReportYearArchiveView(DailyReportDateView, YearArchiveView):
	make_object_list = True

# Update Forms

def Update_PhotoGroup( request, photo_group_pk ):
	print( u"DEBUG: photo_group_pk = {}".format( photo_group_pk ) )
	print( u"DEBUG: active_photogroup = {}".format( request.user.profile.active_photogroup ) )
	q_photogroup = request.user.profile.active_photogroup
	for q_photo_pk in request.POST.getlist('add_photo'):
		print( u"adding q_photo_pk={}".format( q_photo_pk ) )
		q_photo = Photo.objects.get( pk = q_photo_pk )
		q_photogroup.photos.add( q_photo )
	for q_photo_pk in request.POST.getlist('delete_photo'):
		print( u"deleting q_photo_pk={}".format( q_photo_pk))
		q_photo = Photo.objects.get( pk = q_photo_pk )
		q_photogroup.photos.remove( q_photo )
	
	if request.POST.has_key('delete_photo'):
		return HttpResponseRedirect( reverse(
			'photologue:monthly-report-detail', args=[ photo_group_pk ] ) )
	else:
		return HttpResponseRedirect( reverse( 'photologue:message-success' ) )
	

def Update_DailyReportItem( request, daily_report_pk=None, daily_report_item_pk=None ):
	print( u"DEBUG: daily_report_pk = {} daily_report_item_pk = {} // request.POST= {}".format (
			 daily_report_pk, daily_report_item_pk, request.POST.getlist('report_photo'))) 
	print( u"DEBUG: submit department_item_pk = {}".format(
			 request.POST.getlist('department_pk')))
	redirect_url = reverse( 'photologue:report_item_list_view' )
	if '2017' not in daily_report_item_pk:
	#if not isinstance(daily_report_item_pk, basestring):
	#if daily_report_item_pk:
#		date_time = timezone.datetime.strptime( 
#				"%Y-%m-%d-%H%M", daily_report_item_pk )
		q_dri = DailyReportItem.objects.get( pk = daily_report_item_pk )
		date_time = q_dri.daily_report.report_date
		redirect_url = reverse( 'photologue:photo-select-popup-list',
				kwargs = {'year':date_time.year,
						  'month':date_time.month,
						  'day':date_time.day,
						  'target':'dailyreport',
						  'pk':q_dri.pk }
				)
		for q_photo_pk in request.POST.getlist('add_photo' ):
			q_photo = Photo.objects.get( pk = int(q_photo_pk) )
			q_photo.daily_report_item.add( q_dri )
			q_photo.department_item = q_dri.department_item
			q_photo.save()

	for q_photo_pk in request.POST.getlist('report_photo'):
		print( u"updating pk:{} related daily_report_item".format(q_photo_pk) )
		q_photo = Photo.objects.get( pk = int(q_photo_pk) )
		q_related_daily_report_item = q_photo.get_related_daily_report_item()
		q_photo.daily_report_item.add( q_related_daily_report_item )
		q_photo.save()
	for q_photo_pk in request.POST.getlist('delete_photo'):
		print( u"removing pk:{} related daily_report_item".format(q_photo_pk) )
		q_photo = Photo.objects.get( pk = int(q_photo_pk) )
		q_related_daily_report_item = q_photo.get_related_daily_report_item()
		q_photo.daily_report_item.remove(
								q_related_daily_report_item)
		#q_photo.save()
	return HttpResponseRedirect( redirect_url )

class PhotoCatagorize(ListView):
	template_name = "photologue/photo_catagorize.html"

	def get_queryset(self):
		print( "photo_catagorize queryset={0}".format( self.kwargs )  )
		#date_and_time = timezone.datetime.strptime( "20170721", "%Y%m%d" )
		date_and_time = timezone.localtime()#datetime.strptime( "20170722", "%Y%m%d" )
		qset = Photo.objects.filter( date_added__date = date_and_time )
		return qset
	
def SetPhotoDepartmentItem( request ):
	try:
		department_pk = request.POST.getlist('department_pk')[0]
	except:
		return HttpResponseRedirect( reverse( 'photologue:photo_catagorize' ) )
	q_department_item = DepartmentItem.objects.get( pk = department_pk )
	print( "set_dailyreportitem:department={}".format( department_pk ) )
	try:
		list_set_photo = request.POST.getlist('set_photo')
	except:
		return HttpResponseRedirect( reverse( 'photologue:photo_catagorize' ) )
	for set_photo in list_set_photo:
		print( "set_dailyreportitem:{}".format( set_photo))
		q_photo = Photo.objects.get( pk = set_photo )
		q_photo.department_item = q_department_item
		q_photo.save()
	return HttpResponseRedirect( reverse( 'photologue:photo_catagorize' ) )

#def ReportItemListView( request):
#	print( "reportitemlistview called" )
#	queryset = ReportItem.objects.all()
##	paginate_by = 20
#	context = {'qset_report_item': queryset}
#	return render( request, 'photologue/reportitem_list.html',context )
def handle_photo_upload(f):
	filepath = os.path.join('/tmp/',f.name )
	with open( filepath, 'wb+' ) as destination:
		for chunk in f.chunks():
			destination.write(chunk)
		destination.close()

def photosave( filename, content ):
	print("photosave: photo begin")
	p = Photo( title=filename, 
				slug=slugify(filename) )
	print("photosave: photo image save")

@csrf_exempt
def PhotoUploadView( request ):

	logger( "TestFormView request={}".format( request.POST ) ) 
	logger( "TestFormView request={}".format( request.FILES ) ) 
	#return HttpResponseRedirect( reverse( 'admin:login' ))
	if request.method == 'POST':
		form = PhotoUploadForm(request.POST, request.FILES)
		if form.is_valid():
			print( "photouploadview: form.is_valid() true" )
			handle_photo_upload( request.FILES['my_file'] ) 
			filepath = os.path.join('/tmp',request.FILES['my_file'].name)
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
			print( "photo  save" )
			ph.save()
			print( "photo  site" )
			ph.sites.add(Site.objects.get(id=settings.SITE_ID))
			
			print( "photo finish" )
		else:
			logger( "photouploadview: form.is_valid() false" )
	return render( request, 'photologue/photo_upload.html', {
			'title': 'Photo Upload View',
			'name2': 'test_form2',
		})
	#return HttpResponse( "Success" )

def SortableSubmitTest( request, photo_group_pk ):
	print('debug: SortableSubmitTest {}'.format( request.POST ) )
	for q_photo_pk in request.POST.getlist('photo_order'):
			print( "order:{}".format( q_photo_pk  ) ) 

	return HttpResponseRedirect( 
			reverse( 'photologue:test-sortable', args=[photo_group_pk]
				) )
	

# Gallery views.

class GalleryListView(ListView):
	queryset = Gallery.objects.on_site().is_public()
	paginate_by = 20


class GalleryDetailView(DetailView):
	queryset = Gallery.objects.on_site().is_public()


class GalleryDateView(object):
	queryset = Gallery.objects.on_site().is_public()
	date_field = 'date_added'
	allow_empty = True


class GalleryDateDetailView(GalleryDateView, DateDetailView):
	pass


class GalleryArchiveIndexView(GalleryDateView, ArchiveIndexView):
	pass


class GalleryDayArchiveView(GalleryDateView, DayArchiveView):
	pass


class GalleryMonthArchiveView(GalleryDateView, MonthArchiveView):
	pass


class GalleryYearArchiveView(GalleryDateView, YearArchiveView):
	make_object_list = True

# Photo views.


class PhotoListView(ListView):
	queryset = Photo.objects.on_site().is_public()
	paginate_by = 20


class PhotoDetailView(DetailView):
	queryset = Photo.objects.on_site().is_public()


class PhotoDateView(object):
	queryset = Photo.objects.on_site().is_public()
	date_field = 'date_added'
	allow_empty = True


class PhotoDateDetailView(PhotoDateView, DateDetailView):
	pass


class PhotoArchiveIndexView(PhotoDateView, ArchiveIndexView):
	pass


class PhotoDayArchiveView(PhotoDateView, DayArchiveView):
	pass


class PhotoMonthArchiveView(PhotoDateView, MonthArchiveView):
	pass


class PhotoYearArchiveView(PhotoDateView, YearArchiveView):
	make_object_list = True


# Deprecated views.

class DeprecatedMonthMixin(object):

	"""Representation of months in urls has changed from a alpha representation ('jan' for January)
	to a numeric representation ('01' for January).
	Properly deprecate the previous urls."""

	query_string = True

	month_names = {'jan': '01',
				   'feb': '02',
				   'mar': '03',
				   'apr': '04',
				   'may': '05',
				   'jun': '06',
				   'jul': '07',
				   'aug': '08',
				   'sep': '09',
				   'oct': '10',
				   'nov': '11',
				   'dec': '12', }

	def get_redirect_url(self, *args, **kwargs):
		print('a')
		warnings.warn(
			DeprecationWarning('Months are now represented in urls by numbers rather than by '
							   'their first 3 letters. The old style will be removed in Photologue 3.4.'))


class GalleryDateDetailOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(GalleryDateDetailOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:gallery-detail', kwargs={'year': kwargs['year'],
															'month': self.month_names[kwargs['month']],
															'day': kwargs['day'],
															'slug': kwargs['slug']})


class GalleryDayArchiveOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(GalleryDayArchiveOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:gallery-archive-day', kwargs={'year': kwargs['year'],
																 'month': self.month_names[kwargs['month']],
																 'day': kwargs['day']})


class GalleryMonthArchiveOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(GalleryMonthArchiveOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:gallery-archive-month', kwargs={'year': kwargs['year'],
																   'month': self.month_names[kwargs['month']]})


class PhotoDateDetailOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(PhotoDateDetailOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:photo-detail', kwargs={'year': kwargs['year'],
														  'month': self.month_names[kwargs['month']],
														  'day': kwargs['day'],
														  'slug': kwargs['slug']})


class PhotoDayArchiveOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(PhotoDayArchiveOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:photo-archive-day', kwargs={'year': kwargs['year'],
															   'month': self.month_names[kwargs['month']],
															   'day': kwargs['day']})


class PhotoMonthArchiveOldView(DeprecatedMonthMixin, RedirectView):
	permanent = True

	def get_redirect_url(self, *args, **kwargs):
		super(PhotoMonthArchiveOldView, self).get_redirect_url(*args, **kwargs)
		return reverse('photologue:photo-archive-month', kwargs={'year': kwargs['year'],
																 'month': self.month_names[kwargs['month']]})

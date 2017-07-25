import warnings 
import os
from io import BytesIO

try:
	import Image
except ImportError:
	from PIL import Image

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
						  Department, DailyReport

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


# ReportItem Views
class DailyReportDateView(object):
	queryset = Photo.objects.all()
	date_field = 'date_added'
	allow_empty = True

#@login_required
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
			date_and_time = '2017-07-25-1930'

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


class DailyReportDayArchiveView(DailyReportDateView, DayArchiveView):
	template_name = "photologue/dailyreport_edit.html"
	date_and_time = timezone.localtime()
	def get_context_data( self, **kwargs):
		context = super(DayArchiveView, self).get_context_data(**kwargs)
		context['daily_report'] = DailyReport.objects.all()
		return context
	def get_queryset(self):
		print( "DailyReportdayArchiveView:{}".format( self.kwargs ))
	#	date_and_time = '2017-07-25-1930'
		date_and_time = "{}-{}-{}-1930".format(
								self.kwargs['year'],
								self.kwargs['month'],
								self.kwargs['day'] )
		print( "date_and_time={}".format(date_and_time))
		qset = Photo.objects.filter( daily_report_item__daily_report__title = date_and_time ).order_by( 'daily_report_item__reportOrder' ) 
		return qset

	pass


class DailyReportMonthArchiveView(DailyReportDateView, MonthArchiveView):
	pass


class DailyReportYearArchiveView(DailyReportDateView, YearArchiveView):
	make_object_list = True

def Update_DailyReportItem( request, daily_report_pk ):
	print( "DEBUG: daily_report_pk = {} // request.POST= {}".format (
			 daily_report_pk, request.POST.getlist('report_photo'))) 
	print( "DEBUG: submit department_item_pk = {}".format(
			 request.POST.getlist('department_pk')))
	for q_photo_pk in request.POST.getlist('report_photo'):
		print( "updating pk:{} related daily_report_item".format(q_photo_pk) )
		q_photo = Photo.objects.get( pk = int(q_photo_pk) )
		q_related_daily_report_item = q_photo.get_related_daily_report_item()
		q_photo.daily_report_item.add( q_related_daily_report_item )
		q_photo.save()
	for q_photo_pk in request.POST.getlist('delete_photo'):
		print( "removing pk:{} related daily_report_item".format(q_photo_pk) )
		q_photo = Photo.objects.get( pk = int(q_photo_pk) )
		q_related_daily_report_item = q_photo.get_related_daily_report_item()
		q_photo.daily_report_item.remove(
								q_related_daily_report_item)
		#q_photo.save()
	return HttpResponseRedirect( reverse( 'photologue:report_item_list_view' ))

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

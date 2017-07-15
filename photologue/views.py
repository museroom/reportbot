import warnings

from django.views.generic.dates import ArchiveIndexView, DateDetailView,  \
													DayArchiveView, MonthArchiveView, \
													YearArchiveView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse

from django.views.generic import View
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Photo, Gallery, DailyReportItem, ReportItem, \
						  Department, DailyReport

import time, datetime
from HTMLParser import HTMLParser

from utils.logger import logger

# Json Query.
def JsonPhotoQuery( request, report_item, date_and_time ):
	log_text = "JsonPhotoQueue {}{}".format( 
		report_item, date_and_time ) 
	logger(  log_text, 'DEBUG' )
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
								 "name":item.daily_report_item.name,
								 "pk":str(item.pk),
								 "template":item.tableTemplate,
								 "row_photo":item.photoCol,
								 })
		
		#rsp.append( { "name":item.daily_report_item.name, 
		#rspGroup.append( rsp )
	logger( dict(log=rsp), is_json=True )
	return JsonResponse(dict(tableMap=rsp)) #, safe= False )
		
def JsonReportItemQuery( request, report_pk ):
	logger( "JsonReportItemQuery {}".format( 
		report_pk ) , 'DEBUG' )

	HTMLrsp = []
	
	class PrettyHTML( HTMLParser ):
		def handle_starttag( self, tag, attrs ):
			#print( "start tag:", tag )
			#print( "start attrs", attrs )
			HTMLrsp.append( {"startTag":tag} )
			HTMLrsp.append( {"startAttrs":attrs} )
		def handle_endtag( self, tag ):
			#print( "end tag:", tag )
			HTMLrsp.append( {"endTag":tag} )
		def handle_data( self, data ):
			#print( "data:", data )
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
	parser.feed( qset.statusCK )
	HTMLstatus = HTMLrsp
	HTMLrsp = []
	parser.feed( qset.planCK )
	HTMLplan = HTMLrsp
	HTMLrsp = []
	parser.feed( qset.status_TOC_CK )
	HTMLstatus_toc = HTMLrsp
	HTMLrsp = []
	parser.feed( qset.plan_TOC_CK )
	HTMLplan_toc = HTMLrsp

	# if TOC content empty, copy from table HTML text for lazy ass
	if len(HTMLstatus_toc) == 0:
		HTMLstatus_toc = HTMLstatus
	if len(HTMLplan_toc) == 0:
		HTMLplan_toc = HTMLplan

	rspGroup.append ({
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
						"department":qset.daily_report_item.department.name,
						"daily_report_item":qset.daily_report_item.name,
						"direction":qset.daily_report_item.location,
						"name_long":qset.daily_report_item.name_long, 
						});
	#return JsonResponse(list(qset.values('image')), safe=False)
	#return JsonResponse(HTMLrsp, safe=False)
	logger( rspGroup, is_json=True )
	return JsonResponse(dict(reportItems=rspGroup) ) #, safe=False)


# ReportItem Views
#@login_required
class ReportItemListView(ListView):
	qset_report_item = ReportItem.objects.all()
	queryset = qset_report_item
	paginate_by = 20

#def ReportItemListView( request):
#	print( "reportitemlistview called" )
#	queryset = ReportItem.objects.all()
##	paginate_by = 20
#	context = {'qset_report_item': queryset}
#	return render( request, 'photologue/reportitem_list.html',context )

	

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

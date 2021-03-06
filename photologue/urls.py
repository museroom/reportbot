from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.translation import ugettext as _
from django.contrib import admin
from django.utils import timezone 

from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView

from .models import Photo, DailyReportItem, Department, DepartmentItem, Profile, \
					PhotoGroup 

from .views import PhotoListView, PhotoDetailView, GalleryListView, \
	GalleryDetailView, PhotoArchiveIndexView, PhotoDateDetailView, PhotoDayArchiveView, \
	PhotoYearArchiveView, PhotoMonthArchiveView, GalleryArchiveIndexView, \
	GalleryYearArchiveView, GalleryDateDetailView, GalleryDayArchiveView, \
	GalleryMonthArchiveView, GalleryDateDetailOldView, GalleryDayArchiveOldView, \
	GalleryMonthArchiveOldView,  PhotoDateDetailOldView, PhotoDayArchiveOldView, \
	PhotoMonthArchiveOldView, JsonReportItemQuery, JsonPhotoQuery, JsonTableMapQuery, \
	DailyReportListView, DailyReportDetailView, DailyReportArchiveIndexView, \
	DailyReportDayArchiveView, DailyReportMonthArchiveView, \
	Update_DailyReportItem, Update_PhotoGroup, Create_PhotoGroup,\
    PhotoUploadView, PhotoCatagorize, \
	SetPhotoDepartmentItem, PhotoSelectListView, MonthlyReportListView, \
	MonthlyReportDetailView, SortableSubmitTest, MonthlyReportPhotoReorder, \
	GenerateXLSX, GenerateXLSXAll, PhotoGroupPMView, PhotoGroupCMView, \
	SetActivePhotoGroupView, AddPhotoActivePhotoGroupView, \
	Set_dbField_PhotoGroup, \
	InventoryListView, InventoryTypeDetail, InventoryTypeCreate, InventoryCheckout, \
	InventorySet, InventoryItemDetail, InventoryTypeUpdate, InventoryItemUpdate, \
	InventoryItemAddPhoto, InventoryItemRemovePhoto, \
	InstanceMessageCreate

"""NOTE: the url names are changing. In the long term, I want to remove the 'pl-'
prefix on all urls, and instead rely on an application namespace 'photologue'.

At the same time, I want to change some URL patterns, e.g. for pagination. Changing the urls
twice within a few releases, could be confusing, so instead I am updating URLs bit by bit.

The new style will coexist with the existing 'pl-' prefix for a couple of releases.

"""

dt = timezone.localtime() 

urlpatterns = [
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[0-9]{2})/(?P<day>\w{1,2})/(?P<slug>[\-\d\w]+)/$',
		GalleryDateDetailView.as_view(month_format='%m'),
		name='gallery-detail'),
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[0-9]{2})/(?P<day>\w{1,2})/$',
		GalleryDayArchiveView.as_view(month_format='%m'),
		name='gallery-archive-day'),
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[0-9]{2})/$',
		GalleryMonthArchiveView.as_view(month_format='%m'),
	name='gallery-archive-month'),
	url(r'^gallery/(?P<year>\d{4})/$',
		GalleryYearArchiveView.as_view(),
		name='pl-gallery-archive-year'),
	url(r'^gallery/$',
		GalleryArchiveIndexView.as_view(),
		name='pl-gallery-archive'),
	url(r'^$',
		RedirectView.as_view(
			url=reverse_lazy('photologue:pl-gallery-archive'), permanent=True),
		name='pl-photologue-root'),
	url(r'^gallery/(?P<slug>[\-\d\w]+)/$',
		GalleryDetailView.as_view(), name='pl-gallery'),
	url(r'^gallerylist/$',
		GalleryListView.as_view(),
		name='gallery-list'),
	
	url(r'^photo/(?P<year>\d{4})/(?P<month>[0-9]{2})/(?P<day>\w{1,2})/(?P<slug>[\-\d\w]+)/$',
		PhotoDateDetailView.as_view(month_format='%m'),
		name='photo-detail'),
	url(r'^photo/(?P<year>\d{4})/(?P<month>[0-9]{2})/(?P<day>\w{1,2})/$',
		PhotoDayArchiveView.as_view(month_format='%m'),
		name='photo-archive-day'),
	url(r'^photo/(?P<year>\d{4})/(?P<month>[0-9]{2})/$',
		PhotoMonthArchiveView.as_view(month_format='%m'),
		name='photo-archive-month'),
	url(r'^photo/(?P<year>\d{4})/$',
		PhotoYearArchiveView.as_view(),
		name='pl-photo-archive-year'),
	url(r'^photo/$',
		PhotoArchiveIndexView.as_view(),
		name='pl-photo-archive'),
	
	url(r'^photo/(?P<slug>[\-\d\w]+)/$',
		PhotoDetailView.as_view(), name='pl-photo'), 
	url(r'^photolist/$',
		PhotoListView.as_view(),
		name='photo-list'),
	
	# TinyMCE inte)race
	url(r'^tinymce/', include('tinymce.urls')),
	
	# Report Bot Json interface
	url(r'^json/TableMap/(?P<date_and_time>[\-\d\w|\W]+)/$',
		JsonTableMapQuery, name='jsontable'),
	url(r'^json/ReportItem/(?P<report_pk>[\d]+)/$',
		JsonReportItemQuery),
	url(r'^json/Photo/(?P<report_item>[\-\d\w|\W]+)/(?P<date_and_time>[\-\d\w|\W]+)/$',
		JsonPhotoQuery),

	# Photo Group Views
	url(r'^monthlyreport/$',
		MonthlyReportListView.as_view(),
		name = 'monthly-report-list' ),
	url(r'^monthlyreport/(?P<pk>[\d]+)/$',
		MonthlyReportDetailView.as_view(),
		name = 'monthly-report-detail' ), 
	
	# Report Item Views
	url(r'^reportitemlist/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', 
		DailyReportDayArchiveView.as_view(month_format='%m'), 
		name="dailyreport-edit"),
	url(r'^reportitemlist/(?P<year>\d{4})/(?P<month>[0-9]{2})/$', 
		DailyReportMonthArchiveView.as_view(month_format='%m'), 
		name="dailyreport-archive-month"),
	url(r'^reportitemlist/$',
		DailyReportDayArchiveView.as_view(month_format='%m', 
			year=str(dt.year), month=str(dt.month), day=str(dt.day) ),
		name="report_item_list_view"),
	url(r'^update_dailyreportitem/(?P<daily_report_item_pk>\d+)/$',
		Update_DailyReportItem, name="update_dailyreportitem"),
	url(r'^update_dailyreportitem/title/(?P<daily_report_pk>[\-\d\w|\W]+)$',
		Update_DailyReportItem, name="update_dailyreport"),
	url(r'^update_photogroup/(?P<photo_group_pk>[\-\d\w|\W]+)/$',
		Update_PhotoGroup, name="update_photogroup"),
	url(r'^photogroup/create/(?P<photo_pk>\d+)/$',
	    Create_PhotoGroup, name='create-photogroup'),
	url(r'^photogroup/set/(?P<record_type>\w+)/(?P<photogroup_id>\d+)',
		Set_dbField_PhotoGroup, name='set-photogroup-record-type'),
#	url(r'^catagorize/(?P<date_and_time>[\-\d\w|\W]+)/$',
	url(r'^catagorize/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$',
		PhotoCatagorize.as_view(), name="photo_catagorize_date"),
	url(r'^catagorize/$',
		PhotoCatagorize.as_view(), name="photo_catagorize"),
	url(r'^set_dailyreportitem/$',
		SetPhotoDepartmentItem, name="set_dailyreportitem"),
	# IM / forum
	url(r'^testform/$',
		PhotoUploadView, name="upload_photo"),
	url(r'^im/create/$',
		InstanceMessageCreate, name="im_create"), 

	# AJAX form create views
	url(r'^photogroup/pm/edit/(?P<pk>\d+)/$', 
		PhotoGroupPMView.as_view(),
	    name = 'photogroup-pm-edit' ),
	url(r'^photogroup/cm/edit/(?P<pk>\d+)/$', 
		PhotoGroupCMView.as_view(),
	    name = 'photogroup-cm-edit' ), 
	url(r'^photogroup/active/set/(?P<pk>\d+)/$',
		SetActivePhotoGroupView,
		name = 'set-active-photogroup' ),
	url(r'^photogroup/photo/add/(?P<photo_pk>\d+)/$',
		AddPhotoActivePhotoGroupView,
		name = 'add-photogroup-photo' ),

	# Inventory
	url(r'^inventory/$',
		InventoryListView.as_view(),
		name = 'inventory-list' ),
	url(r'^inventory/(?P<pk>\d+)/$',
		InventoryTypeDetail.as_view(),
		name = 'inventorytype-detail' ),
	url(r'^inventory/create/$',
		InventoryTypeCreate.as_view(),
		name = 'inventory-create' ),
	url(r'^inventory/checkout/$',
		InventoryCheckout,
		name = 'inventory-checkout' ),
	url(r'^inventory/set/(?P<photo_pk>\d+)/$',
		InventorySet,
		name = 'inventory-set' ),
	url(r'^inventory/item/(?P<pk>\d+)/$',
		InventoryItemDetail.as_view(),
		name = 'inventoryitem-detail' ),
	url(r'^inventory/update/(?P<pk>\d+)/$',
		InventoryTypeUpdate.as_view(),
		name = 'inventorytype-update' ),
	url(r'^inventory/item/update/(?P<pk>\d+)/$',
		InventoryItemUpdate.as_view(),
		name = 'inventoryitem-update' ),
	url(r'^inventory/item/photo/update/(?P<pk>\d+)/$',
		InventoryItemAddPhoto,
		name = 'inventoryitem-photo-update' ),
	url(r'^inventory/item/photo/remove/(?P<pk>\d+)/$',
		InventoryItemRemovePhoto,
		name = 'inventoryitem-photo-remove' ),
	

	# Photo Selector Popup
	url(r'^photoselect/(?P<year>\d{4})/(?P<month>\w{1,2})/(?P<day>\w{1,2})/(?P<target>[\w|\W]+)/(?P<pk>\d+)/$',
		PhotoSelectListView.as_view(), name = 'photo-select-popup-list' ), 

    # General Message Redirect View
    url(r'^message/success/$',
            TemplateView.as_view( template_name='photologue/message_success.html'), name='message-success' ),
	url(r'^gotoedit/$',
			RedirectView.as_view(
				url=reverse_lazy('photologue:dailyreport-edit', kwargs={'year':2017,'month':8,'day':7}))),

	# -testes-
	# Sortable.js 
	url(r'^sortable/(?P<pk>\d+)/$',
			MonthlyReportPhotoReorder.as_view(), 
		#	DetailView.as_view( model=PhotoGroup, template_name='photologue/test-sortable.html'),
		   # TemplateView.as_view(template_name='photologue/test-sortable.html'), 
			name='test-sortable' ),
	url(r'^sortable/submit/(?P<photo_group_pk>\d+)/$',
			SortableSubmitTest,
			name='test-submit-sortable' ),

	# OpenPyXL output XLSX url
	url(r'^xlsx/download/(?P<photo_group_pk>\d+)/$',
			GenerateXLSX,
			name='generate-xlsx' ),
	url(r'^xlsx/download/all/$',
			GenerateXLSXAll,
			name='generate-xlsx-all' ),

	# Deprecated URLs.
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[\-\d\w]+)/$',
		GalleryDateDetailOldView.as_view(),
		name='pl-gallery-detail'),
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
		GalleryDayArchiveOldView.as_view(),
		name='pl-gallery-archive-day'),
	url(r'^gallery/(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
		GalleryMonthArchiveOldView.as_view(),
		name='pl-gallery-archive-month'),
	url(r'^photo/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[\-\d\w]+)/$',
		PhotoDateDetailOldView.as_view(),
		name='pl-photo-detail'),
	url(r'^photo/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
		PhotoDayArchiveOldView.as_view(),
		name='pl-photo-archive-day'),
	url(r'^photo/(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
		PhotoMonthArchiveOldView.as_view(),
		name='pl-photo-archive-month')
]

# Administration Page Customization
admin.site.site_header = _("MeiTim ReportBot Administration System")
admin.site.site_title = _("ReportBot")


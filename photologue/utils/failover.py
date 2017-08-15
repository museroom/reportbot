from photologue.models import DepartmentItem

# FIXME a good starting point for deep learning
def get_department_item_failover():
	return DepartmentItem.objects.get( 
	          name = "Unknown", 
			  department__name = "Unknown",
			  department__company__name = "Unknown" )

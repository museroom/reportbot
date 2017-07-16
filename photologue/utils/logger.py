from google.cloud import logging
from django.utils.safestring import SafeString

def logger( log_text, level='', is_json=False,
				cloud_log = True,log_target='report_bot', 
				):
	my_log = logging.Client().logger( log_target )
	if cloud_log:
		if is_json:
#			log_text_safe = SafeString(log_text)
#			my_log.log_struct( dict(struct=log_text_safe) ) 
			my_log.log_struct( dict(struct=log_text) ) 
		elif level != '':
			my_log.log_text( log_text, severity=level ) 
		else:
			my_log.log_text( log_text )
	if is_json == True:
		print( "{0}: {1}".format( level, log_text ) )
	else:
		print( log_text )


# -*- coding: utf-8 -*-

import json

fn_config = 'example_project/static/xlsx/sc-config.json'

style_cells_bottom = { 
	'B5:C5', 'F5:G5', 'B6:C6', 'F6:G6', 'F7:G7',
	'F29:G29', 
	}

style_cells_square = { 
	'B9:E9', 'F9:G9',
	'B10:E10', 'B11:E11', 'B12:E12', 'B13:E13', 'B14:E14', 'B15:E15', 'B16:E16', 'B17:E17',
	'B18:E18', 'A19:G19', 'B20:E20', 'B21:E21', 'B22:E22', 'B23:E23',
	'F10:G10', 'F11:G11', 'F12:G12', 'F13:G13', 'F14:G14',
	'F15:G15', 'F16:G16', 'F17:G17', 'F18:G18', 
	'F20:G20', 'F21:G21', 'F22:G22', 'F23:G23', 
	}

cm_headers = (
	{ 'cell':{'left':'C', 'right':'J', 'row':2}, 'align':'center', 'text':u'美添光管冷氣FLORESCENTE E AR-CONDICIONADO' },
	{ 'cell':{'left':'D', 'right':'H', 'row':4}, 'align':'center', 'text':u'CM REPORT' },
	{ 'cell':{'left':'F', 'right':'H', 'row':6}, 'align':'right', 'text':u'Report Ref報告編號 : '},
	{ 'cell':{'left':'G', 'right':'H', 'row':7}, 'align':'right', 'text':u'Date 日期 : '}, 
	{ 'cell':{'left':'I', 'right':'J', 'row':6}, 'align':'left', 'text':'' },
	{ 'cell':{'left':'I', 'right':'J', 'row':7}, 'align':'left', 'text':'' },
)

#configs = {style_cells_bottom, style_cells_square, headers }
configs = {}
#for config in (style_cells_bottom, style_cells_square, cm_headers):
#	configs.append( config )
configs = { 'cm_headers':cm_headers }

j_configs = json.dumps( configs, sort_keys=False, indent=4, separators=(',',': '), ensure_ascii=False).encode('utf8')

f_config = open( fn_config, 'w' )
f_config.write( j_configs )
f_config.close()
print( j_configs )


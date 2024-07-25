# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, format_datetime, format_duration
from operator import itemgetter

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)
	report_summary = get_report_summary(data)
	return columns, data, None, chart, report_summary




present_records=45



def get_columns():
	return [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 220,
		},
		{
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"label": _("Employee Name"),
			"width": 0,
			"hidden": 1,
		},
		{
			"label": _("Shift"),
			"fieldname": "shift",
			"fieldtype": "Link",
			"options": "Shift Type",
			"width": 120,
		},
		{
			"label": _("Attendance Date"),
			"fieldname": "attendance_date",
			"fieldtype": "Date",
			"width": 130,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"label": _("Shift Start Time"),
			"fieldname": "shift_start",
			"fieldtype": "Data",
			"width": 125,
		},
		{
			"label": _("Shift End Time"),
			"fieldname": "shift_end",
			"fieldtype": "Data",
			"width": 125,
		},
		{
			"label": _("In Time"),
			"fieldname": "in_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Breack In Time"),
			"fieldname": "custom_breack_in_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Breack Out Time"),
			"fieldname": "custom_breack_out_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Out Time"),
			"fieldname": "out_time",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Total Working Hours"),
			"fieldname": "working_hours",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Breack Hours"),
			"fieldname": "custom_breack_hours",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Overtime"),
			"fieldname": "overtime_hrs",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Late Entry By"),
			"fieldname": "late_entry_hrs",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Early Exit By"),
			"fieldname": "early_exit_hrs",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		},
		{
			"label": _("Shift Actual Start Time"),
			"fieldname": "shift_actual_start",
			"fieldtype": "Data",
			"width": 165,
		},
		{
			"label": _("Shift Actual End Time"),
			"fieldname": "shift_actual_end",
			"fieldtype": "Data",
			"width": 165,
		},
		{
			"label": _("Attendance ID"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Attendance",
			"width": 150,
		},
		{
			"label": _("Leave Type"),
			"fieldname": "leave_type",
			"fieldtype": "Link",
			"options": "Attendance",
			"width": 150,
		},
	]

def get_data(filters):
	query = get_query(filters)
	data = query.run(as_dict=True)
	data = update_data(data, filters)


# \ get absent abd leave records
	absent_records_filters={"status":["!=","Present"],"docstatus":1,"attendance_date":['between', [filters.from_date,filters.to_date]]}
	if filters.employee:
		absent_records_filters["employee"]=filters.employee

	if filters.department:
		absent_records_filters["department"]=filters.department

	
	absent_records= frappe.get_all("Attendance",fields="*",filters=absent_records_filters)
	data+=absent_records
# / 

# \ get holiday records
	data+=get_holidaies(get_emps(data),filters)
# / 
	newdata = sorted(data, key=itemgetter('attendance_date'))
	return newdata

	 
def get_report_summary(data):
	if not data:
		return None

	present_records = half_day_records = absent_records = late_entries = early_exits = leave_entries= overtime = 0


	
	for entry in data:
		if entry.status == "Present":
			present_records += 1
		elif entry.status == "Half Day":
			half_day_records += 1
		elif entry.status=="Absent":
			absent_records += 1
		elif entry.status=="On Leave":
			leave_entries += 1
		
		if entry.late_entry:
			late_entries += 1
		if entry.early_exit:
			early_exits += 1

		if entry.overtime:
			overtime += 1

	return [
		{
			"value": present_records,
			"indicator": "Green",
			"label": _("Present Records"),
			"datatype": "Int",
		},
		{
			"value": half_day_records,
			"indicator": "Blue",
			"label": _("Half Day Records"),
			"datatype": "Int",
		},
		{
			"value": absent_records,
			"indicator": "Red",
			"label": _("Absent Records"),
			"datatype": "Int",
		},
		{
			"value": leave_entries,
			"indicator": "Red",
			"label": _("Leave Records"),
			"datatype": "Int",
		},
		{
			"value": late_entries,
			"indicator": "Red",
			"label": _("Late Entries"),
			"datatype": "Int",
		},
		{
			"value": early_exits,
			"indicator": "Red",
			"label": _("Early Exits"),
			"datatype": "Int",
		},
		{
			"value": overtime,
			"indicator": "Blue",
			"label": _("Overtime"),
			"datatype": "Int",
		},
			
	]


def get_chart_data(data):
	if not data:
		return None

	total_shift_records = {}
	for entry in data:
		total_shift_records.setdefault(entry.shift, 0)
		total_shift_records[entry.shift] += 1

	labels = [_(d) for d in list(total_shift_records)]
	chart = {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Shift"), "values": list(total_shift_records.values())}],
		},
		"type": "percentage",
	}
	return chart


def get_query(filters):
	attendance = frappe.qb.DocType("Attendance")
	checkin = frappe.qb.DocType("Employee Checkin")
	shift_type = frappe.qb.DocType("Shift Type")


	query = (
		frappe.qb.from_(attendance)
		.inner_join(checkin)
		.on(checkin.attendance == attendance.name)
		.inner_join(shift_type)
		.on(attendance.shift == shift_type.name)
		.select(
			attendance.name,
			attendance.employee,
			attendance.employee_name,
			attendance.shift,
			attendance.attendance_date,
			attendance.status,
			attendance.in_time,
			attendance.out_time,
			attendance.working_hours,
			attendance.custom_breack_in_time,
			attendance.custom_breack_out_time,
			attendance.custom_breack_hours,
			attendance.late_entry,
			attendance.early_exit,
			attendance.department,
			attendance.company,
			checkin.shift_start,
			checkin.shift_end,
			checkin.shift_actual_start,
			checkin.shift_actual_end,
			shift_type.enable_late_entry_marking,
			shift_type.late_entry_grace_period,
			shift_type.enable_early_exit_marking,
			shift_type.early_exit_grace_period,
		)
		.where(attendance.docstatus == 1)
		.groupby(attendance.name)
	)

	for filter in filters:
		if filter == "from_date":
			query = query.where(attendance.attendance_date >= filters.from_date)
		elif filter == "to_date":
			query = query.where(attendance.attendance_date <= filters.to_date)
		elif filter == "consider_grace_period":
			continue
		elif filter == "late_entry" and not filters.consider_grace_period:
			query = query.where(attendance.in_time > checkin.shift_start)
		elif filter == "early_exit" and not filters.consider_grace_period:
			query = query.where(attendance.out_time < checkin.shift_end)
		else:
			query = query.where(attendance[filter] == filters[filter])

	return query


def update_data(data, filters):
	for d in data:
		update_late_entry(d, filters.consider_grace_period)
		update_early_exit(d, filters.consider_grace_period)
		update_overtime(d)
		
		d.working_hours = format_float_precision(d.working_hours)
		d.in_time, d.out_time = format_in_out_time(d.in_time, d.out_time, d.attendance_date)
		d.custom_breack_in_time, d.custom_breack_out_time= format_in_out_time(d.custom_breack_in_time, d.custom_breack_out_time, d.attendance_date)
		d.shift_start, d.shift_end = convert_datetime_to_time_for_same_date(d.shift_start, d.shift_end)
		d.shift_actual_start, d.shift_actual_end = convert_datetime_to_time_for_same_date(
			d.shift_actual_start, d.shift_actual_end
		)
	return data


def format_float_precision(value):
	precision = cint(frappe.db.get_default("float_precision")) or 2
	return flt(value, precision)


def format_in_out_time(in_time, out_time, attendance_date):
	if in_time and not out_time and in_time.date() == attendance_date:
		in_time = in_time.time()
	elif out_time and not in_time and out_time.date() == attendance_date:
		out_time = out_time.time()
	else:
		in_time, out_time = convert_datetime_to_time_for_same_date(in_time, out_time)
	return in_time, out_time


def convert_datetime_to_time_for_same_date(start, end):
	if start and end and start.date() == end.date():
		start = start.time()
		end = end.time()
	else:
		start = format_datetime(start)
		end = format_datetime(end)
	return start, end


def update_late_entry(entry, consider_grace_period):
	if consider_grace_period:
		if entry.late_entry:
			entry_grace_period = entry.late_entry_grace_period if entry.enable_late_entry_marking else 0
			start_time = entry.shift_start + timedelta(minutes=entry_grace_period)
			entry.late_entry_hrs = entry.in_time - start_time
	elif entry.in_time and entry.in_time > entry.shift_start:
		entry.late_entry = 1
		entry.late_entry_hrs = entry.in_time - entry.shift_start
	if entry.late_entry_hrs:
		entry.late_entry_hrs = format_duration(entry.late_entry_hrs.total_seconds())


def update_early_exit(entry, consider_grace_period):
	if consider_grace_period:
		if entry.early_exit:
			exit_grace_period = entry.early_exit_grace_period if entry.enable_early_exit_marking else 0
			end_time = entry.shift_end - timedelta(minutes=exit_grace_period)
			entry.early_exit_hrs = end_time - entry.out_time
	elif entry.out_time and entry.out_time < entry.shift_end:
		entry.early_exit = 1
		entry.early_exit_hrs = entry.shift_end - entry.out_time
	if entry.early_exit_hrs:
		entry.early_exit_hrs = format_duration(entry.early_exit_hrs.total_seconds())



def update_overtime(entry):
	if entry.out_time and entry.out_time > entry.shift_end:
		entry.overtime = 1
		entry.overtime_hrs = entry.out_time - entry.shift_end 
	if entry.overtime_hrs:
		entry.overtime_hrs = format_duration(entry.overtime_hrs.total_seconds())


def get_emps(data):
	emps=[]
	for entry in data:
		if not entry.employee in emps:
			emps.append(entry.employee)
	return emps

def get_holidaies(emps,filters):
	holiday_records_data=[]
	for emp in emps:
		holiday_name,employee_name = frappe.db.get_value('Employee',emp, ['holiday_list','employee_name'])
		holiday_records_filters={"holiday_date":['between', [filters.from_date,filters.to_date]]}
		holiday_records_filters["parent"]=holiday_name
		holiday_records= frappe.get_all("Holiday",fields="*",filters=holiday_records_filters)
		for holiday in holiday_records:
			dict_item = {'name': '', 'employee':emp, 'employee_name': employee_name, '.shift':filters.shift, 'attendance_date':holiday.holiday_date, 'status':'Rest Day', 'in_time':'', 'out_time':'', 'working_hours':'', 'late_entry':'', 'early_exit':'', 'department':'', 'company': '', 'shift_start':'', 'shift_end':'', 'shift_actual_start':'', 'shift_actual_end':'', 'enable_late_entry_marking':'', 'late_entry_grace_period': '', 'enable_early_exit_marking':'', 'early_exit_grace_period':'', 'late_entry_hrs': '', 'overtime':'', 'overtime_hrs': ''}
			dict_item =frappe._dict(dict_item)
			holiday_records_data.append(dict_item)
	return holiday_records_data




	


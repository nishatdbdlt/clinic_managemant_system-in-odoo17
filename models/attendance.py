# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ClinicAttendance(models.Model):
    _name = 'clinic.attendance'
    _description = 'Clinic Attendance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'
    _order = 'attendance_date desc, check_in desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    employee_type = fields.Selection([
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('technician', 'Lab Technician'),
        ('pharmacist', 'Pharmacist'),
        ('admin', 'Admin Staff'),
        ('support', 'Support Staff'),
        ('other', 'Other'),
    ], string='Employee Type')

    department_id = fields.Many2one('hr.department', string='Department',
                                    related='employee_id.department_id', store=True)

    # Attendance Details
    attendance_date = fields.Date(string='Date', required=True, default=fields.Date.today, tracking=True)

    check_in = fields.Datetime(string='Check In', required=True, tracking=True)
    check_out = fields.Datetime(string='Check Out', tracking=True)

    # Working Hours
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True)
    expected_hours = fields.Float(string='Expected Hours', default=8.0)
    overtime_hours = fields.Float(string='Overtime Hours', compute='_compute_overtime', store=True)

    # Status
    status = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('late', 'Late'),
    ], string='Status', default='present', compute='_compute_status', store=True, tracking=True)

    is_late = fields.Boolean(string='Late Arrival', compute='_compute_late', store=True)
    late_minutes = fields.Float(string='Late Minutes', compute='_compute_late', store=True)

    # Shift
    shift = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift'),
    ], string='Shift', default='morning')

    # Location
    check_in_location = fields.Char(string='Check-in Location')
    check_out_location = fields.Char(string='Check-out Location')

    notes = fields.Text(string='Notes')

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.worked_hours = delta.total_seconds() / 3600.0
            else:
                record.overtime_hours = 0.0

    @api.depends('check_in', 'shift')
    def _compute_late(self):
        for record in self:
            if record.check_in and record.shift:
                # Define shift start times
                shift_times = {
                    'morning': 9.0,  # 9:00 AM
                    'evening': 17.0,  # 5:00 PM
                    'night': 22.0,  # 10:00 PM
                }

                expected_time = shift_times.get(record.shift, 9.0)
                check_in_time = record.check_in.hour + record.check_in.minute / 60.0

                if check_in_time > expected_time:
                    record.is_late = True
                    record.late_minutes = (check_in_time - expected_time) * 60
                else:
                    record.is_late = False
                    record.late_minutes = 0.0
            else:
                record.is_late = False
                record.late_minutes = 0.0

    @api.depends('worked_hours', 'expected_hours', 'is_late', 'check_out')
    def _compute_status(self):
        for record in self:
            if not record.check_out:
                record.status = 'present'
            elif record.worked_hours >= record.expected_hours:
                record.status = 'present'
            elif record.worked_hours >= (record.expected_hours / 2):
                record.status = 'half_day'
            elif record.is_late and record.late_minutes > 30:
                record.status = 'late'
            else:
                record.status = 'present'

    @api.constrains('check_in', 'check_out')
    def _check_check_out(self):
        for record in self:
            if record.check_out and record.check_in:
                if record.check_out <= record.check_in:
                    raise ValidationError(_('Check-out time must be after check-in time.'))

    @api.constrains('attendance_date', 'employee_id')
    def _check_duplicate_attendance(self):
        for record in self:
            duplicate = self.search([
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                ('attendance_date', '=', record.attendance_date),
            ])
            if duplicate:
                raise ValidationError(_('Attendance record already exists for this employee on this date.'))

    def action_check_out(self):
        for record in self:
            if not record.check_out:
                record.check_out = fields.Datetime.now()


class ClinicAttendanceSummary(models.Model):
    _name = 'clinic.attendance.summary'
    _description = 'Attendance Summary'
    _rec_name = 'employee_id'
    _order = 'month desc, year desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    month = fields.Selection([
        ('january', 'January'),
        ('february', 'February'),
        ('march', 'March'),
        ('april', 'April'),
        ('may', 'May'),
        ('june', 'June'),
        ('july', 'July'),
        ('august', 'August'),
        ('september', 'September'),
        ('october', 'October'),
        ('november', 'November'),
        ('december', 'December'),
    ], string='Month', required=True)
    year = fields.Integer(string='Year', required=True, default=lambda self: fields.Date.today().year)

    # Summary
    total_working_days = fields.Integer(string='Total Working Days', default=26)
    present_days = fields.Integer(string='Present Days', compute='_compute_summary', store=True)
    absent_days = fields.Integer(string='Absent Days', compute='_compute_summary', store=True)
    half_days = fields.Integer(string='Half Days', compute='_compute_summary', store=True)
    late_days = fields.Integer(string='Late Days', compute='_compute_summary', store=True)

    total_worked_hours = fields.Float(string='Total Worked Hours', compute='_compute_summary', store=True)
    total_overtime_hours = fields.Float(string='Total Overtime', compute='_compute_summary', store=True)

    attendance_percentage = fields.Float(string='Attendance %', compute='_compute_summary', store=True)

    @api.depends('employee_id', 'month', 'year', 'total_working_days')
    def _compute_summary(self):
        for record in self:
            if record.employee_id and record.month and record.year:
                # Get month number
                month_map = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month_num = month_map.get(record.month, 1)

                # Get attendance records for the month
                attendances = self.env['clinic.attendance'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('attendance_date', '>=', f'{record.year}-{month_num:02d}-01'),
                    ('attendance_date', '<=', f'{record.year}-{month_num:02d}-31'),
                ])

                record.present_days = len(attendances.filtered(lambda a: a.status == 'present'))
                record.half_days = len(attendances.filtered(lambda a: a.status == 'half_day'))
                record.late_days = len(attendances.filtered(lambda a: a.status == 'late'))
                record.absent_days = record.total_working_days - len(attendances)

                record.total_worked_hours = sum(attendances.mapped('worked_hours'))
                record.total_overtime_hours = sum(attendances.mapped('overtime_hours'))

                if record.total_working_days > 0:
                    record.attendance_percentage = (len(attendances) / record.total_working_days) * 100
                else:
                    record.attendance_percentage = 0.0

                  # worked_hours = 0.0


@api.depends('worked_hours', 'expected_hours')
def _compute_overtime(self):
    for record in self:
        if record.worked_hours > record.expected_hours:
            record.overtime_hours = record.worked_hours - record.expected_hours
        else:
            record
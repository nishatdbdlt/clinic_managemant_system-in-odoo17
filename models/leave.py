# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class ClinicLeave(models.Model):
    _name = 'clinic.leave'
    _description = 'Leave Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'leave_number'
    _order = 'request_date desc'

    leave_number = fields.Char(string='Leave Number', required=True,
                               copy=False, readonly=True, default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department',
                                    related='employee_id.department_id', store=True)

    # Leave Type
    leave_type = fields.Selection([
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('annual', 'Annual Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('emergency', 'Emergency Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('compensatory', 'Compensatory Leave'),
    ], string='Leave Type', required=True, tracking=True)

    # Dates
    request_date = fields.Date(string='Request Date', default=fields.Date.today,
                               required=True, readonly=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)

    number_of_days = fields.Integer(string='Number of Days',
                                    compute='_compute_number_of_days', store=True)

    # Half Day
    is_half_day = fields.Boolean(string='Half Day')
    half_day_period = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
    ], string='Half Day Period')

    # Reason
    reason = fields.Text(string='Reason', required=True)
    attachment = fields.Binary(string='Attachment (Medical Certificate, etc.)')
    attachment_filename = fields.Char(string='Filename')

    # Approval
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True)
    approval_date = fields.Date(string='Approval Date', tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Leave Balance
    leave_balance = fields.Float(string='Current Leave Balance',
                                 compute='_compute_leave_balance')

    # Handover
    handover_to = fields.Many2one('hr.employee', string='Handover To')
    handover_notes = fields.Text(string='Handover Notes')

    notes = fields.Text(string='Additional Notes')

    @api.model
    def create(self, vals):
        if vals.get('leave_number', _('New')) == _('New'):
            vals['leave_number'] = self.env['ir.sequence'].next_by_code('clinic.leave') or _('New')
        return super(ClinicLeave, self).create(vals)

    @api.depends('start_date', 'end_date', 'is_half_day')
    def _compute_number_of_days(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                days = delta.days + 1

                if record.is_half_day:
                    record.number_of_days = 0.5
                else:
                    record.number_of_days = days
            else:
                record.number_of_days = 0

    def _compute_leave_balance(self):
        for record in self:
            # Calculate leave balance based on leave type and employee
            # This is a simplified version - you can enhance it based on your requirements
            if record.employee_id and record.leave_type:
                approved_leaves = self.search([
                    ('employee_id', '=', record.employee_id.id),
                    ('leave_type', '=', record.leave_type),
                    ('state', '=', 'approved'),
                    ('start_date', '>=', f'{fields.Date.today().year}-01-01'),
                ])

                total_taken = sum(approved_leaves.mapped('number_of_days'))

                # Default yearly allocation (you can make this configurable)
                leave_allocations = {
                    'sick': 10,
                    'casual': 10,
                    'annual': 20,
                    'maternity': 90,
                    'paternity': 10,
                    'emergency': 5,
                    'unpaid': 0,
                    'compensatory': 0,
                }

                allocated = leave_allocations.get(record.leave_type, 0)
                record.leave_balance = allocated - total_taken
            else:
                record.leave_balance = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date < record.start_date:
                raise ValidationError(_('End date must be after start date.'))

            # Check for overlapping leaves
            overlapping = self.search([
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                ('state', 'in', ['submitted', 'approved']),
                '|',
                '&', ('start_date', '<=', record.start_date), ('end_date', '>=', record.start_date),
                '&', ('start_date', '<=', record.end_date), ('end_date', '>=', record.end_date),
            ])

            if overlapping:
                raise ValidationError(_('You already have a leave request for this period.'))

    @api.constrains('number_of_days', 'leave_balance')
    def _check_leave_balance(self):
        for record in self:
            if record.leave_type not in ['unpaid', 'compensatory']:
                if record.number_of_days > record.leave_balance:
                    raise ValidationError(
                        _('Insufficient leave balance. Available: %s days, Requested: %s days')
                        % (record.leave_balance, record.number_of_days)
                    )

    def action_submit(self):
        for record in self:
            record.state = 'submitted'

    def action_approve(self):
        for record in self:
            record.state = 'approved'
            record.approved_by = self.env.user
            record.approval_date = fields.Date.today()

    def action_reject(self):
        for record in self:
            record.state = 'rejected'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'


class ClinicLeaveAllocation(models.Model):
    _name = 'clinic.leave.allocation'
    _description = 'Leave Allocation'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    year = fields.Integer(string='Year', required=True, default=lambda self: fields.Date.today().year)

    # Leave Allocations
    sick_leave = fields.Float(string='Sick Leave', default=10)
    casual_leave = fields.Float(string='Casual Leave', default=10)
    annual_leave = fields.Float(string='Annual Leave', default=20)
    maternity_leave = fields.Float(string='Maternity Leave', default=90)
    paternity_leave = fields.Float(string='Paternity Leave', default=10)
    emergency_leave = fields.Float(string='Emergency Leave', default=5)
    compensatory_leave = fields.Float(string='Compensatory Leave', default=0)

    # Used Leave
    sick_leave_used = fields.Float(string='Sick Leave Used', compute='_compute_used_leaves', store=True)
    casual_leave_used = fields.Float(string='Casual Leave Used', compute='_compute_used_leaves', store=True)
    annual_leave_used = fields.Float(string='Annual Leave Used', compute='_compute_used_leaves', store=True)

    # Balance
    sick_leave_balance = fields.Float(string='Sick Leave Balance', compute='_compute_balance', store=True)
    casual_leave_balance = fields.Float(string='Casual Leave Balance', compute='_compute_balance', store=True)
    annual_leave_balance = fields.Float(string='Annual Leave Balance', compute='_compute_balance', store=True)

    @api.depends('employee_id', 'year')
    def _compute_used_leaves(self):
        for record in self:
            if record.employee_id and record.year:
                leaves = self.env['clinic.leave'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'approved'),
                    ('start_date', '>=', f'{record.year}-01-01'),
                    ('start_date', '<=', f'{record.year}-12-31'),
                ])

                record.sick_leave_used = sum(leaves.filtered(lambda l: l.leave_type == 'sick').mapped('number_of_days'))
                record.casual_leave_used = sum(
                    leaves.filtered(lambda l: l.leave_type == 'casual').mapped('number_of_days'))
                record.annual_leave_used = sum(
                    leaves.filtered(lambda l: l.leave_type == 'annual').mapped('number_of_days'))

    @api.depends('sick_leave', 'sick_leave_used', 'casual_leave', 'casual_leave_used',
                 'annual_leave', 'annual_leave_used')
    def _compute_balance(self):
        for record in self:
            record.sick_leave_balance = record.sick_leave - record.sick_leave_used
            record.casual_leave_balance = record.casual_leave - record.casual_leave_used
            record.annual_leave_balance = record.annual_leave - record.annual_leave_used
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicPayroll(models.Model):
    _name = 'clinic.payroll'
    _description = 'Clinic Payroll'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'payroll_number'
    _order = 'payment_date desc'

    payroll_number = fields.Char(string='Payroll Number', required=True,
                                 copy=False, readonly=True, default=lambda self: _('New'))

    # Employee Information
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
    ], string='Employee Type', required=True)

    department_id = fields.Many2one('hr.department', string='Department')
    job_position = fields.Char(string='Job Position')

    # Period
    payment_month = fields.Selection([
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
    ], string='Payment Month', required=True)

    payment_year = fields.Integer(string='Payment Year', required=True,
                                  default=lambda self: fields.Date.today().year)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.today, tracking=True)

    # Salary Components
    basic_salary = fields.Float(string='Basic Salary', required=True, tracking=True)
    house_allowance = fields.Float(string='House Allowance')
    medical_allowance = fields.Float(string='Medical Allowance')
    transport_allowance = fields.Float(string='Transport Allowance')
    performance_bonus = fields.Float(string='Performance Bonus')
    other_allowances = fields.Float(string='Other Allowances')

    # Earnings
    total_earnings = fields.Float(string='Total Earnings', compute='_compute_totals', store=True)

    # Deductions
    tax_deduction = fields.Float(string='Tax Deduction')
    provident_fund = fields.Float(string='Provident Fund')
    insurance = fields.Float(string='Insurance')
    loan_deduction = fields.Float(string='Loan Deduction')
    advance_deduction = fields.Float(string='Advance Deduction')
    other_deductions = fields.Float(string='Other Deductions')

    total_deductions = fields.Float(string='Total Deductions', compute='_compute_totals', store=True)

    # Net Salary
    net_salary = fields.Float(string='Net Salary', compute='_compute_totals', store=True, tracking=True)

    # Attendance Bonus/Penalty
    working_days = fields.Integer(string='Working Days', default=26)
    present_days = fields.Integer(string='Present Days')
    absent_days = fields.Integer(string='Absent Days', compute='_compute_absent_days', store=True)
    overtime_hours = fields.Float(string='Overtime Hours')
    overtime_rate = fields.Float(string='Overtime Rate per Hour')
    overtime_amount = fields.Float(string='Overtime Amount', compute='_compute_overtime', store=True)

    # Payment Information
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ], string='Payment Method', default='bank_transfer')

    bank_account = fields.Char(string='Bank Account Number')
    bank_name = fields.Char(string='Bank Name')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')

    @api.model
    def create(self, vals):
        if vals.get('payroll_number', _('New')) == _('New'):
            vals['payroll_number'] = self.env['ir.sequence'].next_by_code('clinic.payroll') or _('New')
        return super(ClinicPayroll, self).create(vals)

    @api.depends('basic_salary', 'house_allowance', 'medical_allowance',
                 'transport_allowance', 'performance_bonus', 'other_allowances',
                 'overtime_amount', 'tax_deduction', 'provident_fund',
                 'insurance', 'loan_deduction', 'advance_deduction', 'other_deductions')
    def _compute_totals(self):
        for record in self:
            record.total_earnings = (
                    record.basic_salary +
                    record.house_allowance +
                    record.medical_allowance +
                    record.transport_allowance +
                    record.performance_bonus +
                    record.other_allowances +
                    record.overtime_amount
            )

            record.total_deductions = (
                    record.tax_deduction +
                    record.provident_fund +
                    record.insurance +
                    record.loan_deduction +
                    record.advance_deduction +
                    record.other_deductions
            )

            record.net_salary = record.total_earnings - record.total_deductions

    @api.depends('working_days', 'present_days')
    def _compute_absent_days(self):
        for record in self:
            record.absent_days = record.working_days - record.present_days

    @api.depends('overtime_hours', 'overtime_rate')
    def _compute_overtime(self):
        for record in self:
            record.overtime_amount = record.overtime_hours * record.overtime_rate

    @api.constrains('present_days', 'working_days')
    def _check_present_days(self):
        for record in self:
            if record.present_days > record.working_days:
                raise ValidationError(_('Present days cannot exceed working days.'))
            if record.present_days < 0:
                raise ValidationError(_('Present days cannot be negative.'))

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_pay(self):
        for record in self:
            record.state = 'paid'
            record.payment_date = fields.Date.today()

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_print_payslip(self):
        return self.env.ref('clinic_management_system.action_report_payslip').report_action(self)

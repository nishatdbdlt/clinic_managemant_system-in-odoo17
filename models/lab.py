# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicLabTest(models.Model):
    _name = 'clinic.lab.test'
    _description = 'Lab Test'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'test_number'
    _order = 'test_date desc'

    test_number = fields.Char(string='Test Number', required=True,
                              copy=False, readonly=True, default=lambda self: _('New'))

    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('clinic.doctor', string='Prescribed By', tracking=True)
    appointment_id = fields.Many2one('clinic.appointment', string='Appointment')

    # Test Information
    test_type = fields.Selection([
        ('blood', 'Blood Test'),
        ('urine', 'Urine Test'),
        ('xray', 'X-Ray'),
        ('ct_scan', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('echo', 'Echocardiogram'),
        ('other', 'Other'),
    ], string='Test Type', required=True, tracking=True)

    test_name = fields.Char(string='Test Name', required=True)
    test_description = fields.Text(string='Description')

    # Dates
    test_date = fields.Date(string='Test Date', default=fields.Date.today, required=True)
    result_date = fields.Date(string='Result Date')

    # Results
    result = fields.Text(string='Test Result')
    result_file = fields.Binary(string='Result File')
    result_filename = fields.Char(string='Filename')

    # Clinical Values (for blood tests etc.)
    normal_range = fields.Char(string='Normal Range')
    test_value = fields.Char(string='Test Value')
    unit = fields.Char(string='Unit')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Technician
    technician_id = fields.Many2one('res.users', string='Lab Technician')

    # Pricing
    test_cost = fields.Float(string='Test Cost', required=True)

    notes = fields.Text(string='Notes')
    priority = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ], string='Priority', default='normal', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('test_number', _('New')) == _('New'):
            vals['test_number'] = self.env['ir.sequence'].next_by_code('clinic.lab.test') or _('New')
        return super(ClinicLabTest, self).create(vals)

    def action_collect_sample(self):
        for record in self:
            record.state = 'sample_collected'

    def action_start_test(self):
        for record in self:
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            record.state = 'completed'
            record.result_date = fields.Date.today()

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
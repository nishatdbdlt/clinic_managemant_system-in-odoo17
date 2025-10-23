# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicPatient(models.Model):
    _name = 'clinic.patient'
    _description = 'Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Patient Name', required=True, tracking=True)
    patient_id = fields.Char(string='Patient ID', required=True, copy=False,
                             readonly=True, default=lambda self: _('New'))
    image = fields.Binary(string='Photo')

    # Personal Information
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string='Blood Group')

    # Contact Information
    phone = fields.Char(string='Phone', required=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')

    # Medical Information
    allergies = fields.Text(string='Allergies')
    chronic_diseases = fields.Text(string='Chronic Diseases')
    current_medications = fields.Text(string='Current Medications')
    medical_history = fields.Text(string='Medical History')
    height = fields.Float(string='Height (cm)')
    weight = fields.Float(string='Weight (kg)')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)

    # Insurance
    insurance_company = fields.Char(string='Insurance Company')
    insurance_number = fields.Char(string='Insurance Number')
    insurance_expiry = fields.Date(string='Insurance Expiry Date')

    # Relations
    appointment_ids = fields.One2many('clinic.appointment', 'patient_id', string='Appointments')
    prescription_ids = fields.One2many('clinic.prescription', 'patient_id', string='Prescriptions')
    # lab_test_ids = fields.One2many('clinic.lab.test', 'patient_id', string='Lab Tests')
    cabin_id = fields.Many2one('clinic.cabin', string='Current Cabin')
    ward_id = fields.Many2one('clinic.ward', string='Current Ward')

    # Status
    active = fields.Boolean(string='Active', default=True)
    is_admitted = fields.Boolean(string='Currently Admitted', default=False)
    admission_date = fields.Date(string='Admission Date')

    # Statistics
    total_visits = fields.Integer(string='Total Visits', compute='_compute_statistics')
    last_visit_date = fields.Date(string='Last Visit', compute='_compute_statistics')
    total_amount_paid = fields.Float(string='Total Amount Paid', compute='_compute_statistics')

    @api.model
    def create(self, vals):
        if vals.get('patient_id', _('New')) == _('New'):
            vals['patient_id'] = self.env['ir.sequence'].next_by_code('clinic.patient') or _('New')
        return super(ClinicPatient, self).create(vals)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = fields.Date.today()
                record.age = today.year - record.date_of_birth.year - (
                        (today.month, today.day) < (record.date_of_birth.month, record.date_of_birth.day)
                )
            else:
                record.age = 0

    @api.depends('height', 'weight')
    def _compute_bmi(self):
        for record in self:
            if record.height and record.weight and record.height > 0:
                height_m = record.height / 100
                record.bmi = record.weight / (height_m * height_m)
            else:
                record.bmi = 0.0

    def _compute_statistics(self):
        for record in self:
            appointments = record.appointment_ids.filtered(lambda a: a.state == 'done')
            record.total_visits = len(appointments)
            record.last_visit_date = max(appointments.mapped('appointment_date')) if appointments else False
            record.total_amount_paid = sum(appointments.mapped('total_amount'))

    @api.constrains('height', 'weight')
    def _check_measurements(self):
        for record in self:
            if record.height and record.height < 0:
                raise ValidationError(_('Height cannot be negative.'))
            if record.weight and record.weight < 0:
                raise ValidationError(_('Weight cannot be negative.'))

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'name': _('Appointments'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'view_mode': 'tree,form,calendar',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
        }
    #
    def action_view_medical_history(self):
        self.ensure_one()
        return {
            'name': _('Medical History'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.prescription',
            'view_mode': 'tree,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
        }
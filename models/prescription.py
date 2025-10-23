# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicPrescription(models.Model):
    _name = 'clinic.prescription'
    _description = 'Prescription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'prescription_number'
    _order = 'prescription_date desc'

    prescription_number = fields.Char(string='Prescription Number', required=True,
                                      copy=False, readonly=True, default=lambda self: _('New'))

    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('clinic.doctor', string='Doctor', required=True, tracking=True)
    appointment_id = fields.Many2one('clinic.appointment', string='Appointment')

    prescription_date = fields.Date(string='Prescription Date', required=True,
                                    default=fields.Date.today, tracking=True)

    # Clinical Information
    diagnosis = fields.Text(string='Diagnosis', required=True)
    symptoms = fields.Text(string='Symptoms')
    medical_advice = fields.Text(string='Medical Advice')

    # Vital Signs
    blood_pressure = fields.Char(string='Blood Pressure')
    temperature = fields.Float(string='Temperature (°F)')
    pulse_rate = fields.Integer(string='Pulse Rate (bpm)')
    respiratory_rate = fields.Integer(string='Respiratory Rate')
    oxygen_saturation = fields.Float(string='Oxygen Saturation (%)')

    # Prescription Lines
    prescription_line_ids = fields.One2many('clinic.prescription.line', 'prescription_id',
                                            string='Medicines')

    # Follow-up
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_date = fields.Date(string='Follow-up Date')
    follow_up_notes = fields.Text(string='Follow-up Notes')

    # Lab Tests
    lab_test_required = fields.Boolean(string='Lab Tests Required')
    lab_test_notes = fields.Text(string='Lab Test Instructions')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('dispensed', 'Dispensed'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Additional Notes')

    @api.model
    def create(self, vals):
        if vals.get('prescription_number', _('New')) == _('New'):
            vals['prescription_number'] = self.env['ir.sequence'].next_by_code('clinic.prescription') or _('New')
        return super(ClinicPrescription, self).create(vals)

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_dispense(self):
        for record in self:
            record.state = 'dispensed'

    def action_print_prescription(self):
        return self.env.ref('clinic_management.action_report_prescription').report_action(self)


class ClinicPrescriptionLine(models.Model):
    _name = 'clinic.prescription.line'
    _description = 'Prescription Line'
    _rec_name = 'medicine_name'

    prescription_id = fields.Many2one('clinic.prescription', string='Prescription',
                                      required=True, ondelete='cascade')

    medicine_name = fields.Char(string='Medicine Name', required=True)
    dosage = fields.Char(string='Dosage', required=True)
    frequency = fields.Selection([
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('thrice_daily', 'Thrice Daily'),
        ('four_times', 'Four Times Daily'),
        ('as_needed', 'As Needed'),
        ('before_meal', 'Before Meal'),
        ('after_meal', 'After Meal'),
    ], string='Frequency', required=True)

    duration = fields.Integer(string='Duration (days)', required=True)
    quantity = fields.Integer(string='Quantity', required=True)

    # Administration Instructions
    route = fields.Selection([
        ('oral', 'Oral'),
        ('injection', 'Injection'),
        ('topical', 'Topical'),
        ('inhalation', 'Inhalation'),
        ('drops', 'Drops'),
    ], string='Route', default='oral')

    instructions = fields.Text(string='Special Instructions')
    notes = fields.Text(string='Notes')
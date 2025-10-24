# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class ClinicAppointment(models.Model):
    _name = 'clinic.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'appointment_number'
    _order = 'appointment_date desc, appointment_time desc'

    appointment_number = fields.Char(string='Appointment Number', required=True,
                                     copy=False, readonly=True, default=lambda self: _('New'))

    # Patient and Doctor
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, tracking=True)
    patient_age = fields.Integer(related='patient_id.age', string='Patient Age', store=True)
    patient_phone = fields.Char(related='patient_id.phone', string='Patient Phone')

    doctor_id = fields.Many2one('clinic.doctor', string='Doctor', required=True, tracking=True)
    doctor_specialization = fields.Selection(related='doctor_id.specialization',
                                             string='Specialization', store=True)

    # Appointment Details
    appointment_date = fields.Date(string='Appointment Date', required=True,
                                   default=fields.Date.today, tracking=True)
    appointment_time = fields.Float(string='Appointment Time', required=True)
    appointment_end_time = fields.Float(string='End Time', compute='_compute_end_time', store=True)
    duration = fields.Integer(string='Duration (minutes)', default=30)

    # Appointment Type
    appointment_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('checkup', 'Regular Checkup'),
    ], string='Appointment Type', required=True, default='consultation')

    # Clinical Information
    symptoms = fields.Text(string='Symptoms')
    diagnosis = fields.Text(string='Diagnosis')
    treatment = fields.Text(string='Treatment')
    notes = fields.Text(string='Notes')

    # Financial
    consultation_fee = fields.Float(related='doctor_id.consultation_fee',
                                    string='Consultation Fee', store=True)
    additional_charges = fields.Float(string='Additional Charges')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    paid_amount = fields.Float(string='Paid Amount', tracking=True)
    balance = fields.Float(string='Balance', compute='_compute_balance', store=True)

    # Payment
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ], string='Payment Status', compute='_compute_payment_status', store=True, tracking=True)

    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Relations
    prescription_id = fields.Many2one('clinic.prescription', string='Prescription')
    lab_test_ids = fields.One2many('clinic.lab.test', 'appointment_id', string='Lab Tests')

    # Reminder
    reminder_sent = fields.Boolean(string='Reminder Sent', default=False)

    @api.model
    def create(self, vals):
        if vals.get('appointment_number', _('New')) == _('New'):
            vals['appointment_number'] = self.env['ir.sequence'].next_by_code('clinic.appointment') or _('New')
        return super(ClinicAppointment, self).create(vals)

    @api.depends('appointment_time', 'duration')
    def _compute_end_time(self):
        for record in self:
            if record.appointment_time and record.duration:
                record.appointment_end_time = record.appointment_time + (record.duration / 60.0)
            else:
                record.appointment_end_time = record.appointment_time

    @api.depends('consultation_fee', 'additional_charges')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.consultation_fee + record.additional_charges

    @api.depends('total_amount', 'paid_amount')
    def _compute_balance(self):
        for record in self:
            record.balance = record.total_amount - record.paid_amount

    @api.depends('paid_amount', 'total_amount')
    def _compute_payment_status(self):
        for record in self:
            if record.paid_amount == 0:
                record.payment_status = 'unpaid'
            elif record.paid_amount < record.total_amount:
                record.payment_status = 'partial'
            else:
                record.payment_status = 'paid'

    @api.constrains('appointment_date', 'appointment_time', 'doctor_id')
    def _check_doctor_availability(self):
        for record in self:
            if record.appointment_date and record.doctor_id:
                # Check if doctor is available on that day
                weekday = record.appointment_date.weekday()
                available_days = {
                    0: record.doctor_id.monday_available,
                    1: record.doctor_id.tuesday_available,
                    2: record.doctor_id.wednesday_available,
                    3: record.doctor_id.thursday_available,
                    4: record.doctor_id.friday_available,
                    5: record.doctor_id.saturday_available,
                    6: record.doctor_id.sunday_available,
                }

                if not available_days.get(weekday, False):
                    raise ValidationError(_('Doctor is not available on this day.'))

                # Check working hours
                if record.appointment_time < record.doctor_id.working_hours_start or \
                        record.appointment_time > record.doctor_id.working_hours_end:
                    raise ValidationError(_('Appointment time is outside doctor working hours.'))

                # Check for overlapping appointments
                overlapping = self.search([
                    ('id', '!=', record.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('appointment_date', '=', record.appointment_date),
                    ('state', 'not in', ['cancelled']),
                    '|',
                    '&', ('appointment_time', '<=', record.appointment_time),
                    ('appointment_end_time', '>', record.appointment_time),
                    '&', ('appointment_time', '<', record.appointment_end_time),
                    ('appointment_end_time', '>=', record.appointment_end_time),
                ])

                if overlapping:
                    raise ValidationError(_('This time slot is already booked for this doctor.'))

    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'

    def action_start(self):
        for record in self:
            record.state = 'in_progress'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_create_prescription(self):
        self.ensure_one()
        return {
            'name': _('Create Prescription'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.prescription',
            'view_mode': 'form',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
                'default_appointment_id': self.id,
            },
            'target': 'current',
        }

    def action_create_invoice(self):
        self.ensure_one()
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Consultation - {self.doctor_id.name}',
                'quantity': 1,
                'price_unit': self.total_amount,
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
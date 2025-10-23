# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicDoctor(models.Model):
    _name = 'clinic.doctor'
    _description = 'Doctor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    image = fields.Binary(string='Photo')
    user_id = fields.Many2one('res.users', string='Related User', ondelete='cascade')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', required=True)
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    phone = fields.Char(string='Phone', required=True)
    email = fields.Char(string='Email')
    address = fields.Text(string='Address')

    # Professional Information
    specialization = fields.Selection([
        ('general', 'General Physician'),
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('orthopedics', 'Orthopedics'),
        ('pediatrics', 'Pediatrics'),
        ('gynecology', 'Gynecology'),
        ('dermatology', 'Dermatology'),
        ('psychiatry', 'Psychiatry'),
        ('radiology', 'Radiology'),
        ('surgery', 'Surgery'),
    ], string='Specialization', required=True, tracking=True)

    license_number = fields.Char(string='License Number', required=True)
    qualification = fields.Char(string='Qualification')
    experience_years = fields.Integer(string='Years of Experience')
    joining_date = fields.Date(string='Joining Date', default=fields.Date.today)

    # Consultation
    consultation_fee = fields.Float(string='Consultation Fee', required=True, tracking=True)
    consultation_duration = fields.Integer(string='Consultation Duration (minutes)', default=30)

    # Availability
    monday_available = fields.Boolean(string='Monday', default=True)
    tuesday_available = fields.Boolean(string='Tuesday', default=True)
    wednesday_available = fields.Boolean(string='Wednesday', default=True)
    thursday_available = fields.Boolean(string='Thursday', default=True)
    friday_available = fields.Boolean(string='Friday', default=True)
    saturday_available = fields.Boolean(string='Saturday', default=False)
    sunday_available = fields.Boolean(string='Sunday', default=False)

    working_hours_start = fields.Float(string='Working Hours Start', default=9.0)
    working_hours_end = fields.Float(string='Working Hours End', default=17.0)

    # Relations
    appointment_ids = fields.One2many('clinic.appointment', 'doctor_id', string='Appointments')
    prescription_ids = fields.One2many('clinic.prescription', 'doctor_id', string='Prescriptions')

    # Status
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('on_leave', 'On Leave'),
    ], string='Status', default='available', tracking=True)

    # Statistics
    total_appointments = fields.Integer(string='Total Appointments', compute='_compute_statistics')
    total_patients = fields.Integer(string='Total Patients', compute='_compute_statistics')

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

    def _compute_statistics(self):
        for record in self:
            record.total_appointments = len(record.appointment_ids)
            record.total_patients = len(record.appointment_ids.mapped('patient_id'))

    @api.constrains('consultation_fee')
    def _check_consultation_fee(self):
        for record in self:
            if record.consultation_fee < 0:
                raise ValidationError(_('Consultation fee cannot be negative.'))

    @api.constrains('working_hours_start', 'working_hours_end')
    def _check_working_hours(self):
        for record in self:
            if record.working_hours_start >= record.working_hours_end:
                raise ValidationError(_('Working hours end must be after working hours start.'))

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'name': _('Appointments'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.appointment',
            'view_mode': 'tree,form,calendar',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id}
        }
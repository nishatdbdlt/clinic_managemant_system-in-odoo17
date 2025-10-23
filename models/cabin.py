# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClinicCabin(models.Model):
    _name = 'clinic.cabin'
    _description = 'Cabin/Room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'cabin_number'

    cabin_number = fields.Char(string='Cabin Number', required=True, tracking=True)
    name = fields.Char(string='Cabin Name')

    # Cabin Type
    cabin_type = fields.Selection([
        ('general', 'General'),
        ('private', 'Private'),
        ('deluxe', 'Deluxe'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency'),
    ], string='Cabin Type', required=True, default='general', tracking=True)

    # Location
    floor = fields.Integer(string='Floor')
    building = fields.Char(string='Building')

    # Capacity
    bed_capacity = fields.Integer(string='Bed Capacity', required=True, default=1)
    occupied_beds = fields.Integer(string='Occupied Beds', compute='_compute_occupancy')
    available_beds = fields.Integer(string='Available Beds', compute='_compute_occupancy')

    # Pricing
    daily_rate = fields.Float(string='Daily Rate', required=True)

    # Facilities
    has_ac = fields.Boolean(string='Air Conditioning')
    has_tv = fields.Boolean(string='Television')
    has_wifi = fields.Boolean(string='WiFi')
    has_bathroom = fields.Boolean(string='Attached Bathroom')
    has_oxygen = fields.Boolean(string='Oxygen Supply')
    has_monitor = fields.Boolean(string='Health Monitor')

    # Status
    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    ], string='Status', default='available', compute='_compute_status', store=True, tracking=True)

    active = fields.Boolean(string='Active', default=True)

    # Relations
    patient_ids = fields.One2many('clinic.patient', 'cabin_id', string='Current Patients')

    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')

    @api.depends('patient_ids')
    def _compute_occupancy(self):
        for record in self:
            record.occupied_beds = len(record.patient_ids)
            record.available_beds = record.bed_capacity - record.occupied_beds

    @api.depends('occupied_beds', 'bed_capacity', 'active')
    def _compute_status(self):
        for record in self:
            if not record.active:
                record.status = 'maintenance'
            elif record.occupied_beds >= record.bed_capacity:
                record.status = 'occupied'
            else:
                record.status = 'available'

    @api.constrains('bed_capacity')
    def _check_bed_capacity(self):
        for record in self:
            if record.bed_capacity < 1:
                raise ValidationError(_('Bed capacity must be at least 1.'))

    def action_view_patients(self):
        self.ensure_one()
        return {
            'name': _('Patients'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.patient',
            'view_mode': 'tree,form',
            'domain': [('cabin_id', '=', self.id)],
        }


class ClinicWard(models.Model):
    _name = 'clinic.ward'
    _description = 'Ward'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ward_number'

    ward_number = fields.Char(string='Ward Number', required=True, tracking=True)
    name = fields.Char(string='Ward Name', required=True)

    # Ward Type
    ward_type = fields.Selection([
        ('general', 'General Ward'),
        ('male', 'Male Ward'),
        ('female', 'Female Ward'),
        ('pediatric', 'Pediatric Ward'),
        ('maternity', 'Maternity Ward'),
        ('surgical', 'Surgical Ward'),
        ('icu', 'ICU'),
        ('emergency', 'Emergency Ward'),
    ], string='Ward Type', required=True, default='general', tracking=True)

    # Location
    floor = fields.Integer(string='Floor')
    building = fields.Char(string='Building')

    # Capacity
    bed_capacity = fields.Integer(string='Total Beds', required=True, default=10)
    occupied_beds = fields.Integer(string='Occupied Beds', compute='_compute_occupancy')
    available_beds = fields.Integer(string='Available Beds', compute='_compute_occupancy')
    occupancy_rate = fields.Float(string='Occupancy Rate (%)', compute='_compute_occupancy')

    # Pricing
    daily_rate = fields.Float(string='Daily Rate per Bed', required=True)

    # Staff Assignment
    head_nurse_id = fields.Many2one('res.users', string='Head Nurse')
    nurse_count = fields.Integer(string='Number of Nurses')

    # Facilities
    has_ac = fields.Boolean(string='Air Conditioning')
    has_oxygen = fields.Boolean(string='Oxygen Supply')
    has_monitor = fields.Boolean(string='Health Monitors')
    has_emergency_equipment = fields.Boolean(string='Emergency Equipment')

    # Status
    status = fields.Selection([
        ('available', 'Available'),
        ('full', 'Full'),
        ('maintenance', 'Under Maintenance'),
    ], string='Status', default='available', compute='_compute_status', store=True, tracking=True)

    active = fields.Boolean(string='Active', default=True)

    # Relations
    patient_ids = fields.One2many('clinic.patient', 'ward_id', string='Current Patients')

    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')

    @api.depends('patient_ids', 'bed_capacity')
    def _compute_occupancy(self):
        for record in self:
            record.occupied_beds = len(record.patient_ids)
            record.available_beds = record.bed_capacity - record.occupied_beds
            if record.bed_capacity > 0:
                record.occupancy_rate = (record.occupied_beds / record.bed_capacity) * 100
            else:
                record.occupancy_rate = 0.0

    @api.depends('occupied_beds', 'bed_capacity', 'active')
    def _compute_status(self):
        for record in self:
            if not record.active:
                record.status = 'maintenance'
            elif record.occupied_beds >= record.bed_capacity:
                record.status = 'full'
            else:
                record.status = 'available'

    @api.constrains('bed_capacity')
    def _check_bed_capacity(self):
        for record in self:
            if record.bed_capacity < 1:
                raise ValidationError(_('Bed capacity must be at least 1.'))

    def action_view_patients(self):
        self.ensure_one()
        return {
            'name': _('Patients'),
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.patient',
            'view_mode': 'tree,form',
            'domain': [('ward_id', '=', self.id)],
        }
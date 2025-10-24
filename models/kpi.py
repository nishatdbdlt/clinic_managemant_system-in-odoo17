# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class ClinicKPI(models.Model):
    _name = 'clinic.kpi'
    _description = 'Clinic KPI Dashboard'
    _rec_name = 'name'

    name = fields.Char(string='Dashboard Name', default='Clinic KPI Dashboard', readonly=True)
    date_from = fields.Date(string='From Date', default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='To Date', default=fields.Date.today)

    # Patient Statistics
    total_patients = fields.Integer(string='Total Patients', compute='_compute_patient_kpi')
    new_patients = fields.Integer(string='New Patients', compute='_compute_patient_kpi')
    patient_growth = fields.Float(string='Patient Growth (%)', compute='_compute_patient_kpi')

    # Appointment Statistics
    total_appointments = fields.Integer(string='Total Appointments', compute='_compute_appointment_kpi')
    completed_appointments = fields.Integer(string='Completed', compute='_compute_appointment_kpi')
    cancelled_appointments = fields.Integer(string='Cancelled', compute='_compute_appointment_kpi')
    appointment_completion_rate = fields.Float(string='Completion Rate (%)', compute='_compute_appointment_kpi')

    # Revenue Statistics
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_revenue_kpi')
    consultation_revenue = fields.Float(string='Consultation Revenue', compute='_compute_revenue_kpi')
    lab_test_revenue = fields.Float(string='Lab Test Revenue', compute='_compute_revenue_kpi')
    revenue_growth = fields.Float(string='Revenue Growth (%)', compute='_compute_revenue_kpi')

    # Doctor Performance
    most_booked_doctor_id = fields.Many2one('clinic.doctor', string='Most Booked Doctor',
                                            compute='_compute_doctor_kpi')
    total_active_doctors = fields.Integer(string='Active Doctors', compute='_compute_doctor_kpi')
    avg_consultation_per_doctor = fields.Float(string='Avg Consultations/Doctor',
                                               compute='_compute_doctor_kpi')

    # Occupancy Statistics
    cabin_occupancy_rate = fields.Float(string='Cabin Occupancy (%)', compute='_compute_occupancy_kpi')
    ward_occupancy_rate = fields.Float(string='Ward Occupancy (%)', compute='_compute_occupancy_kpi')
    total_admitted_patients = fields.Integer(string='Admitted Patients', compute='_compute_occupancy_kpi')

    # Attendance Statistics
    total_staff = fields.Integer(string='Total Staff', compute='_compute_attendance_kpi')
    avg_attendance_rate = fields.Float(string='Avg Attendance (%)', compute='_compute_attendance_kpi')
    total_overtime_hours = fields.Float(string='Total Overtime Hours', compute='_compute_attendance_kpi')

    # Lab Test Statistics
    total_lab_tests = fields.Integer(string='Total Lab Tests', compute='_compute_lab_kpi')
    completed_lab_tests = fields.Integer(string='Completed Tests', compute='_compute_lab_kpi')
    pending_lab_tests = fields.Integer(string='Pending Tests', compute='_compute_lab_kpi')
    lab_completion_rate = fields.Float(string='Lab Completion Rate (%)', compute='_compute_lab_kpi')

    # Financial KPIs
    total_payroll = fields.Float(string='Total Payroll', compute='_compute_financial_kpi')
    avg_revenue_per_patient = fields.Float(string='Avg Revenue/Patient', compute='_compute_financial_kpi')
    profit_margin = fields.Float(string='Profit Margin (%)', compute='_compute_financial_kpi')

    def _compute_patient_kpi(self):
        for record in self:
            # Total patients registered
            all_patients = self.env['clinic.patient'].search([('create_date', '<=', record.date_to)])
            record.total_patients = len(all_patients)

            # New patients in date range
            new_patients = self.env['clinic.patient'].search([
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to),
            ])
            record.new_patients = len(new_patients)

            # Patient growth calculation
            previous_total = len(self.env['clinic.patient'].search([
                ('create_date', '<', record.date_from)
            ]))
            if previous_total > 0:
                record.patient_growth = ((record.total_patients - previous_total) / previous_total) * 100
            else:
                record.patient_growth = 100.0 if record.total_patients > 0 else 0.0

    def _compute_appointment_kpi(self):
        for record in self:
            appointments = self.env['clinic.appointment'].search([
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to),
            ])
            record.total_appointments = len(appointments)

            completed = appointments.filtered(lambda a: a.state == 'done')
            record.completed_appointments = len(completed)

            cancelled = appointments.filtered(lambda a: a.state == 'cancelled')
            record.cancelled_appointments = len(cancelled)

            if record.total_appointments > 0:
                record.appointment_completion_rate = (record.completed_appointments / record.total_appointments) * 100
            else:
                record.appointment_completion_rate = 0.0

    def _compute_revenue_kpi(self):
        for record in self:
            appointments = self.env['clinic.appointment'].search([
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to),
                ('state', '=', 'done'),
            ])

            record.consultation_revenue = sum(appointments.mapped('total_amount'))

            lab_tests = self.env['clinic.lab.test'].search([
                ('test_date', '>=', record.date_from),
                ('test_date', '<=', record.date_to),
                ('state', '=', 'completed'),
            ])
            record.lab_test_revenue = sum(lab_tests.mapped('test_cost'))

            record.total_revenue = record.consultation_revenue + record.lab_test_revenue

            # Revenue growth
            prev_start = record.date_from - timedelta(days=30)
            prev_end = record.date_from - timedelta(days=1)

            prev_appointments = self.env['clinic.appointment'].search([
                ('appointment_date', '>=', prev_start),
                ('appointment_date', '<=', prev_end),
                ('state', '=', 'done'),
            ])
            prev_revenue = sum(prev_appointments.mapped('total_amount'))

            if prev_revenue > 0:
                record.revenue_growth = ((record.total_revenue - prev_revenue) / prev_revenue) * 100
            else:
                record.revenue_growth = 100.0 if record.total_revenue > 0 else 0.0

    def _compute_doctor_kpi(self):
        for record in self:
            doctors = self.env['clinic.doctor'].search([('active', '=', True)])
            record.total_active_doctors = len(doctors)

            appointments = self.env['clinic.appointment'].search([
                ('appointment_date', '>=', record.date_from),
                ('appointment_date', '<=', record.date_to),
            ])

            # Most booked doctor
            if appointments:
                doctor_counts = {}
                for appointment in appointments:
                    doctor_id = appointment.doctor_id.id
                    doctor_counts[doctor_id] = doctor_counts.get(doctor_id, 0) + 1

                if doctor_counts:
                    most_booked_id = max(doctor_counts, key=doctor_counts.get)
                    record.most_booked_doctor_id = most_booked_id
                else:
                    record.most_booked_doctor_id = False
            else:
                record.most_booked_doctor_id = False

            # Average consultations per doctor
            if record.total_active_doctors > 0:
                record.avg_consultation_per_doctor = len(appointments) / record.total_active_doctors
            else:
                record.avg_consultation_per_doctor = 0.0

    def _compute_occupancy_kpi(self):
        for record in self:
            # Cabin occupancy
            cabins = self.env['clinic.cabin'].search([('active', '=', True)])
            if cabins:
                total_cabin_beds = sum(cabins.mapped('bed_capacity'))
                occupied_cabin_beds = sum(cabins.mapped('occupied_beds'))
                if total_cabin_beds > 0:
                    record.cabin_occupancy_rate = (occupied_cabin_beds / total_cabin_beds) * 100
                else:
                    record.cabin_occupancy_rate = 0.0
            else:
                record.cabin_occupancy_rate = 0.0

            # Ward occupancy
            wards = self.env['clinic.ward'].search([('active', '=', True)])
            if wards:
                total_ward_beds = sum(wards.mapped('bed_capacity'))
                occupied_ward_beds = sum(wards.mapped('occupied_beds'))
                if total_ward_beds > 0:
                    record.ward_occupancy_rate = (occupied_ward_beds / total_ward_beds) * 100
                else:
                    record.ward_occupancy_rate = 0.0
            else:
                record.ward_occupancy_rate = 0.0

            # Total admitted patients
            admitted_patients = self.env['clinic.patient'].search([('is_admitted', '=', True)])
            record.total_admitted_patients = len(admitted_patients)

    def _compute_attendance_kpi(self):
        for record in self:
            employees = self.env['hr.employee'].search([('active', '=', True)])
            record.total_staff = len(employees)

            attendances = self.env['clinic.attendance'].search([
                ('attendance_date', '>=', record.date_from),
                ('attendance_date', '<=', record.date_to),
            ])

            if attendances:
                present_count = len(attendances.filtered(lambda a: a.status in ['present', 'late']))
                total_expected = len(employees) * ((record.date_to - record.date_from).days + 1)

                if total_expected > 0:
                    record.avg_attendance_rate = (present_count / total_expected) * 100
                else:
                    record.avg_attendance_rate = 0.0

                record.total_overtime_hours = sum(attendances.mapped('overtime_hours'))
            else:
                record.avg_attendance_rate = 0.0
                record.total_overtime_hours = 0.0

    def _compute_lab_kpi(self):
        for record in self:
            lab_tests = self.env['clinic.lab.test'].search([
                ('test_date', '>=', record.date_from),
                ('test_date', '<=', record.date_to),
            ])
            record.total_lab_tests = len(lab_tests)

            completed = lab_tests.filtered(lambda t: t.state == 'completed')
            record.completed_lab_tests = len(completed)

            pending = lab_tests.filtered(lambda t: t.state in ['draft', 'sample_collected', 'in_progress'])
            record.pending_lab_tests = len(pending)

            if record.total_lab_tests > 0:
                record.lab_completion_rate = (record.completed_lab_tests / record.total_lab_tests) * 100
            else:
                record.lab_completion_rate = 0.0

    def _compute_financial_kpi(self):
        for record in self:
            payrolls = self.env['clinic.payroll'].search([
                ('payment_date', '>=', record.date_from),
                ('payment_date', '<=', record.date_to),
                ('state', '=', 'paid'),
            ])
            record.total_payroll = sum(payrolls.mapped('net_salary'))

            if record.new_patients > 0:
                record.avg_revenue_per_patient = record.total_revenue / record.new_patients
            else:
                record.avg_revenue_per_patient = 0.0

            # Simple profit margin calculation
            if record.total_revenue > 0:
                record.profit_margin = ((record.total_revenue - record.total_payroll) / record.total_revenue) * 100
            else:
                record.profit_margin = 0.0

    def action_refresh_dashboard(self):
        """Refresh all KPI calculations"""
        self.ensure_one()
        self._compute_patient_kpi()
        self._compute_appointment_kpi()
        self._compute_revenue_kpi()
        self._compute_doctor_kpi()
        self._compute_occupancy_kpi()
        self._compute_attendance_kpi()
        self._compute_lab_kpi()
        self._compute_financial_kpi()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Dashboard refreshed successfully'),
                'type': 'success',
                'sticky': False,
            }
        }
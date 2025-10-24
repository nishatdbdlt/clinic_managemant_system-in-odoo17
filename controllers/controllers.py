# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import json


class ClinicKPIController(http.Controller):

    @http.route('/clinic/kpi/dashboard', type='http', auth='user', website=True)
    def kpi_dashboard(self, **kwargs):
        """Main KPI Dashboard Route"""
        # Get or create KPI record
        kpi = request.env['clinic.kpi'].search([], limit=1, order='id desc')

        if not kpi:
            kpi = request.env['clinic.kpi'].create({
                'name': 'Clinic KPI Dashboard',
                'date_from': datetime.today().replace(day=1),
                'date_to': datetime.today()
            })

        # Prepare data for template
        values = {
            'kpi': kpi,
            'date_from': kpi.date_from.strftime('%Y-%m-%d') if kpi.date_from else '',
            'date_to': kpi.date_to.strftime('%Y-%m-%d') if kpi.date_to else '',
        }

        return request.render('clinic_management_system.clinic_kpi_dashboard_template', values)

    @http.route('/clinic/kpi/update_dates', type='json', auth='user')
    def update_dashboard_dates(self, date_from, date_to, **kwargs):
        """Update dashboard date range via AJAX"""
        kpi = request.env['clinic.kpi'].search([], limit=1, order='id desc')

        if kpi:
            kpi.write({
                'date_from': date_from,
                'date_to': date_to
            })
            kpi.action_refresh_dashboard()

            return {
                'success': True,
                'message': 'Dashboard updated successfully'
            }

        return {
            'success': False,
            'message': 'No dashboard found'
        }

    @http.route('/clinic/kpi/refresh', type='json', auth='user')
    def refresh_dashboard(self, **kwargs):
        """Refresh dashboard data via AJAX"""
        kpi = request.env['clinic.kpi'].search([], limit=1, order='id desc')

        if kpi:
            kpi.action_refresh_dashboard()

            # Return updated data
            return {
                'success': True,
                'data': {
                    'total_patients': kpi.total_patients,
                    'new_patients': kpi.new_patients,
                    'patient_growth': round(kpi.patient_growth, 2),
                    'total_appointments': kpi.total_appointments,
                    'completed_appointments': kpi.completed_appointments,
                    'cancelled_appointments': kpi.cancelled_appointments,
                    'appointment_completion_rate': round(kpi.appointment_completion_rate, 2),
                    'total_revenue': round(kpi.total_revenue, 2),
                    'consultation_revenue': round(kpi.consultation_revenue, 2),
                    'lab_test_revenue': round(kpi.lab_test_revenue, 2),
                    'revenue_growth': round(kpi.revenue_growth, 2),
                    'most_booked_doctor': kpi.most_booked_doctor_id.name if kpi.most_booked_doctor_id else 'N/A',
                    'total_active_doctors': kpi.total_active_doctors,
                    'avg_consultation_per_doctor': round(kpi.avg_consultation_per_doctor, 2),
                    'cabin_occupancy_rate': round(kpi.cabin_occupancy_rate, 2),
                    'ward_occupancy_rate': round(kpi.ward_occupancy_rate, 2),
                    'total_admitted_patients': kpi.total_admitted_patients,
                    'total_staff': kpi.total_staff,
                    'avg_attendance_rate': round(kpi.avg_attendance_rate, 2),
                    'total_overtime_hours': round(kpi.total_overtime_hours, 2),
                    'total_lab_tests': kpi.total_lab_tests,
                    'completed_lab_tests': kpi.completed_lab_tests,
                    'pending_lab_tests': kpi.pending_lab_tests,
                    'lab_completion_rate': round(kpi.lab_completion_rate, 2),
                    'total_payroll': round(kpi.total_payroll, 2),
                    'avg_revenue_per_patient': round(kpi.avg_revenue_per_patient, 2),
                    'profit_margin': round(kpi.profit_margin, 2),
                }
            }

        return {
            'success': False,
            'message': 'No dashboard found'
        }

    @http.route('/clinic/kpi/export', type='http', auth='user')
    def export_kpi_data(self, **kwargs):
        """Export KPI data as JSON"""
        kpi = request.env['clinic.kpi'].search([], limit=1, order='id desc')

        if kpi:
            data = {
                'dashboard_name': kpi.name,
                'date_from': kpi.date_from.strftime('%Y-%m-%d'),
                'date_to': kpi.date_to.strftime('%Y-%m-%d'),
                'patient_stats': {
                    'total_patients': kpi.total_patients,
                    'new_patients': kpi.new_patients,
                    'patient_growth': kpi.patient_growth,
                },
                'appointment_stats': {
                    'total_appointments': kpi.total_appointments,
                    'completed_appointments': kpi.completed_appointments,
                    'cancelled_appointments': kpi.cancelled_appointments,
                    'completion_rate': kpi.appointment_completion_rate,
                },
                'revenue_stats': {
                    'total_revenue': kpi.total_revenue,
                    'consultation_revenue': kpi.consultation_revenue,
                    'lab_test_revenue': kpi.lab_test_revenue,
                    'revenue_growth': kpi.revenue_growth,
                },
                'doctor_stats': {
                    'most_booked_doctor': kpi.most_booked_doctor_id.name if kpi.most_booked_doctor_id else None,
                    'total_active_doctors': kpi.total_active_doctors,
                    'avg_consultation_per_doctor': kpi.avg_consultation_per_doctor,
                },
                'occupancy_stats': {
                    'cabin_occupancy_rate': kpi.cabin_occupancy_rate,
                    'ward_occupancy_rate': kpi.ward_occupancy_rate,
                    'total_admitted_patients': kpi.total_admitted_patients,
                },
                'attendance_stats': {
                    'total_staff': kpi.total_staff,
                    'avg_attendance_rate': kpi.avg_attendance_rate,
                    'total_overtime_hours': kpi.total_overtime_hours,
                },
                'lab_stats': {
                    'total_lab_tests': kpi.total_lab_tests,
                    'completed_lab_tests': kpi.completed_lab_tests,
                    'pending_lab_tests': kpi.pending_lab_tests,
                    'lab_completion_rate': kpi.lab_completion_rate,
                },
                'financial_stats': {
                    'total_payroll': kpi.total_payroll,
                    'avg_revenue_per_patient': kpi.avg_revenue_per_patient,
                    'profit_margin': kpi.profit_margin,
                }
            }

            return request.make_response(
                json.dumps(data, indent=2),
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Content-Disposition', 'attachment; filename="clinic_kpi_export.json"')
                ]
            )

        return request.not_found()
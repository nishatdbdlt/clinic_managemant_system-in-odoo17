# -*- coding: utf-8 -*-
# from odoo import http


# class ClinicManagementSystem(http.Controller):
#     @http.route('/clinic_management_system/clinic_management_system', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/clinic_management_system/clinic_management_system/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('clinic_management_system.listing', {
#             'root': '/clinic_management_system/clinic_management_system',
#             'objects': http.request.env['clinic_management_system.clinic_management_system'].search([]),
#         })

#     @http.route('/clinic_management_system/clinic_management_system/objects/<model("clinic_management_system.clinic_management_system"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('clinic_management_system.object', {
#             'object': obj
#         })


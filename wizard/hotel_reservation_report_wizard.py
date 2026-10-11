# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class HotelReservationReportWizard(models.TransientModel):
    _name = 'hotel.reservation.report.wizard'
    _description = 'Reservation Report Wizard'

    date_from = fields.Date(string='Check-in From')
    date_to = fields.Date(string='Check-in To')
    property_id = fields.Many2one('hotel.property', string='Property')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status')

    def action_print(self):
        self.ensure_one()
        domain = []
        if self.date_from:
            domain.append(('check_in', '>=', self.date_from))
        if self.date_to:
            domain.append(('check_in', '<=', self.date_to))
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.state:
            domain.append(('state', '=', self.state))

        reservations = self.env['hotel.reservation'].search(domain)
        if not reservations:
            raise UserError(_('No reservations match the selected filters.'))
        return self.env.ref(
            'hotel_management.action_report_hotel_reservation'
        ).report_action(reservations)
# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.misc import format_datetime

STATE_COLORS = {
    'draft': '#757575',
    'confirmed': '#1565c0',
    'checked_in': '#2e7d32',
    'checked_out': '#5b2d90',
    'cancelled': '#aa3333',
    'no_show': '#aa3333',
}


class HotelReservationReport(models.AbstractModel):
    _name = 'report.hotel_management.report_hotel_reservation'
    _description = 'Reservation Confirmation Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        Reservation = self.env['hotel.reservation']
        reservations = Reservation.browse(docids)

        guest_stays = {}     
        other_bookings = {}  
        next_booking = {}   
        guest_phone = {}
        guest_email = {}
        payments = {}        
        state_color = {}

        for rec in reservations:
            guest_stays[rec.id] = Reservation.search_count([
                ('guest_id', '=', rec.guest_id.id),
                ('state', '=', 'checked_out'),
                ('id', '!=', rec.id),
            ])

            later_domain = [
                ('room_id', '=', rec.room_id.id),
                ('check_in', '>=', rec.check_out),
                ('state', 'in', ['draft', 'confirmed']),
                ('id', '!=', rec.id),
            ]
            other_bookings[rec.id] = Reservation.search_count(later_domain)
            nxt = Reservation.search(later_domain, order='check_in asc', limit=1)
            next_booking[rec.id] = nxt.check_in if nxt else False

            guest = rec.guest_id
            guest_phone[rec.id] = guest.phone if 'phone' in guest._fields else False
            guest_email[rec.id] = guest.email if 'email' in guest._fields else False

            if 'paid_amount' in rec._fields:
                paid = rec.paid_amount
                balance = rec.balance if 'balance' in rec._fields else rec.total_amount - paid
                payments[rec.id] = {'paid': paid, 'balance': balance}

            state_color[rec.id] = STATE_COLORS.get(rec.state, '#5b2d90')

        return {
            'doc_ids': docids,
            'doc_model': 'hotel.reservation',
            'docs': reservations,
            'guest_stays': guest_stays,
            'other_bookings': other_bookings,
            'next_booking': next_booking,
            'guest_phone': guest_phone,
            'guest_email': guest_email,
            'payments': payments,
            'state_color': state_color,
            'report_date': format_datetime(self.env, fields.Datetime.now()),
        }
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelExtendStayWizard(models.TransientModel):
    _name = 'hotel.reservation.extend.wizard'
    _description = 'Extend / Shorten Stay Wizard'

    reservation_id = fields.Many2one('hotel.reservation', required=True)
    currency_id = fields.Many2one(related='reservation_id.currency_id')
    room_id = fields.Many2one(related='reservation_id.room_id')
    check_in = fields.Date(related='reservation_id.check_in')
    current_check_out = fields.Date(related='reservation_id.check_out', string='Current Check-out')
    current_nights = fields.Integer(related='reservation_id.nights', string='Current Nights')
    current_total = fields.Monetary(related='reservation_id.room_total', string='Current Total',
                                    currency_field='currency_id')

    new_check_out = fields.Date(string='New Check-out', required=True)

    new_nights = fields.Integer(compute='_compute_preview', string='New Nights')
    new_total = fields.Monetary(compute='_compute_preview', string='New Total',
                                currency_field='currency_id')
    difference = fields.Monetary(compute='_compute_preview', string='Difference',
                                 currency_field='currency_id')
    availability_note = fields.Char(compute='_compute_preview', string='Availability')

    @api.depends('new_check_out', 'reservation_id')
    def _compute_preview(self):
        Reservation = self.env['hotel.reservation']
        for wiz in self:
            res = wiz.reservation_id
            wiz.new_nights = wiz.new_total = wiz.difference = 0
            wiz.availability_note = False
            if not (res and wiz.new_check_out and res.check_in):
                continue
            nights = max((wiz.new_check_out - res.check_in).days, 0)
            wiz.new_nights = nights
            wiz.new_total = nights * res.nightly_rate
            wiz.difference = wiz.new_total - res.room_total
            if wiz.new_check_out > res.check_out:
                clash = Reservation.search([
                    ('room_id', '=', res.room_id.id),
                    ('id', '!=', res.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('check_in', '<', wiz.new_check_out),
                    ('check_out', '>', res.check_out),
                ], limit=1)
                wiz.availability_note = (
                    _('Room is booked by %s in the extra days.') % clash.name
                    if clash else _('Room is free for the extra days.'))

    @api.onchange('reservation_id')
    def _onchange_reservation_id(self):
        if self.reservation_id and not self.new_check_out:
            self.new_check_out = self.reservation_id.check_out

    def action_confirm_change(self):
        self.ensure_one()
        if not self.new_check_out:
            raise ValidationError(_('Please choose the new check-out date.'))
        self.reservation_id._change_checkout(self.new_check_out)
        return {'type': 'ir.actions.act_window_close'}
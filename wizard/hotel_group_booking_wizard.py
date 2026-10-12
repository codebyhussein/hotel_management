# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class HotelGroupBookingWizard(models.TransientModel):
    _name = 'hotel.reservation.group.wizard'
    _description = 'Group Booking Wizard'

    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True)
    check_in = fields.Date(required=True)
    check_out = fields.Date(required=True)
    source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('phone', 'Phone'),
        ('website', 'Website'),
        ('other', 'Other'),
    ], default='phone')
    special_request = fields.Text()
    confirm_now = fields.Boolean(string='Confirm immediately')
    line_ids = fields.One2many(
        'hotel.reservation.group.wizard.line', 'wizard_id', string='Rooms')

    def action_create_group(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one room.'))
        rooms = self.line_ids.mapped('room_id')
        if len(rooms) != len(self.line_ids):
            raise UserError(_('The same room is listed more than once.'))

        vals_list = [{
            'guest_id': self.guest_id.id,
            'room_id': line.room_id.id,
            'check_in': self.check_in,
            'check_out': self.check_out,
            'adults': line.adults,
            'children': line.children,
            'source': self.source,
            'special_request': self.special_request,
        } for line in self.line_ids]

        reservations = self.env['hotel.reservation'].create(vals_list)
        reservations.write({'group_ref': reservations[0].name})
        if self.confirm_now:
            reservations.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Group Reservations'),
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form,calendar',
            'domain': [('id', 'in', reservations.ids)],
        }


class HotelGroupBookingWizardLine(models.TransientModel):
    _name = 'hotel.reservation.group.wizard.line'
    _description = 'Group Booking Wizard Line'

    wizard_id = fields.Many2one('hotel.reservation.group.wizard', required=True, ondelete='cascade')
    room_id = fields.Many2one('hotel.room', string='Room', required=True)
    adults = fields.Integer(default=1)
    children = fields.Integer(default=0)
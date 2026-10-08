from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Reservation'
    _order = 'check_in desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    guest_id = fields.Many2one('hotel.guest', required=True)
    room_type_id = fields.Many2one('hotel.room.type', required=True)
    room_id = fields.Many2one(
        'hotel.room', required=True,
        domain="[('room_type_id', '=', room_type_id)]")
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one(
        'res.currency', default=lambda s: s.env.company.currency_id)
    check_in = fields.Date(required=True, default=fields.Date.context_today)
    check_out = fields.Date(required=True)
    actual_check_in = fields.Datetime(readonly=True)
    actual_check_out = fields.Datetime(readonly=True)
    nights = fields.Integer(compute='_compute_nights', store=True)
    adults = fields.Integer(default=1)
    children = fields.Integer()
    nightly_rate = fields.Monetary(compute='_compute_nightly_rate', store=True, readonly=False)
    room_total = fields.Monetary(compute='_compute_room_total', store=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked-in'), ('checked_out', 'Checked-out'),
        ('cancelled', 'Cancelled'), ('no_show', 'No Show')],
        default='draft', required=True)

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for r in self:
            r.nights = (r.check_out - r.check_in).days if r.check_in and r.check_out else 0

    @api.depends('room_id')
    def _compute_nightly_rate(self):
        for r in self:
            r.nightly_rate = r.room_id.nightly_rate

    @api.depends('nights', 'nightly_rate')
    def _compute_room_total(self):
        for r in self:
            r.room_total = r.nights * r.nightly_rate

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for r in self:
            if r.check_in and r.check_out and r.check_out <= r.check_in:
                raise ValidationError("Check-out must be after check-in.")

    @api.constrains('room_id', 'check_in', 'check_out', 'state')
    def _check_double_booking(self):
        for r in self:
            if r.state in ('cancelled', 'no_show'):
                continue
            clash = self.search_count([
                ('id', '!=', r.id), ('room_id', '=', r.room_id.id),
                ('state', 'not in', ('cancelled', 'no_show', 'checked_out')),
                ('check_in', '<', r.check_out), ('check_out', '>', r.check_in)])
            if clash:
                raise ValidationError("This room is already booked for these dates.")

    @api.constrains('adults', 'children', 'room_id')
    def _check_capacity(self):
        for r in self:
            if r.adults + r.children > r.room_id.capacity:
                raise ValidationError("Guests exceed the room capacity.")

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if v.get('name', 'New') == 'New':
                v['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for r in self:
            if r.guest_id.blacklisted:
                raise UserError("This guest is blacklisted.")
        self.write({'state': 'confirmed'})

    def action_check_in(self):
        self.write({'state': 'checked_in', 'actual_check_in': fields.Datetime.now()})
        self.mapped('room_id').write({'state': 'occupied'})

    def action_check_out(self):
        self.write({'state': 'checked_out', 'actual_check_out': fields.Datetime.now()})
        self.mapped('room_id').write({'state': 'dirty'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
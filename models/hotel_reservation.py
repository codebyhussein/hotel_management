# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_in desc, id desc'

    name = fields.Char(
        string='Reservation Reference',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'hotel.reservation.sequence'
        ) or 'New',
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], string='Status', default='draft', tracking=True, copy=False)

    source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('phone', 'Phone'),
        ('website', 'Website'),
        ('other', 'Other'),
    ], string='Source', default='walk_in')

    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True, tracking=True)
    room_id = fields.Many2one('hotel.room', string='Room', required=True, tracking=True)
    property_id = fields.Many2one(
        'hotel.property', string='Property', related='room_id.property_id', store=True
    )

    # حقل room_type في hotel.room نوعه Selection وليس Many2one
    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('suite', 'Suite'),
    ], string='Room Type', related='room_id.room_type', store=True, readonly=True)
        'hotel.property', string='Property', related='room_id.property_id', store=True)
    room_type = fields.Selection(
        'hotel.room', string='Room Type', related='room_id.room_type' , store=True )
    responsible_id = fields.Many2one(
        'res.users', string='Responsible', default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True)

    check_in = fields.Date(string='Check-in', required=True, tracking=True)
    check_out = fields.Date(string='Check-out', required=True, tracking=True)
    actual_check_in = fields.Datetime(string='Actual Check-in', readonly=True, copy=False)
    actual_check_out = fields.Datetime(string='Actual Check-out', readonly=True, copy=False)

    adults = fields.Integer(string='Adults', default=0, required=True)
    children = fields.Integer(string='Children', default=0)

    nights = fields.Integer(compute='_compute_nights', store=True)
    nightly_rate = fields.Monetary(
        compute='_compute_nightly_rate', store=True, readonly=False,
        currency_field='currency_id')
    room_total = fields.Monetary(
        compute='_compute_room_total', store=True, currency_field='currency_id')
    # Mahmoud (Feature 4) سيضيف folio_total / paid_amount / balance ويعدّل total_amount
    total_amount = fields.Monetary(
        compute='_compute_total_amount', store=True, currency_field='currency_id')

    special_request = fields.Text()
    cancel_reason = fields.Text(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Sequence عند الإنشاء
    # ------------------------------------------------------------------
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('name', _('New')) == _('New'):
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 'hotel.reservation.sequence') or _('New')
    #     return super().create(vals_list)

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.nights = max((rec.check_out - rec.check_in).days, 0)
            else:
                rec.nights = 0

    @api.depends('room_id')
    def _compute_nightly_rate(self):
        for rec in self:
            if rec.room_id:
                rec.nightly_rate = rec.room_id.price

    @api.depends('nights', 'nightly_rate')
    def _compute_room_total(self):
        for rec in self:
            rec.room_total = rec.nights * rec.nightly_rate

    @api.depends('room_total')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.room_total

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out <= rec.check_in:
                raise ValidationError(_('Check-out date must be strictly after the Check-in date.'))

    @api.constrains('room_id', 'check_in', 'check_out', 'state')
    def _check_double_booking(self):
        for rec in self:
            if not (rec.room_id and rec.check_in and rec.check_out):
                continue
            if rec.state in ('cancelled', 'no_show'):
                continue
            overlap = self.search([
                ('room_id', '=', rec.room_id.id),
                ('id', '!=', rec.id),
                ('state', 'not in', ['cancelled', 'no_show']),
                ('check_in', '<', rec.check_out),
                ('check_out', '>', rec.check_in),
            ], limit=1)
            if overlap:
                raise ValidationError(_(
                    'Room %(room)s is already booked for these dates (%(ref)s).',
                    room=rec.room_id.display_name, ref=overlap.name))

    @api.constrains('adults', 'children', 'room_id')
    def _check_capacity(self):
        for rec in self:
            if rec.adults < 1:
                raise ValidationError(_('There must be at least 1 adult in the reservation.'))
            if rec.children < 0:
                raise ValidationError(_('Children cannot be negative.'))
            if rec.room_id:
                total = rec.adults + rec.children
                capacity = rec.room_id.capacity
                if capacity > 0 and total > capacity:
                    raise ValidationError(_(
                        'The total number of guests (%(total)s) exceeds the room capacity (%(cap)s).',
                        total=total, cap=capacity))

    @api.constrains('guest_id')
    def _check_blacklist(self):
        for rec in self:
            if rec.guest_id.blacklisted:
                raise ValidationError(_('Guest "%s" is blacklisted and cannot book.') % rec.guest_id.display_name)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Only draft reservations can be confirmed.'))
            rec.state = 'confirmed'

    def action_check_in(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('Reservation must be confirmed before check-in.'))
            if today < rec.check_in:
                raise ValidationError(_('Too early: check-in date is %s.') % rec.check_in)
            if rec.room_id.status != 'available':
                raise ValidationError(_(
                    'Room %(room)s is not available (current status: %(state)s).',
                    room=rec.room_id.display_name, state=rec.room_id.status))
            rec.write({'state': 'checked_in', 'actual_check_in': fields.Datetime.now()})
            rec.room_id.write({'status': 'occupied'})

    def action_check_out(self):
        for rec in self:
            if rec.state != 'checked_in':
                raise ValidationError(_('Reservation must be checked in before check-out.'))
            rec.write({'state': 'checked_out', 'actual_check_out': fields.Datetime.now()})
            # 🔴 التعديل هنا: استخدام status بدلاً من state
            rec.room_id.write({'status': 'needs_cleaning'})

    def action_cancel(self):
        """يفتح wizard لإدخال سبب الإلغاء (إجباري)."""
        self.ensure_one()
        if self.state not in ('draft', 'confirmed'):
            raise ValidationError(_('Only draft or confirmed reservations can be cancelled.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Reservation'),
            'res_model': 'hotel.reservation.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id},
        }

    def _do_cancel(self, reason):
        for rec in self:
            if rec.state not in ('draft', 'confirmed'):
                raise ValidationError(_('Only draft or confirmed reservations can be cancelled.'))
            rec.write({'state': 'cancelled', 'cancel_reason': reason})
            rec.message_post(body=_('Reservation cancelled. Reason: %s') % reason)

    def action_no_show(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('Only confirmed reservations can be marked as No Show.'))
            rec.state = 'no_show'

    # ------------------------------------------------------------------
    # Cron + Website API
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_no_show(self):
        today = fields.Date.context_today(self)
        late = self.search([('state', '=', 'confirmed'), ('check_in', '<', today)])
        for rec in late:
            rec.state = 'no_show'
            rec.message_post(body=_('Automatically marked as No Show (guest did not arrive).'))

    @api.model
    def create_from_website(self, vals):
        """تُستدعى من الـ website/API. ترجّع dict منظم."""
        allowed = {'guest_id', 'room_id', 'check_in', 'check_out',
                   'adults', 'children', 'special_request'}
        clean = {k: v for k, v in (vals or {}).items() if k in allowed}
        missing = [k for k in ('guest_id', 'room_id', 'check_in', 'check_out') if not clean.get(k)]
        if missing:
            raise UserError(_('Missing required fields: %s') % ', '.join(missing))
        clean['source'] = 'website'
        rec = self.create(clean)   # الـ constrains بترفض التداخل/السعة/المحظور
        rec.action_confirm()
        return {
            'id': rec.id,
            'name': rec.name,
            'state': rec.state,
            'nights': rec.nights,
            'total_amount': rec.total_amount,
        }

    def action_cancel(self):
        self.ensure_one()
        ...
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',          # دي اللي بتخليه popup
            'context': {'default_reservation_id': self.id},
        }
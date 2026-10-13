# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from psycopg2 import IntegrityError

CANCEL_FREE_DAYS = 2


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

    booking_type = fields.Selection([
        ('individual', 'Individual'),
        ('group', 'Group'),
    ], string='Booking Type', default='individual', required=True, tracking=True)

    source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('phone', 'Phone'),
        ('website', 'Website'),
        ('other', 'Other'),
    ], string='Source', default='walk_in')

    guest_id = fields.Many2one('hotel.guest', string='Guest', required=True, tracking=True)
    
    # Individual Room
    room_id = fields.Many2one('hotel.room', string='Room', tracking=True)
    
    # Group Rooms
    room_ids = fields.Many2many(
        'hotel.room', 'hotel_reservation_room_rel',
        'reservation_id', 'room_id', string='Rooms'
    )
    room_display = fields.Char(string='Room(s)', compute='_compute_room_display')

    property_id = fields.Many2one(
        'hotel.property', string='Property', compute='_compute_property_id', store=True)
    room_type = fields.Selection(
        related='room_id.room_type', string='Room Type', store=True)
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

    adults = fields.Integer(string='Adults', default=1, required=True)
    children = fields.Integer(string='Children', default=0)

    nights = fields.Integer(compute='_compute_nights', store=True)
    nightly_rate = fields.Monetary(
        compute='_compute_nightly_rate', store=True, readonly=False,
        currency_field='currency_id', tracking=True)
    room_total = fields.Monetary(
        compute='_compute_room_total', store=True, currency_field='currency_id')
    
    total_amount = fields.Monetary(
        compute='_compute_total_amount', store=True, currency_field='currency_id')

    special_request = fields.Text()
    cancel_reason = fields.Text(readonly=True, copy=False)

    cancellation_fee = fields.Monetary(
        readonly=True, copy=False, currency_field='currency_id')

    # ---- Deposit ----
    deposit_amount = fields.Monetary(
        string='Deposit', currency_field='currency_id', tracking=True, copy=False)
    deposit_paid = fields.Boolean(string='Deposit Paid', copy=False, tracking=True)
    deposit_paid_date = fields.Date(readonly=True, copy=False)
    deposit_refund = fields.Monetary(
        string='Deposit Refund', readonly=True, copy=False, currency_field='currency_id')
    balance_after_deposit = fields.Monetary(
        compute='_compute_balance_after_deposit', currency_field='currency_id')

    # ---- Group booking ----
    group_ref = fields.Char(string='Group Reference', copy=False, index=True, readonly=True)
    group_count = fields.Integer(compute='_compute_group_count')
    group_label = fields.Char(compute='_compute_group_label')
    external_id = fields.Char(string='External ID', copy=False, index=True, readonly=True)

    # ---- Reminder ----
    reminder_sent = fields.Boolean(copy=False, readonly=True)

    # ------------------------------------------------------------------
    # Sequence & Onchange
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hotel.reservation.sequence') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if 'deposit_paid' in vals:
            if vals['deposit_paid']:
                for rec in self:
                    deposit_amount = vals.get('deposit_amount', rec.deposit_amount)
                    if deposit_amount <= 0:
                        raise ValidationError(_('Set a positive deposit amount before marking it as paid.'))
                vals.setdefault('deposit_paid_date', fields.Date.context_today(self))
            else:
                vals.setdefault('deposit_paid_date', False)
        return super().write(vals)

    @api.onchange('booking_type', 'room_id', 'room_ids')
    def _onchange_booking_type_and_rooms(self):
        for rec in self:
            if rec.booking_type == 'individual':
                rec.room_ids = [(5, 0, 0)]
                if rec.room_id:
                    rec.adults = rec.room_id.capacity or 1
            elif rec.booking_type == 'group':
                rec.room_id = False
                if rec.room_ids:
                    rec.adults = sum(r.capacity for r in rec.room_ids) or 1

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('room_id', 'room_ids', 'booking_type')
    def _compute_property_id(self):
        for rec in self:
            if rec.booking_type == 'individual' and rec.room_id:
                rec.property_id = rec.room_id.property_id
            elif rec.booking_type == 'group' and rec.room_ids:
                rec.property_id = rec.room_ids[0].property_id
            else:
                rec.property_id = False

    @api.depends('booking_type', 'room_id.room_number', 'room_ids.room_number')
    def _compute_room_display(self):
        for rec in self:
            rooms = rec.room_id if rec.booking_type == 'individual' else rec.room_ids
            rec.room_display = ', '.join(rooms.mapped('room_number'))

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.nights = max((rec.check_out - rec.check_in).days, 0)
            else:
                rec.nights = 0

    @api.depends('room_id', 'room_ids', 'booking_type')
    def _compute_nightly_rate(self):
        for rec in self:
            if rec.booking_type == 'individual' and rec.room_id:
                rec.nightly_rate = rec.room_id.price
            elif rec.booking_type == 'group' and rec.room_ids:
                rec.nightly_rate = sum(r.price for r in rec.room_ids)
            else:
                rec.nightly_rate = 0.0

    @api.depends('nights', 'nightly_rate')
    def _compute_room_total(self):
        for rec in self:
            rec.room_total = rec.nights * rec.nightly_rate

    @api.depends('room_total', 'state', 'cancellation_fee')
    def _compute_total_amount(self):
        for rec in self:
            if rec.state in ('cancelled', 'no_show'):
                rec.total_amount = rec.cancellation_fee
            else:
                rec.total_amount = rec.room_total

    @api.depends('total_amount', 'deposit_amount', 'deposit_paid')
    def _compute_balance_after_deposit(self):
        for rec in self:
            paid = rec.deposit_amount if rec.deposit_paid else 0.0
            rec.balance_after_deposit = rec.total_amount - paid

    def _compute_group_count(self):
        for rec in self:
            rec.group_count = (
                self.search_count([('group_ref', '=', rec.group_ref)])
                if rec.group_ref else 0)

    @api.depends('group_ref')
    def _compute_group_label(self):
        counts = {}
        refs = [r for r in self.mapped('group_ref') if r]
        if refs:
            data = self.read_group(
                [('group_ref', 'in', refs)], ['group_ref'], ['group_ref'])
            counts = {d['group_ref']: d['group_ref_count'] for d in data}
        for rec in self:
            if rec.group_ref:
                rec.group_label = '%s · %s' % (rec.group_ref, counts.get(rec.group_ref, 1))
            else:
                rec.group_label = False

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('booking_type', 'room_id', 'room_ids')
    def _check_rooms_selected(self):
        for rec in self:
            if rec.booking_type == 'individual' and not rec.room_id:
                raise ValidationError(_('Please select a room for Individual booking.'))
            if rec.booking_type == 'group' and not rec.room_ids:
                raise ValidationError(_('Please select at least one room for Group booking.'))

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out <= rec.check_in:
                raise ValidationError(_('Check-out date must be strictly after the Check-in date.'))

    @api.constrains('room_id', 'room_ids', 'booking_type', 'check_in', 'check_out', 'state')
    def _check_double_booking(self):
        for rec in self:
            if not (rec.check_in and rec.check_out) or rec.state in ('cancelled', 'no_show'):
                continue
            
            rooms_to_check = rec.room_id if rec.booking_type == 'individual' else rec.room_ids
            for room in rooms_to_check:
                overlap = self.search([
                    '|', ('room_id', '=', room.id), ('room_ids', 'in', room.id),
                    ('id', '!=', rec.id),
                    ('state', 'not in', ['cancelled', 'no_show']),
                    ('check_in', '<', rec.check_out),
                    ('check_out', '>', rec.check_in),
                    '|', ('state', '!=', 'checked_out'),
                         ('actual_check_out', '=', False),
                ], limit=1)
                if overlap:
                    raise ValidationError(_(
                        'Room %(room)s is already booked for these dates (%(ref)s).',
                        room=room.display_name, ref=overlap.name))

    @api.constrains('adults', 'children', 'room_id', 'room_ids', 'booking_type')
    def _check_capacity(self):
        for rec in self:
            if rec.adults < 1:
                raise ValidationError(_('There must be at least 1 adult in the reservation.'))
            if rec.children < 0:
                raise ValidationError(_('Children cannot be negative.'))
            
            total_guests = rec.adults + rec.children
            if rec.booking_type == 'individual' and rec.room_id:
                capacity = rec.room_id.capacity
            elif rec.booking_type == 'group' and rec.room_ids:
                capacity = sum(r.capacity for r in rec.room_ids)
            else:
                capacity = 0

            if capacity > 0 and total_guests > capacity:
                raise ValidationError(_(
                    'The total number of guests (%(total)s) exceeds total rooms capacity (%(cap)s).',
                    total=total_guests, cap=capacity))

    @api.constrains('guest_id')
    def _check_blacklist(self):
        for rec in self:
            if rec.guest_id.blacklisted:
                raise ValidationError(_('Guest "%s" is blacklisted and cannot book.') % rec.guest_id.display_name)

    @api.constrains('deposit_amount', 'room_total')
    def _check_deposit(self):
        for rec in self:
            if rec.deposit_amount < 0:
                raise ValidationError(_('Deposit cannot be negative.'))
            if rec.deposit_amount > rec.room_total > 0:
                raise ValidationError(_('Deposit cannot exceed the room total.'))

    @api.constrains('deposit_paid', 'deposit_amount')
    def _check_deposit_paid_amount(self):
        for rec in self:
            if rec.deposit_paid and rec.deposit_amount <= 0:
                raise ValidationError(_('Set a positive deposit amount before marking it as paid.'))

    # ------------------------------------------------------------------
    # Emails & Workflow
    # ------------------------------------------------------------------
    def _send_confirmation_email(self):
        template = self.env.ref(
            'hotel_management.mail_template_reservation_confirmation',
            raise_if_not_found=False)
        for rec in self:
            if template and rec.guest_id.email:
                template.send_mail(rec.id, force_send=False)
                rec.message_post(body=_('Confirmation email sent to %s.') % rec.guest_id.email)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Only draft reservations can be confirmed.'))
            if rec.deposit_amount <= 0:
                raise ValidationError(_('A deposit greater than zero is required before confirming.'))
            if not rec.deposit_paid:
                raise ValidationError(_('Register the deposit before confirming this reservation.'))
            rec.state = 'confirmed'
        self._send_confirmation_email()

    def action_check_in(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('Reservation must be confirmed before check-in.'))
            if today < rec.check_in:
                raise ValidationError(_('Too early: check-in date is %s.') % rec.check_in)
            
            rooms = [rec.room_id] if rec.booking_type == 'individual' else rec.room_ids
            for r in rooms:
                if r.status != 'available':
                    raise ValidationError(_(
                        'Room %(room)s is not available (current status: %(state)s).',
                        room=r.display_name, state=r.status))
                r.write({'status': 'occupied'})

            rec.write({'state': 'checked_in', 'actual_check_in': fields.Datetime.now()})

    def action_check_out(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != 'checked_in':
                raise ValidationError(_('Reservation must be checked in before check-out.'))

            vals = {'state': 'checked_out', 'actual_check_out': fields.Datetime.now()}
            if today < rec.check_out and today > rec.check_in:
                vals['check_out'] = today

            rec.write(vals)
            rooms = [rec.room_id] if rec.booking_type == 'individual' else rec.room_ids
            for r in rooms:
                r.write({'status': 'needs_cleaning'})

    def _get_cancellation_fee(self):
        self.ensure_one()
        if self.state != 'confirmed' or not self.check_in:
            return 0.0
        days_left = (self.check_in - fields.Date.context_today(self)).days
        return 0.0 if days_left >= CANCEL_FREE_DAYS else self.nightly_rate

    def _refund_for_fee(self, fee):
        self.ensure_one()
        return max(self.deposit_amount - fee, 0.0) if self.deposit_paid else 0.0

    def action_cancel(self):
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft reservations can be cancelled.'))
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
            if rec.state != 'draft':
                raise ValidationError(_('Only draft reservations can be cancelled.'))
            fee = rec._get_cancellation_fee()
            refund = rec._refund_for_fee(fee)
            rec.write({
                'state': 'cancelled',
                'cancel_reason': reason,
                'cancellation_fee': fee,
                'deposit_refund': refund,
            })

    def action_no_show(self):
        for rec in self:
            fee = rec.nightly_rate
            refund = rec._refund_for_fee(fee)
            rec.write({
                'state': 'no_show',
                'cancellation_fee': fee,
                'deposit_refund': refund,
            })

    def action_register_deposit(self):
        for rec in self:
            if rec.state not in ('draft', 'confirmed'):
                raise ValidationError(_('Deposit can only be registered for draft or confirmed reservations.'))
            if rec.deposit_amount <= 0:
                raise ValidationError(_('Please set a deposit amount first.'))
            rec.write({
                'deposit_paid': True,
                'deposit_paid_date': fields.Date.context_today(self),
            })

    def action_change_room(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Change Room'),
            'res_model': 'hotel.reservation.room.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id},
        }

    def action_extend_stay(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extend Stay'),
            'res_model': 'hotel.reservation.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id},
        }

    def _change_checkout(self, new_check_out):
        self.ensure_one()
        if self.state not in ('confirmed', 'checked_in'):
            raise ValidationError(_('Only confirmed or checked-in reservations can be changed.'))
        if not new_check_out:
            raise ValidationError(_('Please choose the new check-out date.'))
        if new_check_out <= self.check_in:
            raise ValidationError(_('Check-out date must be strictly after the Check-in date.'))
        self.write({'check_out': new_check_out})

    def action_view_group(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Group %s') % self.group_ref,
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form,calendar',
            'domain': [('group_ref', '=', self.group_ref)],
        }
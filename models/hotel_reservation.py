# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

CANCEL_FREE_DAYS = 2
from psycopg2 import IntegrityError


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
        'hotel.property', string='Property', related='room_id.property_id', store=True)
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

    adults = fields.Integer(string='Adults', default=0, required=True)
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

    # ----  Deposit ----
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
    external_id= fields.Char(string='External ID', copy=False, index=True, readonly=True)

    # ---- Reminder ----
    reminder_sent = fields.Boolean(copy=False, readonly=True)

    # ------------------------------------------------------------------
    # Sequence
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hotel.reservation.sequence') or _('New')
        return super().create(vals_list)

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
    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out <= rec.check_in:
                raise ValidationError(_('Check-out date must be strictly after the Check-in date.'))

    @api.constrains('room_id', 'check_in', 'check_out', 'state')
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
                '|', ('state', '!=', 'checked_out'),
                     ('actual_check_out', '=', False),
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

    @api.constrains('deposit_amount', 'room_total')
    def _check_deposit(self):
        for rec in self:
            if rec.deposit_amount < 0:
                raise ValidationError(_('Deposit cannot be negative.'))
            if rec.deposit_amount > rec.room_total > 0:
                raise ValidationError(_('Deposit cannot exceed the room total.'))

    # ------------------------------------------------------------------
    # Emails
    # ------------------------------------------------------------------
    def _send_confirmation_email(self):
        template = self.env.ref(
            'hotel_management.mail_template_reservation_confirmation',
            raise_if_not_found=False)
        for rec in self:
            if template and rec.guest_id.email:
                template.send_mail(rec.id, force_send=False)
                rec.message_post(body=_('Confirmation email sent to %s.') % rec.guest_id.email)
            else:
                rec.message_post(body=_('Confirmation email NOT sent: guest has no email address.'))

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Only draft reservations can be confirmed.'))
            if rec.deposit_amount > 0 and not rec.deposit_paid:
                raise ValidationError(_(
                    'A deposit of %(amount)s is required before confirming %(ref)s.',
                    amount=rec.deposit_amount, ref=rec.name))
            rec.state = 'confirmed'
        self._send_confirmation_email()

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
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state != 'checked_in':
                raise ValidationError(_('Reservation must be checked in before check-out.'))
            # TODO (Mahmoud T-16/T-17): منع الـ check-out لو فيه balance مستحق

            vals = {'state': 'checked_out', 'actual_check_out': fields.Datetime.now()}

            if today < rec.check_out and today > rec.check_in:
                vals['check_out'] = today
                rec.message_post(body=_(
                    'Early check-out: stay shortened from %(old)s to %(new)s.',
                    old=rec.check_out, new=today))
            rec.write(vals)
            rec.room_id.write({'state': 'dirty'}) 
            
                # ---- Cancel + fee ----
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
            rec.message_post(body=_(
                'Reservation cancelled. Reason: %(reason)s. Cancellation fee: %(fee)s. Deposit refund: %(refund)s.',
                reason=reason, fee=fee, refund=refund))

    def _mark_no_show(self, auto=False):
        for rec in self:
            fee = rec.nightly_rate  
            refund = rec._refund_for_fee(fee)
            rec.write({
                'state': 'no_show',
                'cancellation_fee': fee,
                'deposit_refund': refund,
            })
            rec.message_post(body=_(
                '%(prefix)s marked as No Show. Fee: %(fee)s. Deposit refund: %(refund)s.',
                prefix=_('Automatically') if auto else _('Manually'), fee=fee, refund=refund))

    def action_no_show(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('Only confirmed reservations can be marked as No Show.'))
        self._mark_no_show()

    # ---- Deposit ----
    def action_register_deposit(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Deposit can only be registered for draft reservations.'))
            if rec.deposit_amount <= 0:
                raise ValidationError(_('Please set a deposit amount first.'))
            if rec.deposit_paid:
                raise ValidationError(_('Deposit is already registered.'))
            rec.write({
                'deposit_paid': True,
                'deposit_paid_date': fields.Date.context_today(self),
            })
            rec.message_post(body=_('Deposit of %s received.') % rec.deposit_amount)

    # ----  Room change ----
    def action_change_room(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'checked_in'):
            raise ValidationError(_('Room can only be changed for confirmed or checked-in reservations.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Change Room'),
            'res_model': 'hotel.reservation.room.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id},
        }

    def _change_room(self, new_room, reason, keep_rate=False):
        self.ensure_one()
        if self.state not in ('confirmed', 'checked_in'):
            raise ValidationError(_('Room can only be changed for confirmed or checked-in reservations.'))
        old_room = self.room_id
        if new_room == old_room:
            raise ValidationError(_('Please choose a different room.'))
        if new_room.state == 'maintenance':
            raise ValidationError(_('Room %s is under maintenance.') % new_room.display_name)
        if self.state == 'checked_in' and new_room.state != 'available':
            raise ValidationError(_(
                'Room %(room)s is not available now (status: %(state)s).',
                room=new_room.display_name, state=new_room.state))

        vals = {'room_id': new_room.id}
        if keep_rate:
            vals['nightly_rate'] = self.nightly_rate
        self.write(vals)   

        if self.state == 'checked_in':
            old_room.write({'state': 'dirty'})
            new_room.write({'state': 'occupied'})

        self.message_post(body=_(
            'Room changed from %(old)s to %(new)s. Reason: %(reason)s',
            old=old_room.display_name, new=new_room.display_name, reason=reason))

            # ---- Extend / shorten stay ----
    def action_extend_stay(self):
        self.ensure_one()
        if self.state not in ('confirmed', 'checked_in'):
            raise ValidationError(_('Stay can only be changed for confirmed or checked-in reservations.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Extend / Shorten Stay'),
            'res_model': 'hotel.reservation.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id},
        }

    def _change_checkout(self, new_checkout, reason):
        self.ensure_one()
        if self.state not in ('confirmed', 'checked_in'):
            raise ValidationError(_('Stay can only be changed for confirmed or checked-in reservations.'))
        old_checkout = self.check_out
        if new_checkout == old_checkout:
            raise ValidationError(_('The new check-out date is the same as the current one.'))
        if new_checkout <= self.check_in:
            raise ValidationError(_('New check-out must be after the check-in date.'))
        if self.state == 'checked_in' and new_checkout <= fields.Date.context_today(self):
            raise ValidationError(_('For an in-house guest, check-out must be after today. Use Check Out instead.'))

        old_total = self.room_total

        self.write({'check_out': new_checkout})

        diff = self.room_total - old_total
        self.message_post(body=_(
            'Stay changed: check-out %(old)s → %(new)s (%(nights)s nights). '
            'Total difference: %(diff)s. Reason: %(reason)s',
            old=old_checkout, new=new_checkout, nights=self.nights,
            diff=diff, reason=reason))

    # ---- Group ----
    def action_view_group(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Group %s') % self.group_ref,
            'res_model': 'hotel.reservation',
            'view_mode': 'tree,form,calendar',
            'domain': [('group_ref', '=', self.group_ref)],
        }

    # ------------------------------------------------------------------
    # Crons + Website API
    # ------------------------------------------------------------------
    @api.model
    def _cron_check_no_show(self):
        today = fields.Date.context_today(self)
        late = self.search([('state', '=', 'confirmed'), ('check_in', '<', today)])
        late._mark_no_show(auto=True)

    @api.model
    def _cron_send_arrival_reminder(self):
        template = self.env.ref(
            'hotel_management.mail_template_reservation_reminder',
            raise_if_not_found=False)
        if not template:
            return
        tomorrow = fields.Date.context_today(self) + timedelta(days=1)
        reservations = self.search([
            ('state', '=', 'confirmed'),
            ('check_in', '=', tomorrow),
            ('reminder_sent', '=', False),
        ])
        for rec in reservations:
            if rec.guest_id.email:
                template.send_mail(rec.id, force_send=False)
                rec.message_post(body=_('Arrival reminder sent to %s.') % rec.guest_id.email)
            rec.reminder_sent = True

    @api.model
    def _cron_auto_check_out(self):
        today = fields.Date.context_today(self)
        due = self.search([('state', '=', 'checked_in'), ('check_out', '<=', today)])
        for rec in due:
            try:
                with self.env.cr.savepoint():
                    rec.action_check_out()
                    rec.message_post(body=_('Automatically checked out (check-out date reached).'))
            except Exception as e:
                rec.message_post(body=_('Auto check-out failed: %s') % e)



    @api.model
    def create_from_website(self, vals):
        allowed = {'guest_id', 'room_id', 'check_in', 'check_out',
                   'adults', 'children', 'special_request'}
        clean = {k: v for k, v in (vals or {}).items() if k in allowed}
        missing = [k for k in ('guest_id', 'room_id', 'check_in', 'check_out') if not clean.get(k)]
        if missing:
            raise UserError(_('Missing required fields: %s') % ', '.join(missing))
        clean['source'] = 'website'
        rec = self.create(clean)
        rec.action_confirm()
        return {
            'id': rec.id,
            'name': rec.name,
            'state': rec.state,
            'nights': rec.nights,
            'total_amount': rec.total_amount,
        }
            
            
    @api.model
    def create_from_external_api(self, vals):
        """Create an external reservation with idempotency support."""

        vals = vals or {}

        # 1. Validate external_id
        external_id = str(vals.get('external_id') or '').strip()

        if not external_id:
            raise UserError(_('The external_id field is required.'))

        # 2. Return existing reservation if already created
        existing = self.search([
            ('external_id', '=', external_id),
        ], limit=1)

        if existing:
            return existing, False

        # 3. Allow only the required reservation fields
        allowed_fields = {
            'guest_id',
            'room_id',
            'check_in',
            'check_out',
            'adults',
            'children',
            'special_request',
        }

        clean = {
            key: vals[key]
            for key in allowed_fields
            if key in vals
        }

        # 4. Validate required fields
        required_fields = [
            'guest_id',
            'room_id',
            'check_in',
            'check_out',
        ]

        missing = [
            field
            for field in required_fields
            if not clean.get(field)
        ]

        if missing:
            raise UserError(
                _('Missing required fields: %s')
                % ', '.join(missing)
            )

        # 5. Set trusted values on the server
        clean.update({
            'external_id': external_id,
            'source': 'other',
            'state': 'draft',
        })

        # 6. Protect against simultaneous duplicate requests
        try:
            with self.env.cr.savepoint():
                reservation = self.create(clean)
                reservation.action_confirm()

        except IntegrityError:
            # Another request may have created the same external_id
            existing = self.search([
                ('external_id', '=', external_id),
            ], limit=1)

            if existing:
                return existing, False

            raise

        return reservation, True
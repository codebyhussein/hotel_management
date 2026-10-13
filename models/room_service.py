# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


# =========================================
# 1. Housekeeping Task Model
# =========================================
class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Room Service & Task Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Request Reference', required=True, default='New')
    room_id = fields.Many2one('hotel.room', string='Room', required=True, ondelete='restrict', index=True)
    guest_id = fields.Many2one('hotel.guest', string='Guest')
    assigned_user_id = fields.Many2one('res.users', string='Assigned Staff')

    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now)

    task_type = fields.Selection([
        ('housekeeping', 'Housekeeping'),
        ('maintenance', 'Maintenance'),
        ('room_service', 'Room Service')
    ], default='room_service', string='Task Type')

    is_housekeeping = fields.Boolean(string='Housekeeping')
    is_food_ordering = fields.Boolean(string='Food Ordering')
    is_laundry = fields.Boolean(string='Laundry')
    is_extra_towels = fields.Boolean(string='Extra Towels')
    is_guest_supplies = fields.Boolean(string='Guest Supplies')

    housekeeping_type = fields.Selection([
        ('deep_clean', 'Deep Cleaning'),
        ('regular_clean', 'Regular Cleaning'),
        ('turndown', 'Turndown Service')
    ], string='Housekeeping Type', default='regular_clean')

    laundry_type = fields.Selection([
        ('wash_iron', 'Wash & Iron'),
        ('dry_clean', 'Dry Cleaning'),
        ('iron_only', 'Iron Only')
    ], string='Laundry Type', default='wash_iron')

    extra_towels_type = fields.Selection([
        ('bath_sheet', 'Bath Sheets'),
        ('hand_towel', 'Hand Towels'),
        ('pool_towel', 'Pool Towels')
    ], string='Towels Type', default='bath_sheet')

    guest_supplies_type = fields.Selection([
        ('toiletries', 'Toiletries (Soap, Shampoo)'),
        ('coffee_tea', 'Coffee & Tea Tray'),
        ('slippers_robes', 'Slippers & Bathrobes')
    ], string='Supplies Type', default='toiletries')

    food_item_ids = fields.One2many('hotel.room.service.food.line', 'task_id', string='Food Items')

    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='new', string='Status', tracking=True)

    start_date = fields.Datetime(string='Start Date')
    done_date = fields.Datetime(string='Done Date')
    description = fields.Text(string='Special Instructions')

    def action_mark_in_progress(self):
        for rec in self:
            rec.write({
                'state': 'in_progress',
                'start_date': fields.Datetime.now()
            })

    def action_mark_done(self):
        for rec in self:
            rec.write({
                'state': 'done',
                'done_date': fields.Datetime.now()
            })
            if rec.room_id:
                rec.room_id.write({'status': 'available'})

    def action_cancel(self):
        for rec in self:
            if rec.state in ('done', 'cancel'):
                raise UserError(_("You cannot cancel a task that is already done or cancelled!"))
            rec.write({'state': 'cancel'})


# =========================================
# 2. Maintenance Request Model
# =========================================
class HotelMaintenanceRequest(models.Model):
    _name = 'hotel.maintenance.request'
    _description = 'Hotel Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Maintenance Ref', required=True, default='New')
    room_id = fields.Many2one('hotel.room', string='Room', required=True, ondelete='restrict', index=True)

    issue_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('ac', 'AC / HVAC'),
        ('furniture', 'Furniture / Carpentry'),
        ('other', 'Other')
    ], string='Issue Type', required=True)

    urgency = fields.Selection([
        ('0', '0 - Very Low'),
        ('1', '1 - Low'),
        ('2', '2 - Normal'),
        ('3', '3 - Medium'),
        ('4', '4 - High'),
        ('5', '5 - Urgent'),
    ], string='Urgency', default='0')

    assigned_user_id = fields.Many2one('res.users', string='Assigned Staff')
    description = fields.Text(string='Description')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], default='draft', string='Status', tracking=True)

    def action_start_maintenance(self):
        for rec in self:
            rec.write({'state': 'in_progress'})

    def action_done(self):
        for rec in self:
            rec.write({'state': 'done'})

    def action_set_done(self):
        return self.action_done()

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})


# =========================================
# 3. Food Line Model
# =========================================
class HotelRoomServiceFoodLine(models.Model):
    _name = 'hotel.room.service.food.line'
    _description = 'Room Service Food Line'

    task_id = fields.Many2one('hotel.housekeeping.task', string='Task Reference', ondelete='cascade')
    name = fields.Char(string='Food/Drink Item', required=True)
    qty = fields.Integer(string='Quantity', default=1)
    notes = fields.Char(string='Notes')
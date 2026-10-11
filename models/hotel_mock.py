# -*- coding: utf-8 -*-
from odoo import models, fields

# TEMP: امسحي الملف ده كله قبل الدمج مع main


class HotelPropertyMock(models.Model):
    _name = 'hotel.property'
    _description = 'Hotel Property (temp mock)'

    name = fields.Char(required=True)


class HotelRoomTypeMock(models.Model):
    _name = 'hotel.room.type'
    _description = 'Room Type (temp mock)'

    name = fields.Char(required=True)
    base_rate = fields.Float()
    capacity = fields.Integer(default=2)


class HotelRoomMock(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room (temp mock)'
    _rec_name = 'number'

    number = fields.Char(required=True)
    property_id = fields.Many2one('hotel.property')
    room_type_id = fields.Many2one('hotel.room.type')
    capacity = fields.Integer(default=2)
    nightly_rate = fields.Float()
    state = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('dirty', 'Dirty'),
        ('maintenance', 'Maintenance'),
    ], default='available')


class HotelGuestMock(models.Model):
    _name = 'hotel.guest'
    _description = 'Hotel Guest (temp mock)'
    email = fields.Char()

    name = fields.Char(required=True)
    blacklisted = fields.Boolean()
    vip = fields.Boolean()
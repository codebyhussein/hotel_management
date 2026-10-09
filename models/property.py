# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HotelProperty(models.Model):
    _name = 'hotel.property'
    _description = 'Hotel Property'
    _order = 'name asc'

    name = fields.Char(
        string='Property Name',
        required=True,
        index=True
    )
    


    code = fields.Char(
        string='Property Code',
        index=True
    )

    description = fields.Text(
        string='Description'
    )

    address = fields.Char(
        string='Address'
    )

    city = fields.Char(
        string='City'
    )

    country = fields.Char(
        string='Country'
    )

    phone = fields.Char(
        string='Phone'
    )

    email = fields.Char(
        string='Email'
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Rooms belonging to this property
    room_ids = fields.One2many(
        'hotel.room',
        'property_id',
        string='Rooms'
    )

    room_count = fields.Integer(
        string='Room Count',
        compute='_compute_room_count'
    )

    @api.depends('room_ids')
    def _compute_room_count(self):
        for property in self:
            property.room_count = len(property.room_ids)

    def action_view_rooms(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} Rooms',
            'res_model': 'hotel.room',
            'view_mode': 'tree,form',
            'domain': [
                ('property_id', '=', self.id)
            ],
            'context': {
                'default_property_id': self.id,
            },
        }
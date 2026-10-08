from odoo import models, fields


class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Room Type'

    name = fields.Char(required=True)
    capacity = fields.Integer(default=2)
    base_rate = fields.Float()


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Room'
    _rec_name = 'number'

    number = fields.Char(required=True)
    room_type_id = fields.Many2one('hotel.room.type', required=True)
    capacity = fields.Integer(related='room_type_id.capacity', store=True)
    nightly_rate = fields.Float(related='room_type_id.base_rate', store=True)
    state = fields.Selection([
        ('available', 'Available'), ('occupied', 'Occupied'),
        ('dirty', 'Dirty'), ('maintenance', 'Maintenance')],
        default='available')


class HotelGuest(models.Model):
    _name = 'hotel.guest'
    _description = 'Guest'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    blacklisted = fields.Boolean()
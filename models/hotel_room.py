from odoo import models, fields , api


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _order = 'room_number asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # =========================
    # Room Information
    # =========================

    room_number = fields.Char(
        string='Room Number',
        required=True,
        index=True
    )

    room_type = fields.Selection([
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('suite', 'Suite'),
    ], string='Room Type', required=True)

    price = fields.Float(
        string='Price',
        required=True
    )

    capacity = fields.Integer(
        string='Capacity',
        compute='_compute_capacity',
        store=True,
        readonly=True,
    )
    nightly_rate = fields.Float(
        related='price',
        string='Nightly Rate',
    )

    property_id = fields.Many2one(
        'hotel.property',
        string='Property',
        required=True,
        ondelete='restrict',
        index=True,
        default=lambda self: self.env.user.property_id,
    )
    employee_name = fields.Many2one(
    'res.users',
    string='Employee Name',
    required=True,
    
    index=True,
   
    )

    description = fields.Text(
    string='Description'
    )
    
    # =========================
    # Room Status
    # =========================



    status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('needs_cleaning', 'Needs Cleaning'),
    ], string='Status', default='available', required=True, tracking=True)
    @api.depends('room_number')
    def _compute_display_name(self):
        for room in self:
            room.display_name = f"Room {room.room_number}" if room.room_number else 'New Room'
    @api.depends('room_type')
    def _compute_capacity(self):
        capacity_map = {
            'single': 1,
            'double': 2,
            'triple': 3,
            'suite': 2,
        }
        for room in self:
            room.capacity = capacity_map.get(room.room_type, 0)
    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_occupied(self):
        self.write({'status': 'occupied'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    def action_set_needs_cleaning(self):
        self.write({'status': 'needs_cleaning'})

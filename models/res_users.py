# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    property_id = fields.Many2one(
        'hotel.property',
        string='Hotel Property',
        ondelete='restrict'
    )

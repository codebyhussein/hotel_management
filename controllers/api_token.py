# -*- coding: utf-8 -*-

import secrets
from datetime import timedelta
import json
from odoo import api, fields, models


class HotelApiToken(models.Model):
    _name = 'hotel.api_token'
    _description = 'Hotel API Token'
    _rec_name = 'user_id'
    _order = 'create_date desc'

    token = fields.Char(
        string='Token',
        required=True,
        copy=False,
        index=True,
    )

    user_id = fields.Many2one(
       'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True,
    )

    expires_at = fields.Datetime(
        string='Expires At',
        required=True,
        index=True,
    )

    _sql_constraints = [
        (
            'token_unique',
            'UNIQUE(token)',
            'Token must be unique.',
        ),
    ]

    @api.model
    def generate_token(self, user_id):
        """Generate a new API token for an active Odoo user."""

        user = self.env['res.users'].sudo().browse(user_id).exists()

        if not user or not user.active:
            raise ValueError('Invalid or inactive user.')

        token_value = secrets.token_urlsafe(32)

        expires_at = (
            fields.Datetime.now() + timedelta(days=6)
        )

        token_record = self.sudo().create({
            'token': token_value,
            'user_id': user.id,
            'expires_at': expires_at,
        })

        return token_record

    @api.model
    def validate_token(self, token_value):
        """Return the token record if it exists and has not expired."""

        if not token_value:
            return False

        token_record = self.sudo().search([
            ('token', '=', token_value),
            ('expires_at', '>', fields.Datetime.now()),
        ], limit=1)

        if not token_record:
            return False

        if not token_record.user_id.active:
            return False

        return token_record
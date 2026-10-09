
# from datetime import timedelta

# from odoo import fields, http
# from odoo.exceptions import UserError, ValidationError
# from odoo.http import request
# from odoo.tools import format_date

# # Rooms in these statuses can never be shown or booked.
# UNBOOKABLE_ROOM_STATUSES = ['maintenance', 'needs_cleaning']

# # Reservations in these states do NOT block a room.
# # Single source of truth: used by availability search AND next-slot search.
# NON_BLOCKING_RESERVATION_STATES = ['cancelled', 'no_show']

# # How many alternative rooms to suggest in the "not available" message.
# MAX_SUGGESTED_ROOMS = 3


# class HotelRoomController(http.Controller):

#     # =====================================================
#     # Shared helpers
#     # =====================================================

#     @staticmethod
#     def _to_int(value, default):
#         """Safely convert a request value to int (used for filters)."""
#         try:
#             return int(value)
#         except (TypeError, ValueError):
#             return default

#     def _get_bookable_room(self, room_id):
#         """Return the room if it can be shown/booked, else an empty set."""
#         return request.env['hotel.room'].sudo().search([
#             ('id', '=', room_id),
#             ('status', 'not in', UNBOOKABLE_ROOM_STATUSES),
#         ], limit=1)

#     def _get_available_rooms(self, check_in, check_out, adults, children):
#         """Return rooms available for the requested dates and capacity."""
#         domain = [
#             ('status', 'not in', UNBOOKABLE_ROOM_STATUSES),
#             ('capacity', '>=', adults + children),
#         ]

#         if check_in and check_out:
#             overlapping = request.env['hotel.reservation'].sudo().search([
#                 ('check_in', '<', check_out),
#                 ('check_out', '>', check_in),
#                 ('state', 'not in', NON_BLOCKING_RESERVATION_STATES),
#             ])
#             reserved_room_ids = overlapping.mapped('room_id').ids

#             if reserved_room_ids:
#                 domain.append(('id', 'not in', reserved_room_ids))

#         return request.env['hotel.room'].sudo().search(domain)

#     # =====================================================
#     # Availability message helpers
#     # =====================================================

#     def _get_next_available_slot(self, room, check_in, check_out):
#         """Return (first_conflict, next_check_in, next_check_out).

#         - first_conflict: first reservation overlapping the request
#           (empty recordset if none).
#         - next_check_in / next_check_out: earliest window with the SAME
#           number of nights in which the room is completely free.
#         """
#         nights = (check_out - check_in).days
#         candidate = max(check_in, fields.Date.today())

#         reservations = request.env['hotel.reservation'].sudo().search([
#             ('room_id', '=', room.id),
#             ('state', 'not in', NON_BLOCKING_RESERVATION_STATES),
#             ('check_out', '>', candidate),
#         ], order='check_in asc')

#         first_conflict = reservations.filtered(
#             lambda r: r.check_in < check_out and r.check_out > check_in
#         )[:1]

#         for reservation in reservations:
#             # The whole stay fits before this reservation starts.
#             if reservation.check_in >= candidate + timedelta(days=nights):
#                 break
#             # Otherwise push the start to the end of this reservation.
#             if reservation.check_out > candidate:
#                 candidate = reservation.check_out

#         return first_conflict, candidate, candidate + timedelta(days=nights)

#     def _build_unavailable_message(self, room, check_in, check_out,
#                                    adults, children):
#         """Build a helpful, dynamic 'room not available' message."""
#         env = request.env
#         nights = (check_out - check_in).days
#         conflict, next_in, next_out = self._get_next_available_slot(
#             room, check_in, check_out
#         )

#         parts = [
#             'Room %s is not available from %s to %s.' % (
#                 room.room_number,
#                 format_date(env, check_in),
#                 format_date(env, check_out),
#             )
#         ]

#         if conflict:
#             parts.append(
#                 'It is booked from %s to %s.' % (
#                     format_date(env, conflict.check_in),
#                     format_date(env, conflict.check_out),
#                 )
#             )

#         parts.append(
#             'The earliest dates available for %s night%s are %s to %s.' % (
#                 nights,
#                 '' if nights == 1 else 's',
#                 format_date(env, next_in),
#                 format_date(env, next_out),
#             )
#         )

#         # Suggest other rooms that ARE free for the requested dates.
#         others = self._get_available_rooms(
#             check_in, check_out, adults, children
#         ).filtered(lambda r: r.id != room.id)

#         same_type = others.filtered(lambda r: r.room_type == room.room_type)
#         suggestions = (same_type or others)[:MAX_SUGGESTED_ROOMS]

#         if suggestions:
#             parts.append(
#                 'Other rooms available for your dates: %s.'
#                 % ', '.join(suggestions.mapped('room_number'))
#             )

#         return '\n'.join(parts)

#     # =====================================================
#     # Booking helpers
#     # =====================================================

#     @staticmethod
#     def _booking_form_values(room, post):
#         """Values used to (re)fill the booking form."""
#         return {
#             'room': room,
#             'error': False,
#             'check_in': post.get('check_in', ''),
#             'check_out': post.get('check_out', ''),
#             'adults': post.get('adults', '1'),
#             'children': post.get('children', '0'),
#             'guest_name': post.get('guest_name', ''),
#             'email': post.get('email', ''),
#             'phone': post.get('phone', ''),
#             'id_number': post.get('id_number', ''),
#             'special_request': post.get('special_request', ''),
#         }

#     @staticmethod
#     def _parse_booking_form(post):
#         """Clean and type-convert the submitted booking form."""
#         try:
#             check_in = fields.Date.to_date(post.get('check_in'))
#             check_out = fields.Date.to_date(post.get('check_out'))
#         except (ValueError, TypeError):
#             raise ValidationError(
#                 'Please enter valid check-in and check-out dates.'
#             )

#         try:
#             adults = int(post.get('adults') or 1)
#             children = int(post.get('children') or 0)
#         except (ValueError, TypeError):
#             raise ValidationError('Please enter valid guest numbers.')

#         data = {
#             'check_in': check_in,
#             'check_out': check_out,
#             'adults': adults,
#             'children': children,
#             'guest_name': (post.get('guest_name') or '').strip(),
#             'email': (post.get('email') or '').strip(),
#             'phone': (post.get('phone') or '').strip(),
#             'id_number': (post.get('id_number') or '').strip(),
#             'special_request': post.get('special_request', ''),
#         }

#         required = ('check_in', 'check_out', 'guest_name',
#                     'email', 'id_number')
#         if not all(data[key] for key in required):
#             raise ValidationError('Please complete all required fields.')

#         return data

#     def _validate_booking_request(self, room, data):
#         """Business validation. Raises ValidationError on any problem."""
#         check_in = data['check_in']
#         check_out = data['check_out']
#         adults = data['adults']
#         children = data['children']

#         if check_out <= check_in:
#             raise ValidationError('Check-out must be after check-in.')

#         if adults < 1 or children < 0:
#             raise ValidationError('Please enter valid guest numbers.')

#         if room.capacity < adults + children:
#             raise ValidationError(
#                 'This room does not have enough capacity '
#                 'for the selected guests.'
#             )

#         # Recheck availability right before creating the reservation.
#         available_rooms = self._get_available_rooms(
#             check_in, check_out, adults, children
#         )
#         if room.id not in available_rooms.ids:
#             raise ValidationError(
#                 self._build_unavailable_message(
#                     room, check_in, check_out, adults, children
#                 )
#             )

#     @staticmethod
#     def _get_or_create_guest(data):
#         """Find the guest by email, or create partner + guest."""
#         Guest = request.env['hotel.guest'].sudo()

#         guest = Guest.search([('email', '=ilike', data['email'])], limit=1)

#         if guest:
#             if guest.blacklisted:
#                 raise ValidationError(
#                     'This guest cannot make a reservation. '
#                     'Please contact the hotel.'
#                 )
#             return guest

#         # Avoid creating a duplicate ID/passport number.
#         if Guest.search([('id_number', '=', data['id_number'])], limit=1):
#             raise ValidationError(
#                 'This ID/passport number is already registered. '
#                 'Please use the email associated with your '
#                 'existing guest account.'
#             )

#         partner = request.env['res.partner'].sudo().create({
#             'name': data['guest_name'],
#             'email': data['email'],
#             'phone': data['phone'],
#         })

#         return Guest.create({
#             'partner_id': partner.id,
#             'id_number': data['id_number'],
#         })

#     # =====================================================
#     # Routes
#     # =====================================================

#     @http.route('/', type='http', auth='public', website=True)
#     def home(self, **kwargs):
#         featured_rooms = request.env['hotel.room'].sudo().search([
#             ('status', '=', 'available'),
#         ], limit=3)

#         return request.render(
#             'hotel_management.homepage',
#             {'featured_rooms': featured_rooms}
#         )

#     @http.route('/rooms', type='http', auth='public', website=True)
#     def rooms(self, **kwargs):
#         check_in = kwargs.get('check_in', '')
#         check_out = kwargs.get('check_out', '')
#         adults = self._to_int(kwargs.get('adults'), 1)
#         children = self._to_int(kwargs.get('children'), 0)

#         error = False
#         rooms = request.env['hotel.room'].sudo().browse()

#         if adults < 1 or children < 0:
#             error = 'Please enter valid guest numbers.'

#         elif check_in and check_out:
#             try:
#                 check_in_date = fields.Date.to_date(check_in)
#                 check_out_date = fields.Date.to_date(check_out)

#                 if check_out_date <= check_in_date:
#                     error = 'Check-out must be after check-in.'
#                 else:
#                     rooms = self._get_available_rooms(
#                         check_in_date, check_out_date, adults, children
#                     )
#             except (ValueError, TypeError):
#                 error = 'Please enter valid check-in and check-out dates.'

#         else:
#             rooms = self._get_available_rooms(False, False, adults, children)

#         return request.render(
#             'hotel_management.room_list',
#             {
#                 'rooms': rooms,
#                 'check_in': check_in,
#                 'check_out': check_out,
#                 'adults': adults,
#                 'children': children,
#                 'error': error,
#             }
#         )

#     @http.route('/room/<int:room_id>', type='http', auth='public',
#                 website=True)
#     def room_details(self, room_id, **kwargs):
#         room = self._get_bookable_room(room_id)

#         if not room:
#             return request.not_found()

#         return request.render(
#             'hotel_management.room_details',
#             {'room': room}
#         )

#     @http.route(
#         '/booking/<int:room_id>',
#         type='http',
#         auth='public',
#         website=True,
#         methods=['GET', 'POST'],
#         csrf=True,
#     )
#     def online_booking(self, room_id, **post):
#         room = self._get_bookable_room(room_id)

#         if not room:
#             return request.not_found()

#         values = self._booking_form_values(room, post)

#         if request.httprequest.method == 'GET':
#             return request.render('hotel_management.online_booking', values)

#         try:
#             data = self._parse_booking_form(post)
#             self._validate_booking_request(room, data)
#             guest = self._get_or_create_guest(data)

#             # Use the existing reservation method.
#             result = request.env['hotel.reservation'].sudo(
#             ).create_from_website({
#                 'guest_id': guest.id,
#                 'room_id': room.id,
#                 'check_in': data['check_in'],
#                 'check_out': data['check_out'],
#                 'adults': data['adults'],
#                 'children': data['children'],
#                 'special_request': data['special_request'],
#             })

#             reservation = request.env['hotel.reservation'].sudo().browse(
#                 result['id']
#             )

#             return request.render(
#                 'hotel_management.booking_confirmation',
#                 {'reservation': reservation, 'result': result}
#             )

#         except (ValidationError, UserError) as exc:
#             values['error'] = str(exc)
#             return request.render('hotel_management.online_booking', values)

# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import fields, http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from odoo.tools import format_date

# Rooms in these statuses can never be shown or booked.
UNBOOKABLE_ROOM_STATUSES = ['maintenance', 'needs_cleaning']

# Reservations in these states do NOT block a room.
# Single source of truth: used by availability search AND next-slot search.
NON_BLOCKING_RESERVATION_STATES = ['cancelled', 'no_show']

# How many alternative rooms to suggest in the "not available" message.
MAX_SUGGESTED_ROOMS = 3


class HotelRoomController(http.Controller):

    # =====================================================
    # Shared helpers
    # =====================================================

    @staticmethod
    def _to_int(value, default):
        """Safely convert a request value to int (used for filters)."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _get_bookable_room(self, room_id):
        """Return the room if it can be shown/booked, else an empty set."""
        return request.env['hotel.room'].sudo().search([
            ('id', '=', room_id),
            ('status', 'not in', UNBOOKABLE_ROOM_STATUSES),
        ], limit=1)

    def _get_available_rooms(self, check_in, check_out, adults, children):
        """Return rooms available for the requested dates and capacity."""
        domain = [
            ('status', 'not in', UNBOOKABLE_ROOM_STATUSES),
            ('capacity', '>=', adults + children),
        ]

        if check_in and check_out:
            overlapping = request.env['hotel.reservation'].sudo().search([
                ('check_in', '<', check_out),
                ('check_out', '>', check_in),
                ('state', 'not in', NON_BLOCKING_RESERVATION_STATES),
            ])
            reserved_room_ids = overlapping.mapped('room_id').ids

            if reserved_room_ids:
                domain.append(('id', 'not in', reserved_room_ids))

        return request.env['hotel.room'].sudo().search(domain)

    # =====================================================
    # Availability message helpers
    # =====================================================

    def _get_next_available_slot(self, room, check_in, check_out):
        """Return (first_conflict, next_check_in, next_check_out).

        - first_conflict: first reservation overlapping the request
          (empty recordset if none).
        - next_check_in / next_check_out: earliest window with the SAME
          number of nights in which the room is completely free.
        """
        nights = (check_out - check_in).days
        candidate = max(check_in, fields.Date.today())

        reservations = request.env['hotel.reservation'].sudo().search([
            ('room_id', '=', room.id),
            ('state', 'not in', NON_BLOCKING_RESERVATION_STATES),
            ('check_out', '>', candidate),
        ], order='check_in asc')

        first_conflict = reservations.filtered(
            lambda r: r.check_in < check_out and r.check_out > check_in
        )[:1]

        for reservation in reservations:
            # The whole stay fits before this reservation starts.
            if reservation.check_in >= candidate + timedelta(days=nights):
                break
            # Otherwise push the start to the end of this reservation.
            if reservation.check_out > candidate:
                candidate = reservation.check_out

        return first_conflict, candidate, candidate + timedelta(days=nights)

    def _build_unavailable_message(self, room, check_in, check_out,
                                   adults, children):
        """Build a helpful, dynamic 'room not available' message."""
        env = request.env
        nights = (check_out - check_in).days
        conflict, next_in, next_out = self._get_next_available_slot(
            room, check_in, check_out
        )

        parts = [
            'Room %s is not available from %s to %s.' % (
                room.room_number,
                format_date(env, check_in),
                format_date(env, check_out),
            )
        ]

        if conflict:
            parts.append(
                'It is booked from %s to %s.' % (
                    format_date(env, conflict.check_in),
                    format_date(env, conflict.check_out),
                )
            )

        parts.append(
            'The earliest dates available for %s night%s are %s to %s.' % (
                nights,
                '' if nights == 1 else 's',
                format_date(env, next_in),
                format_date(env, next_out),
            )
        )

        # Suggest other rooms that ARE free for the requested dates.
        others = self._get_available_rooms(
            check_in, check_out, adults, children
        ).filtered(lambda r: r.id != room.id)

        same_type = others.filtered(lambda r: r.room_type == room.room_type)
        suggestions = (same_type or others)[:MAX_SUGGESTED_ROOMS]

        if suggestions:
            parts.append(
                'Other rooms available for your dates: %s.'
                % ', '.join(suggestions.mapped('room_number'))
            )

        return '\n'.join(parts)

    # =====================================================
    # Booking helpers
    # =====================================================

    @staticmethod
    def _booking_form_values(room, post):
        """Values used to (re)fill the booking form."""
        return {
            'room': room,
            'error': False,
            'check_in': post.get('check_in', ''),
            'check_out': post.get('check_out', ''),
            'adults': post.get('adults', '1'),
            'children': post.get('children', '0'),
            'guest_name': post.get('guest_name', ''),
            'email': post.get('email', ''),
            'phone': post.get('phone', ''),
            'id_number': post.get('id_number', ''),
            'special_request': post.get('special_request', ''),
        }

    @staticmethod
    def _parse_booking_form(post):
        """Clean and type-convert the submitted booking form."""
        try:
            check_in = fields.Date.to_date(post.get('check_in'))
            check_out = fields.Date.to_date(post.get('check_out'))
        except (ValueError, TypeError):
            raise ValidationError(
                'Please enter valid check-in and check-out dates.'
            )

        try:
            adults = int(post.get('adults') or 1)
            children = int(post.get('children') or 0)
        except (ValueError, TypeError):
            raise ValidationError('Please enter valid guest numbers.')

        data = {
            'check_in': check_in,
            'check_out': check_out,
            'adults': adults,
            'children': children,
            'guest_name': (post.get('guest_name') or '').strip(),
            'email': (post.get('email') or '').strip(),
            'phone': (post.get('phone') or '').strip(),
            'id_number': (post.get('id_number') or '').strip(),
            'special_request': post.get('special_request', ''),
        }

        required = ('check_in', 'check_out', 'guest_name',
                    'email', 'id_number')
        if not all(data[key] for key in required):
            raise ValidationError('Please complete all required fields.')

        return data

    def _validate_booking_request(self, room, data):
        """Business validation. Raises ValidationError on any problem."""
        check_in = data['check_in']
        check_out = data['check_out']
        adults = data['adults']
        children = data['children']

        if check_out <= check_in:
            raise ValidationError('Check-out must be after check-in.')

        if adults < 1 or children < 0:
            raise ValidationError('Please enter valid guest numbers.')

        if room.capacity < adults + children:
            raise ValidationError(
                'This room does not have enough capacity '
                'for the selected guests.'
            )

        # Recheck availability right before creating the reservation.
        available_rooms = self._get_available_rooms(
            check_in, check_out, adults, children
        )
        if room.id not in available_rooms.ids:
            raise ValidationError(
                self._build_unavailable_message(
                    room, check_in, check_out, adults, children
                )
            )

    @staticmethod
    def _get_or_create_guest(data):
        """Find the guest by email, or create partner + guest."""
        Guest = request.env['hotel.guest'].sudo()

        # 1) Existing guest by ID/passport number (unique), 2) else by email.
        guest = Guest.search(
            [('id_number', '=', data['id_number'])], limit=1
        )
        if not guest:
            guest = Guest.search(
                [('email', '=ilike', data['email'])], limit=1
            )

        if guest:
            if guest.blacklisted:
                raise ValidationError(
                    'This guest cannot make a reservation. '
                    'Please contact the hotel.'
                )

            # Reuse the stored profile. Only fill missing details,
            # never overwrite what the hotel already has on file.
            partner = guest.partner_id
            if data['phone'] and not partner.phone:
                partner.phone = data['phone']

            return guest

        partner = request.env['res.partner'].sudo().create({
            'name': data['guest_name'],
            'email': data['email'],
            'phone': data['phone'],
        })

        return Guest.create({
            'partner_id': partner.id,
            'id_number': data['id_number'],
        })

    # =====================================================
    # Routes
    # =====================================================

    @http.route('/booking/guest_lookup', type='json', auth='public',
                website=True)
    def guest_lookup(self, id_number='', **kwargs):
        """Return stored guest details for an exact ID/passport match."""
        id_number = (id_number or '').strip()

        if len(id_number) < 5:
            return {'found': False}

        guest = request.env['hotel.guest'].sudo().search(
            [('id_number', '=', id_number)], limit=1
        )

        # Blacklisted guests are treated as "not found" (reveal nothing).
        if not guest or guest.blacklisted:
            return {'found': False}

        partner = guest.partner_id
        return {
            'found': True,
            'guest_name': partner.name or '',
            'email': partner.email or '',
            'phone': partner.phone or '',
        }

    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kwargs):
        featured_rooms = request.env['hotel.room'].sudo().search([
            ('status', '=', 'available'),
        ], limit=3)

        return request.render(
            'hotel_management.homepage',
            {'featured_rooms': featured_rooms}
        )

    @http.route('/rooms', type='http', auth='public', website=True)
    def rooms(self, **kwargs):
        check_in = kwargs.get('check_in', '')
        check_out = kwargs.get('check_out', '')
        adults = self._to_int(kwargs.get('adults'), 1)
        children = self._to_int(kwargs.get('children'), 0)

        error = False
        rooms = request.env['hotel.room'].sudo().browse()

        if adults < 1 or children < 0:
            error = 'Please enter valid guest numbers.'

        elif check_in and check_out:
            try:
                check_in_date = fields.Date.to_date(check_in)
                check_out_date = fields.Date.to_date(check_out)

                if check_out_date <= check_in_date:
                    error = 'Check-out must be after check-in.'
                else:
                    rooms = self._get_available_rooms(
                        check_in_date, check_out_date, adults, children
                    )
            except (ValueError, TypeError):
                error = 'Please enter valid check-in and check-out dates.'

        else:
            rooms = self._get_available_rooms(False, False, adults, children)

        return request.render(
            'hotel_management.room_list',
            {
                'rooms': rooms,
                'check_in': check_in,
                'check_out': check_out,
                'adults': adults,
                'children': children,
                'error': error,
            }
        )

    @http.route('/room/<int:room_id>', type='http', auth='public',
                website=True)
    def room_details(self, room_id, **kwargs):
        room = self._get_bookable_room(room_id)

        if not room:
            return request.not_found()

        return request.render(
            'hotel_management.room_details',
            {'room': room}
        )

    @http.route(
        '/booking/<int:room_id>',
        type='http',
        auth='public',
        website=True,
        methods=['GET', 'POST'],
        csrf=True,
    )
    def online_booking(self, room_id, **post):
        room = self._get_bookable_room(room_id)

        if not room:
            return request.not_found()

        values = self._booking_form_values(room, post)

        if request.httprequest.method == 'GET':
            return request.render('hotel_management.online_booking', values)

        try:
            data = self._parse_booking_form(post)
            self._validate_booking_request(room, data)
            guest = self._get_or_create_guest(data)

            # Use the existing reservation method.
            result = request.env['hotel.reservation'].sudo(
            ).create_from_website({
                'guest_id': guest.id,
                'room_id': room.id,
                'check_in': data['check_in'],
                'check_out': data['check_out'],
                'adults': data['adults'],
                'children': data['children'],
                'special_request': data['special_request'],
            })

            reservation = request.env['hotel.reservation'].sudo().browse(
                result['id']
            )

            return request.render(
                'hotel_management.booking_confirmation',
                {'reservation': reservation, 'result': result}
            )

        except (ValidationError, UserError) as exc:
            values['error'] = str(exc)
            return request.render('hotel_management.online_booking', values)
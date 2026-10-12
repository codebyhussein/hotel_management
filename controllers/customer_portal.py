# -*- coding: utf-8 -*-

from odoo import fields, http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager # pyright: ignore[missing-import

# Rooms in these statuses can never be booked.
UNBOOKABLE_ROOM_STATUSES = ['maintenance', 'needs_cleaning']

# Reservations in these states do NOT occupy a room.
FREE_RESERVATION_STATES = ['cancelled', 'no_show', 'checked_out']


class HotelCustomerPortal(CustomerPortal):

    # =====================================================
    # Helpers
    # =====================================================

    def _get_current_guest(self):
        """Return the hotel guest linked to the logged-in portal user."""
        Guest = request.env['hotel.guest'].sudo()
        partner = request.env.user.partner_id

        # 1) Exact link: the guest uses the same partner as the user.
        guest = Guest.search([('partner_id', '=', partner.id)], limit=1)

        # 2) Fallback: same email (guest created from a website booking
        #    or by reception gets its own partner record).
        if not guest and partner.email:
            guest = Guest.search(
                [('email', '=ilike', partner.email)], limit=1
            )

        return guest

    def _get_guest_reservation_domain(self, guest):
        """Limit reservations to the current guest."""
        return [('guest_id', '=', guest.id)]

    def _render_no_guest(self):
        values = self._prepare_portal_layout_values()
        values['page_name'] = 'hotel_reservations'
        return request.render('hotel_management.portal_no_guest', values)

    # =====================================================
    # Portal home dashboard (/my)
    # =====================================================

    def _get_hotel_dashboard(self):
        """Numbers shown on the portal dashboard cards."""
        env = request.env
        today = fields.Date.context_today(env['hotel.reservation'])
        Room = env['hotel.room'].sudo()
        Reservation = env['hotel.reservation'].sudo()

        # --- Hotel-wide availability for today -------------------------
        total_rooms = Room.search_count([])
        bookable_rooms = Room.search(
            [('status', 'not in', UNBOOKABLE_ROOM_STATUSES)]
        )
        occupied_rooms = Reservation.search([
            ('check_in', '<=', today),
            ('check_out', '>', today),
            ('state', 'not in', FREE_RESERVATION_STATES),
        ]).mapped('room_id')
        available_rooms = bookable_rooms - occupied_rooms

        # --- Current guest reservations --------------------------------
        reservation_count = 0
        booked_rooms_count = 0
        guest = self._get_current_guest()
        if guest:
            my_reservations = Reservation.search(
                self._get_guest_reservation_domain(guest)
            )
            reservation_count = len(my_reservations)
            active = my_reservations.filtered(
                lambda r: r.state not in FREE_RESERVATION_STATES
                and r.check_out and r.check_out >= today
            )
            booked_rooms_count = len(active.mapped('room_id'))

        return {
            'reservation_count': reservation_count,
            'booked_rooms_count': booked_rooms_count,
            'available_rooms_count': len(available_rooms),
            'total_rooms_count': total_rooms,
            # True when no room is occupied today: the hotel is empty.
            'hotel_is_empty': bool(total_rooms) and not occupied_rooms,
        }

    @http.route()
    def home(self, **kw):
        response = super().home(**kw)
        if hasattr(response, 'qcontext'):
            response.qcontext['hotel_dashboard'] = self._get_hotel_dashboard()
            response.qcontext['hotel_portal_invoices'] = request.env[
                'account.move'
            ].search(
                [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                ],
                order='invoice_date desc, id desc',
                limit=5,
            )
        return response

    # =====================================================
    # Portal home counter
    # =====================================================

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)

        if 'hotel_reservation_count' in counters:
            guest = self._get_current_guest()
            values['hotel_reservation_count'] = (
                request.env['hotel.reservation'].sudo().search_count(
                    self._get_guest_reservation_domain(guest)
                ) if guest else 0
            )

        return values

    # =====================================================
    # Reservations list
    # =====================================================

    @http.route(
        ['/my/hotel/reservations'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_my_hotel_reservations(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kwargs
    ):
        guest = self._get_current_guest()
        if not guest:
            return self._render_no_guest()

        Reservation = request.env['hotel.reservation'].sudo()
        domain = self._get_guest_reservation_domain(guest)

        if date_begin:
            domain.append(('check_in', '>=', date_begin))

        if date_end:
            domain.append(('check_out', '<=', date_end))

        total = Reservation.search_count(domain)

        pager_values = pager(
            url='/my/hotel/reservations',
            total=total,
            page=page,
            step=10,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
        )

        reservations = Reservation.search(
            domain,
            order='check_in desc, id desc',
            limit=10,
            offset=pager_values['offset'],
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'hotel_reservations',
            'reservations': reservations,
            'pager': pager_values,
            'default_url': '/my/hotel/reservations',
            'guest': guest,
        })

        return request.render(
            'hotel_management.portal_my_hotel_reservations',
            values,
        )

    # =====================================================
    # Reservation details
    # =====================================================

    @http.route(
        ['/my/hotel/reservation/<int:reservation_id>'],
        type='http',
        auth='user',
        website=True,
    )
    def portal_hotel_reservation_detail(self, reservation_id, **kwargs):
        guest = self._get_current_guest()
        if not guest:
            return self._render_no_guest()

        reservation = request.env['hotel.reservation'].sudo().search([
            ('id', '=', reservation_id),
            ('guest_id', '=', guest.id),
        ], limit=1)

        if not reservation:
            return request.not_found()

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'hotel_reservation',
            'reservation': reservation,
        })

        return request.render(
            'hotel_management.portal_hotel_reservation_detail',
            values,
        )
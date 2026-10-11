import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.exceptions import UserError, ValidationError
import json


_logger = logging.getLogger(__name__)
db = 'hotel_management_db'

class HotelManagementTokenAPI(http.Controller):
    
    
    

    
    
# Endpoint to get the current logged-in user's details with token authentication
    @http.route(
    '/api/token/login',
    type='http',
    auth='none',
    methods=['POST'],
        csrf=False,)
    def token_login(self, **kwargs):

        params = request.httprequest.get_json(silent=True) or {}

        username = params.get('username')
        password = params.get('password')

        if not username or not password:
            return request.make_json_response({
                'status': 'error',
                'message': 'Username and password are required',
            }, status=400)

        try:
            uid = request.session.authenticate(
                db,
                username,
                password,
            )

            if not uid:
                return request.make_json_response({
                    'status': 'error',
                    'message': 'Invalid username or password',
                }, status=401)

            token_record = request.env[
                'hotel.api_token'
            ].sudo().generate_token(uid)

            return request.make_json_response({
                'status': 'success',
                'message': 'Login successful',
                'data': {
                    'user_id': uid,
                    'token': token_record.token,
                    'expires_at': token_record.expires_at,
                },
            })

        except AccessDenied:
            return request.make_json_response({
                'status': 'error',
                'message': 'Invalid username or password',
            }, status=401)

        except Exception:
            _logger.exception('Hotel API token login failed')

            return request.make_json_response({
                'status': 'error',
                'message': 'Login failed',
            }, status=500)
 # =====================================================
    # Helper: Validate Bearer Token
    # =====================================================

    def _authenticate_token(self):
        auth_header = request.httprequest.headers.get(
            'Authorization', ''
        )

        if not auth_header.startswith('Bearer '):
            return None

        token_value = auth_header.split(' ', 1)[1].strip()

        if not token_value:
            return None

        token_record = request.env[
            'hotel.api_token'
        ].sudo().validate_token(token_value)

        if not token_record:
            return None

        # Switch to the token owner's identity.
        request.update_env(user=token_record.user_id.id)

        return token_record.user_id

    # =====================================================
    # Endpoint: Get Available Rooms
    # GET /api/token/rooms/available
    # =====================================================

    @http.route(
        '/api/token/rooms/available',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def get_available_rooms(self, **kwargs):

        try:
            user = self._authenticate_token()

            if not user:
                return request.make_json_response({
                    'status': 'error',
                    'message': 'Invalid or expired token',
                }, status=401)

            rooms = request.env['hotel.room'].search([
                ('status', '=', 'available')
            ])

            rooms_data = []

            for room in rooms:
                rooms_data.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.room_type,
                    'price': room.price,
                    'nightly_rate': room.nightly_rate,
                    'capacity': room.capacity,
                    'description': room.description,
                    'status': room.status,
                    'property_id': room.property_id.id,
                    'property_name': room.property_id.display_name,
                    'room_image': (
                        f'/web/image/hotel.room/{room.id}/room_image'
                        if room.room_image else False
                    ),
                })

            return request.make_json_response({
                'status': 'success',
                'count': len(rooms_data),
                'data': rooms_data,
            })

        except Exception:
            _logger.exception('Failed to get available rooms')

            return request.make_json_response({
                'status': 'error',
                'message': 'Failed to retrieve available rooms',
            }, status=500)

    # =====================================================
    # Endpoint: Get Room Details
    # GET /api/token/rooms/<room_id>
    # =====================================================

    @http.route(
        '/api/token/rooms/<int:room_id>',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def get_room_details(self, room_id, **kwargs):

        try:
            user = self._authenticate_token()

            if not user:
                return request.make_json_response({
                    'status': 'error',
                    'message': 'Invalid or expired token',
                }, status=401)

            room = request.env['hotel.room'].browse(room_id).exists()

            if not room:
                return request.make_json_response({
                    'status': 'error',
                    'message': 'Room not found',
                }, status=404)

            return request.make_json_response({
                'status': 'success',
                'data': {
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.room_type,
                    'price': room.price,
                    'nightly_rate': room.nightly_rate,
                    'capacity': room.capacity,
                    'description': room.description,
                    'status': room.status,
                    'property_id': room.property_id.id,
                    'property_name': room.property_id.display_name,
                    'property_address': room.property_id.address,
                    'room_image': (
                        f'/web/image/hotel.room/{room.id}/room_image'
                        if room.room_image else False
                    ),
                },
            })

        except Exception:
            _logger.exception('Failed to get room details')

            return request.make_json_response({
                'status': 'error',
                'message': 'Failed to retrieve room details',
            }, status=500)

    # =====================================================
    # Endpoint: Get All Rooms
    # GET /api/token/rooms
    # =====================================================

    @http.route(
        '/api/token/rooms',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
    )
    def get_rooms(self, **kwargs):

        try:
            user = self._authenticate_token()

            if not user:
                return request.make_json_response({
                    'status': 'error',
                    'message': 'Invalid or expired token',
                }, status=401)

            rooms = request.env['hotel.room'].search([])

            rooms_data = []

            for room in rooms:
                rooms_data.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type': room.room_type,
                    'price': room.price,
                    'nightly_rate': room.nightly_rate,
                    'capacity': room.capacity,
                    'description': room.description,
                    'status': room.status,
                    'property_id': room.property_id.id,
                    'property_name': room.property_id.display_name,
                    'room_image': (
                        f'/web/image/hotel.room/{room.id}/room_image'
                        if room.room_image else False
                    ),
                })

            return request.make_json_response({
                'status': 'success',
                'count': len(rooms_data),
                'data': rooms_data,
            })

        except Exception:
            _logger.exception('Failed to get rooms')

            return request.make_json_response({
                'status': 'error',
                'message': 'Failed to retrieve rooms',
            }, status=500)
        
        
    @http.route(
        '/api/token/reservations',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def create_reservation(self, **kwargs):

        # 1. Authenticate using Bearer Token
        user = self._authenticate_token()

        if not user:
            return request.make_response(
                json.dumps({
                    'success': False,
                    'message': 'Invalid or expired token.',
                }),
                headers=[('Content-Type', 'application/json')],
                status=401,
            )

        # 2. Read JSON body
        payload = request.httprequest.get_json(silent=True)

        if not isinstance(payload, dict):
            return request.make_response(
                json.dumps({
                    'success': False,
                    'message': 'A valid JSON object is required.',
                }),
                headers=[('Content-Type', 'application/json')],
                status=400,
            )

        try:
            # 3. Create reservation through shared model method
            reservation, created = request.env[
                'hotel.reservation'
            ].create_from_external_api(payload)

            response_data = {
                'success': True,
                'created': created,
                'message': (
                    'Reservation created successfully.'
                    if created
                    else 'Reservation already exists.'
                ),
                'data': {
                    'id': reservation.id,
                    'name': reservation.name,
                    'external_id': reservation.external_id,
                    'source': reservation.source,
                    'state': reservation.state,
                    'guest_id': reservation.guest_id.id,
                    'room_id': reservation.room_id.id,
                    'check_in': str(reservation.check_in),
                    'check_out': str(reservation.check_out),
                    'nights': reservation.nights,
                    'total_amount': reservation.total_amount,
                },
            }

            status = 201 if created else 200

        except (UserError, ValidationError) as exc:
            response_data = {
                'success': False,
                'message': str(exc),
            }
            status = 400

        return request.make_response(
            json.dumps(response_data),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )
     
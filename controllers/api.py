import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied


_logger = logging.getLogger(__name__)
db = 'hotel_management_db'


class HotelManagementAPI(http.Controller):

    # Login endpoint for the hotel Login API

    @http.route('/api/login', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self, **kwargs):

        # Get request data
        params = request.httprequest.get_json(silent=True) or {}

        username = params.get('username')
        password = params.get('password')

        # Validate required fields
        if not username or not password:
            return request.make_json_response(
                {
                    'status': 'error',
                    'message': 'Username and password are required'
                },
                status=400
            )

        try:
            # Authenticate user
            uid = request.session.authenticate(
                db,
                username,
                password
            )

            if not uid:
                return request.make_json_response(
                    {
                        'status': 'error',
                        'message': 'Invalid username or password'
                    },
                    status=401
                )

            # Update current environment
            request.update_env(user=uid)

            user = request.env['res.users'].sudo().browse(uid)

            return request.make_json_response({
                'status': 'success',
                'message': 'Login successful',
                'data': {
                    'user_id': user.id,
                    'user_name': user.name,
                    'session_id': request.session.sid,
                }
            })

        except AccessDenied:
            return request.make_json_response(
                {
                    'status': 'error',
                    'message': 'Invalid username or password'
                },
                status=401
            )

        except Exception:
            _logger.exception('Hotel API login failed')

            return request.make_json_response(
                {
                    'status': 'error',
                    'message': 'Username or password is incorrect'
                },
                status=500
            )

    # Endpoint to get available rooms

    @http.route(
        '/api/rooms/available',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def get_available_rooms(self, **kwargs):
        try:
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

    # Endpoint to get room details by ID

    @http.route(
        '/api/rooms/<int:room_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def get_room_details(self, room_id, **kwargs):
        try:
            room = request.env['hotel.room'].browse(room_id)

            if not room.exists():
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
    
    # Endpoint to get all rooms
    
    @http.route(
    '/api/rooms',
    type='http',
    auth='user',
    methods=['GET'],
    csrf=False
        )
    def get_rooms(self, **kwargs):
        try:
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
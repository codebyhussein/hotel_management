# -*- coding: utf-8 -*-
{
    'name': "hotel_management",
    'summary': "Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.",
    'description': """
        Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'mail', 'website'],
    'data': [
        # Security
        'security/hotel_security.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',

        # Data
        'data/hotel_reservation_data.xml',

        # Views
        'views/guest.xml',
        'views/housekeeping.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',

        # Website templates
        'views/homepage.xml',
        'views/room_templates_website.xml',
        'views/online_booking_templates.xml',

        # Menus
        'views/menus.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
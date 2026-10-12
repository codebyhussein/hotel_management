
{
    'name': "Hotel Management",

    'summary': "Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.",

    'description': """
Hotel Management
================

A complete Odoo solution for managing hotel operations efficiently.

Key Features:
- Manage hotel rooms and room types.
- Manage guests and their information.
- Create and manage hotel bookings.
- Track room availability and booking status.
- Manage check-in and check-out operations.
- Organize hotel data through clear and user-friendly views.
- Support efficient day-to-day hotel management.

This module provides a centralized system to simplify hotel management
and improve operational efficiency.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'application': True,
    'installable': True,

<<<<<<< HEAD
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'account', 'product'],
=======
    'depends': [
        'base',
        'mail',
        'website',
        'crm',
    ],
>>>>>>> e58f499f74761fc542cc78bd49a2d919ef5c3998

    'data': [
<<<<<<< HEAD
        'security/hotel_security.xml',
        'security/groups.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hotel_reservation_data.xml',
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',
        'views/housekeeping.xml',
        'views/guest.xml',
        'views/hotel_reservation_views.xml',
=======
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

        'views/crm_lead_view.xml',
        # wizards
        'wizard/room_report_excel.xml',
        # Website Templates
        'views/homepage.xml',
        'views/room_templates_website.xml',
        'views/online_booking_templates.xml',

        # Menus
>>>>>>> e58f499f74761fc542cc78bd49a2d919ef5c3998
        'views/menus.xml',
        'views/folio_payment_views.xml',
        'views/hotel_reservation_inherit_views.xml',
        'report/folio_report.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],
}

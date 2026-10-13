{
    'name': 'Hotel Management',

    'summary': 'Complete hotel management solution for managing rooms, guests, bookings, and daily hotel operations.',

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

    'author': 'My Company',
    'website': 'https://www.yourcompany.com',

    'category': 'Uncategorized',
    'version': '0.1',

    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail',
        'product',
        'website',
        'crm',
    ],

    'data': [
        # ==========================================
        # Security
        # ==========================================
        'security/security_group.xml',
        'security/hotel_security.xml',
        'security/ir.model.access.csv',

        # ==========================================
        # Data
        # ==========================================
        'data/ir_sequence.xml',
        'data/hotel_reservation_data.xml',
        'data/inquiry_confirmation.xml',
        'report/reservation_report.xml',
        'data/mail_template_data.xml',
        'data/hotel_reminder_data.xml',

        # ==========================================
        # Core Views
        # ==========================================
        'views/property.xml',
        'views/guest.xml',
        'views/hotel_room.xml',
        'views/room_service.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_reservation_inherit_views.xml',
        'views/maintenance_request.xml',
        'views/res_user.xml',
        'views/crm_lead_view.xml',

        # ==========================================
        # Mail Templates
        # ==========================================
        'views/mail_template.xml',

        # ==========================================
        # Wizards

       
        'wizard/room_service.xml',
        'wizard/hotel_reservation_report_wizard_views.xml',
        'wizard/hotel_room_change_wizard_views.xml',
        'wizard/hotel_extend_stay_wizard_views.xml',
        'wizard/all_rooms_report_pdf.xml',
        'wizard/bulk_assign_wizard.xml',

        # ==========================================
        # Reports
        # ==========================================
        'report/room_report_pdf.xml',
        'report/room_report_excel.xml',
        'report/all_rooms_report_pdf.xml',

        # ==========================================
        # Other Views
        # ==========================================
        'views/room_report.xml',
        'views/folio_payment_views.xml',
        'views/hotel_reservation_dashboard.xml',

        # ==========================================
        # Website Templates
        # ==========================================
        'views/homepage.xml',
        'views/room_templates_website.xml',
        'views/online_booking_templates.xml',

        # ==========================================
        # Portal
        # ==========================================
        'views/portal/portal_views.xml',
        'views/portal/portal_home.xml',

        # ==========================================
        # Menus
        # ==========================================
        'views/menus.xml',
    ],

    # ==========================================
    # Application Settings
    # ==========================================
    'application': True,
    'installable': True,

    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
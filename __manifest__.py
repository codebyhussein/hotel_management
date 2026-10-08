# -*- coding: utf-8 -*-
{
    'name': 'Hotel Management',

    'summary': 'Hotel Management System',

    'description': """
        Hotel Management System
    """,

    'author': 'My Company',
    'website': 'https://www.yourcompany.com',

    'category': 'Operations',
    'version': '0.1',

    'depends': [
        'base',
        'mail',
    
    ],

    'data': [

        # Security
        'security/hotel_security.xml',
        'security/ir.model.access.csv',
        'security/groups.xml',

        # Views
        'views/hotel_room.xml',
        'views/property.xml',
        'views/res_user.xml',
        'views/menus.xml',

    ],

    'demo': [],
}

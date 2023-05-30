# -*- coding: utf-8 -*-
{
    'name': "Hospital Universitario - Productividad",

    'summary': 'Módulo de inventario para Hospital Universitario',

    'author': "Hexium Software Factory",
    'website': "https://hexium.com.ar",
    'category': 'Uncategorized',
    'version': '1.0',
    'installable': True,
    'application': True,

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        # Data
        'data/ir.module.category.csv',

        # Security
        'security/res.groups.xml',
        'security/ir.model.access.csv',

        # Views
        'views/productividad_views.xml',
        'views/metodo_calculo_views.xml',
        'views/configuracion_views.xml',
        'views/hr_employee.xml',

        # Menu
        'views/menu.xml'
    ],
}
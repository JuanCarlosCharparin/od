# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductividadMetodoCalculo(models.Model):
    _name = 'hu_productividad.metodo_calculo'
    _description = 'Productividad - Método de cálculo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True, tracking=True)
    tipo = fields.Selection([
        ('generico', 'Genérico'),
        ('personalizado', 'Personalizado')
    ], string='Tipo', required=True, tracking=True)
    metodo_calculo_variable_ids = fields.One2many('hu_productividad.metodo_calculo_variable', 'metodo_calculo_id')


class ProductividadMetodoCalculoVariable(models.Model):
    _name = 'hu_productividad.metodo_calculo_variable'
    _description = 'Productividad - Variable de método de cálculo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    agrupador_prestaciones_ids = fields.Many2many(
        'hu_productividad.agrupador_prestaciones',
        relation='hu_prod_metodo_calculo_var_agrup_prestaciones',
        column1='metodo_calculo_variable_id',
        column2='agrupador_prestaciones_id',
        string='Agrupadores de prestaciones'
    )
    prestacion_ids = fields.Many2many(
        'hu_productividad.prestacion',
        relation='hu_prod_metodo_calculo_var_prestacion',
        column1='metodo_calculo_variable_id',
        column2='prestacion_id',
        string='Prestaciones'
    )
    forma_calculo = fields.Selection([
        ('puntaje', 'Por puntaje'),
        ('porcentaje_facturado', 'Porcentaje facturado'),
        ('monto_fijo_cantidad', 'Monto fijo por cantidad'),
        ('monto_fijo', 'Monto fijo'),
        ('formula_vieja', 'Fórmula vieja'),
    ], string='Forma de Cálculo', required=True, tracking=True)

    # Según forma de cálculo
    base = fields.Integer(string='Base', tracking=True)
    tipo_punto_id = fields.Many2one('hu_productividad.tipo_punto', string='Tipo de punto', tracking=True)
    valor_punto = fields.Float(string='Valor punto', tracking=True)
    porcentaje = fields.Integer(string='Porcentaje', tracking=True)
    valor_monto_fijo = fields.Float(string='Valor monto fijo ($)', tracking=True)

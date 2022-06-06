# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductividadVariable(models.Model):
    _name = 'hu_productividad.variable'
    _description = 'Productividad - Variable'

    name = fields.Char(string='Código', required=True)
    descripcion = fields.Char(string='Descripción')
    active = fields.Boolean(string='Activo', default=True)


class ProductividadVariablePunto(models.Model):
    _name = 'hu_productividad.variable_punto'
    _description = 'Productividad - Variable (punto)'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo', default=True)


class ProductividadMetodoCalculoVariable(models.Model):
    _name = 'hu_productividad.metodo_calculo_variable'
    _description = 'Productividad - Variable de método de cálculo'

    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    variable_id = fields.Many2one('hu_productividad.variable', string='Variable')
    forma_calculo = fields.Selection([
        ('puntaje', 'Por puntaje'),
        ('porcentaje_facturado', '% facturado'),
        ('monto_fijo_cantidad', 'Monto fijo por cantidad'),
        ('monto_fijo', 'Monto fijo'),
        ('formula_vieja', 'Fórmula vieja'),
    ], string='Forma de Cálculo', required=True)

    # Según forma de cálculo
    base = fields.Integer(string='Base')
    punto = fields.Many2one('hu_productividad.variable_punto', string='Punto')
    valor_punto = fields.Float(string='Valor punto')

    porcentaje = fields.Integer(string='porcentaje')

    # Monto fijo por cantidad
    valor_monto_fijo_cantidad = fields.Float(string='Valor $')

    # Monto fijo
    valor_monto_fijo = fields.Float(string='Valor $')

    # Fórmula vieja
    base_formula_vieja = fields.Integer(string='Base')
    punto_formula_vieja = fields.Many2one('hu_productividad.variable_punto', string='Punto')
    valor_punto_formula_vieja = fields.Float(string='Valor punto')


class ProductividadMetodoCalculo(models.Model):
    _name = 'hu_productividad.metodo_calculo'
    _description = 'Productividad - Método de cálculo'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo', default=True)
    tipo = fields.Selection([
        ('generico', 'Genérico'),
        ('personalizado', 'Personalizado')
    ], string='Tipo', required=True)
    variable_ids = fields.One2many('hu_productividad.metodo_calculo_variable', 'metodo_calculo_id')


class ProductividadTipoPunto(models.Model):
    _name = 'hu_productividad.tipo_punto'
    _description = 'Productividad - Tipo de punto'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Descripción', required=True)
    valor = fields.Float(string='Valor $', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True)

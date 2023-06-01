# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductividadMetodoCalculo(models.Model):
    _name = 'hu_productividad.metodo_calculo'
    _description = 'Productividad - Método de cálculo'

    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo', default=True)
    tipo = fields.Selection([
        ('generico', 'Genérico'),
        ('personalizado', 'Personalizado')
    ], string='Tipo', required=True)
    metodo_calculo_variable_ids = fields.One2many('hu_productividad.metodo_calculo_variable', 'metodo_calculo_id')


class ProductividadMetodoCalculoVariable(models.Model):
    _name = 'hu_productividad.metodo_calculo_variable'
    _description = 'Productividad - Variable de método de cálculo'

    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    prestacion_id = fields.Many2one('hu_productividad.prestacion', string='Prestación') # @TODO esto debe ser un M2M
    forma_calculo = fields.Selection([
        ('puntaje', 'Por puntaje'),
        ('porcentaje_facturado', 'Porcentaje facturado'),
        ('monto_fijo_cantidad', 'Monto fijo por cantidad'),
        ('monto_fijo', 'Monto fijo'),
        ('formula_vieja', 'Fórmula vieja'),
    ], string='Forma de Cálculo', required=True)

    # Según forma de cálculo
    base = fields.Integer(string='Base')
    tipo_punto_id = fields.Many2one('hu_productividad.tipo_punto', string='Tipo de punto')
    valor_punto = fields.Float(string='Valor punto')
    porcentaje = fields.Integer(string='Porcentaje')
    valor_monto_fijo = fields.Float(string='Valor monto fijo ($)')

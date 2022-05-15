# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Productividad(models.Model):
    _name = 'hu_productividad.productividad'

    name = fields.Char(string='Periodo', compute='set_name_periodo')
    mes = fields.Integer(string='Mes')
    anio = fields.Integer(string='Año')
    monto_total_calculado = fields.Integer(string='Monto total calculado')
    estado = fields.Selection(selection=[('pendiente', 'Pendiente'), ('cobrado', 'Cobrado')], string='Estado')

    def set_name_periodo(self):
        for productividad in self:
            productividad.name = str(productividad.mes) + ' - ' + str(productividad.anio)


class ProductividadEmpleado(models.Model):
    _name = 'hu_productividad.empleado'

    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    empleado_id = fields.Many2one('hr.employee', string='Empleado')

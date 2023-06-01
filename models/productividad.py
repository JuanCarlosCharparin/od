# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Productividad(models.Model):
    _name = 'hu_productividad.productividad'
    _description = 'Productividad'

    name = fields.Char(string='Periodo', compute='set_name_periodo')
    mes = fields.Integer(string='Mes')
    anio = fields.Integer(string='Año')
    monto_total_calculado = fields.Integer(string='Monto total calculado')
    estado = fields.Selection(selection=[('pendiente', 'Pendiente'), ('cobrado', 'Cobrado')], string='Estado')

    def set_name_periodo(self):
        for productividad in self:
            productividad.name = str(productividad.mes) + ' - ' + str(productividad.anio)

# @TODO
# Crear clase que almacene la info leída de Alephoo y buscar la forma de que se vincule al profesional - LISTO
# Crear clase productividad_empleado donde se va a almacenar el calculo de productividad de cada empleado - LISTO (a completar con mas info cdo se realicen los calculos)
# Crear clase productividad_empleado_detalle donde se va a almacenar cada detalle de como se calculó la productividad de ese empleado
# Crear acción planificada que mensualmente cree la productividad


class ProductividadEmpleado(models.Model):
    _name = 'hu_productividad.productividad_empleado'
    _description = 'Productividad - Productividad empleado'


    productividad_id = fields.Many2one('hu_productividad.productividad', string='Productividad')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    practicas_realizadas = fields.Integer(string='Prácticas realizadas')
    importe = fields.Float(string='Importe')

    #Datos del método de calculo que serán persistidos
    forma_calculo = fields.Selection([
        ('puntaje', 'Por puntaje'),
        ('porcentaje_facturado', 'Porcentaje facturado'),
        ('monto_fijo_cantidad', 'Monto fijo por cantidad'),
        ('monto_fijo', 'Monto fijo'),
        ('formula_vieja', 'Fórmula vieja'),
    ], string='Forma de Cálculo')
    base = fields.Integer(string='Base')
    tipo_punto_id = fields.Many2one('hu_productividad.tipo_punto', string='Tipo de punto')
    valor_punto = fields.Float(string='Valor punto')
    porcentaje = fields.Integer(string='Porcentaje')
    valor_monto_fijo = fields.Float(string='Valor monto fijo ($)')

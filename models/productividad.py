# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime


class Productividad(models.Model):
    _name = 'hu_productividad.productividad'
    _description = 'Productividad'

    name = fields.Char(string='Periodo')
    mes = fields.Integer(string='Mes')
    anio = fields.Integer(string='Año')
    monto_total_calculado = fields.Integer(string='Monto total calculado')
    estado = fields.Selection(selection=[('pendiente', 'Pendiente'), ('cobrado', 'Cobrado')], string='Estado', default='pendiente')
    productividad_empleado_ids = fields.One2many('hu_productividad.productividad_empleado', 'productividad_id')

    #@TODO esto debe ser una accion planificada
    def generar_productividad_mensual(self, mes, anio, limite_empleados):
        if not mes or anio:
            mes = datetime.now().year
            anio = datetime.now().month

        productividad = self.buscar_o_crear_productividad(mes, anio)
        empleados = self.env['hr.employee'].get_empleados_a_calcular_productividad_mes_actual(limite=limite_empleados)
        for empleado in empleados:
            #Se contempla la posibilidad de que un empleado tenga más de un método de calculo por lo que se hace un bucle
            calculos_productividad_empleado = empleado.calcular_productividad(mes, anio)
            for calculo_pe in calculos_productividad_empleado:
                #@TODO completar creacion de productividad_empleado, productividad_empleado_detalle y prod_empleado_det_turno_alephoo
                self.env['hu_productividad.productividad_empleado'].create({
                    'productividad_id': productividad.id,
                    'employee_id': empleado.id,
                    'metodo_calculo_id': '',
                    'forma_calculo': '',
                    'base': '',
                    'tipo_punto_id': '',
                    'valor_punto': '',
                    'porcentaje': '',
                    'valor_monto_fijo': '',
                    'cantidad_practicas_realizadas': '',
                    'importe': '',
                    'productividad_empleado_detalle_ids': '',
                })

    def buscar_o_crear_productividad(self, mes, anio):
        productividad = self.search([
            ('mes', '=', mes),
            ('anio', '=', anio)
        ], limit=1)
        if not productividad:
            productividad = self.create({
                'name': str(anio) + ' - ' + str(mes),
                'anio': anio,
                'mes': mes,
            })

        return productividad


class ProductividadEmpleado(models.Model):
    _name = 'hu_productividad.productividad_empleado'
    _description = 'Productividad - Productividad empleado'


    productividad_id = fields.Many2one('hu_productividad.productividad', string='Productividad')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    importe = fields.Float(string='Importe')
    productividad_empleado_detalle_ids = fields.One2many('hu_productividad.productividad_empleado_detalle', 'productividad_empleado_id')


class ProductividadEmpleadoDetalle(models.Model):
    _name = 'hu_productividad.productividad_empleado_detalle'
    _description = 'Productividad - Productividad empleado detalle'

    productividad_empleado_id = fields.Many2one('hu_productividad.productividad_empleado', string='Productividad empleado')
    importe = fields.Float(string='Importe')
    cantidad_practicas_realizadas = fields.Integer(string='Cantidad de prácticas realizadas')
    metodo_calculo_variable_id = fields.Many2one('hu_productividad.metodo_calculo_variable', string='Variable de método de cálculo')

    #Datos de la variable de método de calculo que serán persistidos
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


class ProductividadEmpleadoDetalleTurnoAlephoo(models.Model):
    _name = 'hu_productividad.prod_empleado_det_turno_alephoo'
    _description = 'Productividad - Productividad empleado detalle - Turno alephoo'

    productividad_emp_detalle_id = fields.Many2one('hu_productividad.productividad_empleado_detalle', string='Productividad empleado detalle')
    turno_alephoo_id = fields.Many2one('hu_productividad.hu_productividad.turno_alephoo', string='Turno Alephoo')
    incluido = fields.Boolean(string='Incluído', help='Indica si el turno será incluído en el calculo de productividad. En caso de no estarlo, puede incluirse en futuros cálculos')

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
    importe_total = fields.Integer(string='Importe total calculado')
    estado = fields.Selection(selection=[('pendiente', 'Pendiente'), ('cobrado', 'Cobrado')], string='Estado', default='pendiente')
    productividad_empleado_ids = fields.One2many('hu_productividad.productividad_empleado', 'productividad_id')

    def generar_productividad_mensual(self, mes=False, anio=False, limite_empleados=10):
        if not (mes or anio):
            anio = datetime.now().year
            mes = datetime.now().month

        productividad = self.buscar_o_crear_productividad(mes, anio)
        empleados = self.env['hr.employee'].get_empleados_a_calcular_productividad(mes=mes, anio=anio, limite=limite_empleados)
        importe_total_productividad = productividad.importe_total
        for empleado in empleados:
            calculos_productividad_empleado = empleado.calcular_productividad(mes, anio)
            productividad_empleado = self.env['hu_productividad.productividad_empleado'].create({
                'productividad_id': productividad.id,
                'employee_id': empleado.id
            })
            importe_total_empleado = 0
            for calculo_pe in calculos_productividad_empleado:
                productividad_empleado_detalle =self.env['hu_productividad.productividad_empleado_detalle'].create({
                    'productividad_empleado_id': productividad_empleado.id,
                    'importe': calculo_pe.get('importe'),
                    'cantidad_practicas_realizadas': calculo_pe.get('cantidad_practicas_realizadas'),
                    'metodo_calculo_id': calculo_pe.get('metodo_calculo_id'),
                    'metodo_calculo_variable_id': calculo_pe.get('metodo_calculo_variable_id'),
                    'forma_calculo': calculo_pe.get('forma_calculo'),
                    'base': calculo_pe.get('base'),
                    'tipo_punto_id': calculo_pe.get('tipo_punto_id'),
                    'valor_punto': calculo_pe.get('valor_punto'),
                    'porcentaje': calculo_pe.get('porcentaje'),
                    'valor_monto_fijo': calculo_pe.get('valor_monto_fijo')
                })
                importe_total_empleado += calculo_pe.get('importe')

                #Crea los registros de prod_empleado_det_turno_alephoo (relación entre productividad_empleado_detalle y el turno)
                for turno_alephoo_id in calculo_pe.get('turno_alephoo_ids'):
                    self.env['hu_productividad.prod_empleado_det_turno_alephoo'].create({
                        'turno_alephoo_id': turno_alephoo_id,
                        'productividad_emp_detalle_id': productividad_empleado_detalle.id,
                        'incluido': True
                    })

            productividad_empleado.importe = importe_total_empleado
            importe_total_productividad += importe_total_empleado

        productividad.importe_total = importe_total_productividad

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
    importe = fields.Float(string='Importe')
    productividad_empleado_detalle_ids = fields.One2many('hu_productividad.productividad_empleado_detalle', 'productividad_empleado_id')


class ProductividadEmpleadoDetalle(models.Model):
    _name = 'hu_productividad.productividad_empleado_detalle'
    _description = 'Productividad - Productividad empleado detalle'

    productividad_empleado_id = fields.Many2one('hu_productividad.productividad_empleado', string='Productividad empleado')
    importe = fields.Float(string='Importe')
    cantidad_practicas_realizadas = fields.Integer(string='Cantidad de prácticas realizadas')
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo')
    metodo_calculo_variable_id = fields.Many2one('hu_productividad.metodo_calculo_variable', string='Variable de método de cálculo')
    prod_empleado_det_turno_alephoo_ids = fields.One2many('hu_productividad.prod_empleado_det_turno_alephoo', 'productividad_emp_detalle_id')

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

    #Campos relacionados
    met_calc_variable_prestacion_ids = fields.Many2many('hu_productividad.prestacion', related='metodo_calculo_variable_id.prestacion_ids', string='Prestaciones incluídas')
    productividad_empleado_employee_id = fields.Many2one('hr.employee', related='productividad_empleado_id.employee_id')


#Almacena la relación entre productividad_empleado_detalle y el turno alephoo
class ProductividadEmpleadoDetalleTurnoAlephoo(models.Model):
    _name = 'hu_productividad.prod_empleado_det_turno_alephoo'
    _description = 'Productividad - Productividad empleado detalle - Turno alephoo'

    productividad_emp_detalle_id = fields.Many2one('hu_productividad.productividad_empleado_detalle', string='Productividad empleado detalle')
    turno_alephoo_id = fields.Many2one('hu_productividad.turno_alephoo', string='Turno Alephoo')
    incluido = fields.Boolean(string='Incluído', default=True, help='Indica si el turno será incluído en el calculo de productividad. En caso de no estarlo, puede incluirse en futuros cálculos')

    #Campos relacionados de turno alephoo
    turno_alephoo_turno_id = fields.Integer(related='turno_alephoo_id.turno_id')
    turno_alephoo_fecha = fields.Date(related='turno_alephoo_id.fecha')
    turno_alephoo_hora = fields.Float(related='turno_alephoo_id.hora')
    turno_alephoo_estado = fields.Char(related='turno_alephoo_id.estado')
    turno_alephoo_paciente_nombre = fields.Char(related='turno_alephoo_id.paciente_nombre')
    turno_alephoo_paciente_dni = fields.Char(related='turno_alephoo_id.paciente_dni')
    turno_alephoo_prestacion_nombre = fields.Char(related='turno_alephoo_id.prestacion_nombre')
    turno_alephoo_prestacion_codigo = fields.Char(related='turno_alephoo_id.prestacion_codigo')
    turno_alephoo_prestacion_cantidad = fields.Integer(related='turno_alephoo_id.prestacion_cantidad')


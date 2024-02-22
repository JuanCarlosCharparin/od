# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class Productividad(models.Model):
    _name = 'hu_productividad.productividad'
    _description = 'Productividad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name DESC'

    name = fields.Char(string='Periodo')
    mes = fields.Integer(string='Mes')
    anio = fields.Integer(string='Año')
    importe_total = fields.Integer(string='Importe total calculado')
    estado = fields.Selection(selection=[
        ('en_calculo', 'En proceso de cálculo'),
        ('calculo_completo', 'Cálculo aut. completo'),
        ('ajustes_manuales', 'Ajustes manuales'),
        ('a_pagar', 'A pagar'),
        ('pagado', 'Pagado')
    ], string='Estado', default='en_calculo', tracking=True)
    productividad_empleado_ids = fields.One2many('hu_productividad.productividad_empleado', 'productividad_id')

    def write(self, vals):
        for rec in self:
            if rec.estado in ('a_pagar', 'pagado') and vals.get('importe_total') and vals.get('importe_total') != rec.importe_total:
                raise ValidationError('No se pueden hacer cambios en la productividad una vez que está en estado A pagar o Pagado')

        return super(Productividad, self).write(vals)

    #Acción planificada
    def generar_productividad_mensual(self, mes=False, anio=False, limite_empleados=10, empleado_ids=[]):
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        if not mes or not anio:
            mes = mes_actual
            anio = anio_actual

        if mes == mes_actual and anio == anio_actual:
            proxima_fecha_calculo_str = self.env["ir.config_parameter"].get_param("productividad_proxima_fecha_calculo", False)
            if not proxima_fecha_calculo_str:
                raise ValidationError('No es posible crear la productividad del mes actual ya que no está configurada la fecha de próximo cálculo.')
            proxima_fecha_calculo = datetime.strptime(proxima_fecha_calculo_str + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
            if datetime.now() <= proxima_fecha_calculo:
                raise ValidationError('No es posible crear la productividad del mes actual ya que la próxima fecha de inicio es el día ' + proxima_fecha_calculo_str)

        productividad = self.buscar_o_crear_productividad(mes, anio)

        if empleado_ids:
            empleados = self.env['hr.employee'].search([('id', 'in', empleado_ids)])
        else:
            empleados = self.env['hr.employee'].get_empleados_a_calcular_productividad(mes=mes, anio=anio, limite=limite_empleados)

        if not empleados and productividad.estado == 'en_calculo':
            productividad.estado = 'calculo_completo'
            return
        importe_total_productividad = productividad.importe_total
        for empleado in empleados:
            calculos_productividad_empleado = empleado.calcular_productividad(mes, anio)

            productividad_empleado = self.env['hu_productividad.productividad_empleado'].search([
                ('productividad_id', '=', productividad.id),
                ('employee_id', '=', empleado.id)
            ])
            if not productividad_empleado:
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
                    'horario': calculo_pe.get('horario'),
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

            if not empleado.no_incluir_en_importe_total_productividad:
                importe_total_productividad += importe_total_empleado

        productividad.importe_total = importe_total_productividad

    def buscar_o_crear_productividad(self, mes, anio):
        productividad = self.search([
            ('mes', '=', mes),
            ('anio', '=', anio)
        ], limit=1)
        if not productividad:
            productividad = self.create({
                'name': str(anio) + ' - ' + str(mes).zfill(2),
                'anio': anio,
                'mes': mes,
            })

        return productividad

    def recalcular_importe_total(self):
        importe_total = 0
        for productividad_empleado in self.productividad_empleado_ids:
            if not productividad_empleado.employee_id.no_incluir_en_importe_total_productividad:
                importe_total += productividad_empleado.importe
        self.importe_total = importe_total

    # Acción planificada
    def enviar_productividad_mensual_por_mail(self, mes=False, anio=False, limite=20, force_send=False, empleado_ids=[]):
        if not mes or not anio:
            mes = datetime.now().month
            anio = datetime.now().year

        productividad = self.buscar_o_crear_productividad(mes, anio)
        if productividad.estado in ('a_pagar', 'pagado'):
            if empleado_ids:
                criterio_busqueda = [
                    ('productividad_id', '=', productividad.id),
                    ('enviado', '=', False),
                    ('error_envio', '=', False),
                    ('importe', '>', 0),
                    ('employee_id', 'in', empleado_ids)
                ]
            else:
                criterio_busqueda = [
                    ('productividad_id', '=', productividad.id),
                    ('enviado', '=', False),
                    ('error_envio', '=', False),
                    ('importe', '>', 0)
                ]

            productividad_empleados_ids = self.env['hu_productividad.productividad_empleado'].search(criterio_busqueda, limit=limite)

            for productividad_empleado in productividad_empleados_ids:
                productividad_empleado.enviar_productividad_por_email(force_send)

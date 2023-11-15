from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class ProductividadEmpleado(models.Model):
    _name = 'hu_productividad.productividad_empleado'
    _description = 'Productividad - Productividad empleado'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'productividad_name DESC'


    productividad_id = fields.Many2one('hu_productividad.productividad', string='Productividad')
    employee_id = fields.Many2one('hr.employee', string='Empleado', tracking=True)
    importe = fields.Float(string='Importe', tracking=True)
    productividad_empleado_detalle_ids = fields.One2many('hu_productividad.productividad_empleado_detalle', 'productividad_empleado_id')
    enviado = fields.Boolean(string='Enviado por email')
    error_envio = fields.Boolean(string='Error de envío')
    detalle_error_envio = fields.Text(string='Detalle de error de envío')

    #Campos relaciones
    employee_job_id = fields.Many2one('hr.job', related='employee_id.job_id', store=True)
    productividad_name = fields.Char(related='productividad_id.name')
    productividad_estado = fields.Selection(related='productividad_id.estado')

    def recalcular_manualmente(self):
        for productividad_empleado_detalle in self.productividad_empleado_detalle_ids:
            productividad_empleado_detalle.recalcular_productividad_empleado_detalle()


    def recalcular_importe(self):
        importe = 0
        for productividad_empleado_detalle in self.productividad_empleado_detalle_ids:
            importe += productividad_empleado_detalle.importe
        self.importe = importe

    def enviar_productividad_por_email(self, force_send=False):
        if not self.enviado and not self.error_envio:
            try:
                template_id = self.env.ref('hu_productividad.template_envio_productividad')
                if not template_id:
                    raise ValidationError('Plantilla de email no encontrada: hu_productividad.template_envio_productividad')

                user_destinatario = self.employee_id.user_id
                if not user_destinatario:
                    raise ValidationError('Usuario relacionado al empleado no encontrado')

                if template_id and user_destinatario:
                    email_values = {
                        'email_from': 'Hospital Universitario <controldestock@hospital.uncu.edu.ar>',
                        'email_to': user_destinatario.email,
                        'auto_delete': False,
                        'scheduled_date': False,
                    }
                    template_id.send_mail(self.id, force_send=force_send, email_values=email_values)

                    self.enviado = True

            except Exception as e:
                self.error_envio = True
                self.detalle_error_envio = 'Error al enviar mail de productividad: ' + str(e)


class ProductividadEmpleadoDetalle(models.Model):
    _name = 'hu_productividad.productividad_empleado_detalle'
    _description = 'Productividad - Productividad empleado detalle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    productividad_empleado_id = fields.Many2one('hu_productividad.productividad_empleado', string='Productividad empleado')
    importe = fields.Float(string='Importe', tracking=True)
    cantidad_practicas_realizadas = fields.Integer(string='Cantidad de prácticas realizadas', tracking=True)
    metodo_calculo_id = fields.Many2one('hu_productividad.metodo_calculo', string='Método de Cálculo', tracking=True)
    horario = fields.Char(string='Horario', tracking=True)
    metodo_calculo_variable_id = fields.Many2one('hu_productividad.metodo_calculo_variable', string='Variable de método de cálculo', tracking=True)
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
    #@TODO Los campos relaciones met_calc_variable_prestacion_ids y met_calc_variable_agrup_prestaciones_ids deberían ser almacenados xq si se cambia en el método de calculo, también se cambia acá
    met_calc_variable_prestacion_ids = fields.Many2many('hu_productividad.prestacion', related='metodo_calculo_variable_id.prestacion_ids', string='Prestaciones incluídas')
    met_calc_variable_agrup_prestaciones_ids = fields.Many2many('hu_productividad.agrupador_prestaciones', related='metodo_calculo_variable_id.agrupador_prestaciones_ids', string='Agrupadores de prestaciones incluídos')
    productividad_empleado_employee_id = fields.Many2one('hr.employee', related='productividad_empleado_id.employee_id')

    #Permite recalcular el importe de productividad cuando se agregaron o quitaron prácticas manualmente o cuando se usa el botón "Recalcular"
    def recalcular_productividad_empleado_detalle(self):
        prod_empleado_det_turno_alephoo_incluidos = self.env['hu_productividad.prod_empleado_det_turno_alephoo'].search([
            ('productividad_emp_detalle_id', '=', self.id),
            ('incluido', '=', True)
        ])
        turnos_alephoo_ids = []
        for prod_empleado_det_turno_alephoo in prod_empleado_det_turno_alephoo_incluidos:
            turnos_alephoo_ids.append(prod_empleado_det_turno_alephoo.turno_alephoo_id.id)

        turnos_alephoo = self.env['hu_productividad.turno_alephoo'].search([('id', 'in', turnos_alephoo_ids)])

        cantidad_prestaciones = 0
        total_facturado = 0
        for turno_alephoo in turnos_alephoo:
            cantidad_prestaciones += turno_alephoo.prestacion_cantidad
            total_facturado += turno_alephoo.importe_total

        importe = 0
        if turnos_alephoo:
            # Calculo por puntaje: (Cantidad prestac de alephoo - Base) * Valor del punto) * Tipo_punto.valor
            if self.metodo_calculo_variable_id.forma_calculo == 'puntaje':
                importe = (cantidad_prestaciones - self.metodo_calculo_variable_id.base) * self.metodo_calculo_variable_id.valor_punto * self.metodo_calculo_variable_id.tipo_punto_id.valor

            # Calculo por porcentaje_facturado: (sumatoria del total de lo facturado por esa prestación) * %
            elif self.metodo_calculo_variable_id.forma_calculo == 'porcentaje_facturado':
                importe = total_facturado * self.metodo_calculo_variable_id.porcentaje / 100

            # Calculo por monto_fijo_cantidad: cantidad de turnos de esa prestación * monto fijo
            elif self.metodo_calculo_variable_id.forma_calculo == 'monto_fijo_cantidad':
                importe = cantidad_prestaciones * self.metodo_calculo_variable_id.valor_monto_fijo

            # Calculo por monto_fijo
            elif self.metodo_calculo_variable_id.forma_calculo == 'monto_fijo':
                importe = self.metodo_calculo_variable_id.valor_monto_fijo

            # Calculo por formula_vieja: ((Cantidad de prestac de alephoo  * valor del punto) - Base) * Tipo_punto.valor
            elif self.metodo_calculo_variable_id.forma_calculo == 'formula_vieja':
                importe = ((cantidad_prestaciones * self.metodo_calculo_variable_id.valor_punto) - self.metodo_calculo_variable_id.base) * self.metodo_calculo_variable_id.tipo_punto_id.valor

        self.importe = importe if importe > 0 else 0
        self.cantidad_practicas_realizadas = cantidad_prestaciones

        self.productividad_empleado_id.recalcular_importe()
        self.productividad_empleado_id.productividad_id.recalcular_importe_total()



#Almacena la relación entre productividad_empleado_detalle y el turno alephoo
class ProductividadEmpleadoDetalleTurnoAlephoo(models.Model):
    _name = 'hu_productividad.prod_empleado_det_turno_alephoo'
    _description = 'Productividad - Productividad empleado detalle - Turno alephoo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    productividad_emp_detalle_id = fields.Many2one('hu_productividad.productividad_empleado_detalle', string='Productividad empleado detalle')
    turno_alephoo_id = fields.Many2one('hu_productividad.turno_alephoo', string='Turno Alephoo', tracking=True)
    incluido = fields.Boolean(string='Incluído', default=True, help='Indica si el turno será incluído en el calculo de productividad. En caso de no estarlo, puede incluirse en futuros cálculos', tracking=True)
    active = fields.Boolean(string='Activo', default=True)

    #Campos relacionados de turno alephoo
    turno_alephoo_turno_id = fields.Integer(related='turno_alephoo_id.turno_id', store=True)
    turno_alephoo_fecha = fields.Date(related='turno_alephoo_id.fecha', store=True)
    turno_alephoo_hora = fields.Float(related='turno_alephoo_id.hora', store=True)
    turno_alephoo_estado = fields.Char(related='turno_alephoo_id.estado', store=True)
    turno_alephoo_paciente_nombre = fields.Char(related='turno_alephoo_id.paciente_nombre', store=True)
    turno_alephoo_paciente_dni = fields.Char(related='turno_alephoo_id.paciente_dni', store=True)
    turno_alephoo_prestacion_nombre = fields.Char(related='turno_alephoo_id.prestacion_nombre', store=True)
    turno_alephoo_prestacion_codigo = fields.Char(related='turno_alephoo_id.prestacion_codigo', store=True)
    turno_alephoo_prestacion_cantidad = fields.Integer(related='turno_alephoo_id.prestacion_cantidad', store=True)
    turno_alephoo_agregado_manualmente = fields.Boolean(related='turno_alephoo_id.agregado_manualmente', store=True)
    turno_alephoo_importe_total = fields.Float(related='turno_alephoo_id.importe_total', store=True)

    def incluir_item(self):
        if not self.incluido:
            self.incluido = True
            self.productividad_emp_detalle_id.recalcular_productividad_empleado_detalle()

    def excluir_item(self):
        if self.incluido:
            self.incluido = False
            self.productividad_emp_detalle_id.recalcular_productividad_empleado_detalle()

    def archivar_item(self):
        if not self.incluido:
            self.active = False

class CrearProdEmpleadoDetalleTurnoAlephoo(models.TransientModel):
    _name = 'hu_productividad.crear_prod_empleado_det_turno_alephoo'
    _description = 'Productividad - Crear Productividad empleado detalle - Turno alephoo'

    fecha = fields.Date(string='Fecha')
    hora = fields.Float(string='Hora')
    paciente_nombre = fields.Char(string='Nombre paciente')
    paciente_dni = fields.Char(string='DNI')
    prestacion_codigo = fields.Char(string='Código prestación', required=True)
    prestacion_cantidad = fields.Integer(string='Cantidad prestación', required=True)
    importe_total = fields.Float(string='Importe total prestación', required=True)

    def guardar_y_cerrar(self):
        if self.prestacion_cantidad <= 0:
            raise ValidationError('La cantidad de prestación realizada debe ser mayor a cero.')

        productividad_emp_detalle = self.env['hu_productividad.productividad_empleado_detalle'].search([('id', '=', self._context.get('active_id'))])
        if productividad_emp_detalle:
            #Crea Turno alepho
            turno_alephoo = self.env['hu_productividad.turno_alephoo'].create({
                'fecha': self.fecha,
                'hora': self.hora,
                'paciente_nombre': self.paciente_nombre,
                'paciente_dni': self.paciente_dni,
                'prestacion_codigo': self.prestacion_codigo,
                'prestacion_cantidad': self.prestacion_cantidad,
                'importe_total': self.importe_total,
                'agregado_manualmente': True
            })

            #Crea Prorecductividad empleado detalle - Turno alephoo
            self.env['hu_productividad.prod_empleado_det_turno_alephoo'].create({
                'productividad_emp_detalle_id': productividad_emp_detalle.id,
                'turno_alephoo_id': turno_alephoo.id,
                'incluido': True
            })

            productividad_emp_detalle.recalcular_productividad_empleado_detalle()

        return {'type': 'ir.actions.act_window_close'}

    # @api.model
    # def create(self, vals):
    #     rec = super(CrearProdEmpleadoDetalleTurnoAlephoo, self).create(vals)
    #
    #
    #
    #     return rec

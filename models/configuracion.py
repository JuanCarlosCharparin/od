# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class ProductividadPrestacion(models.Model):
    _name = 'hu_productividad.prestacion'
    _description = 'Productividad - Prestación'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, tracking=True)
    codigo = fields.Char(string='Código', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True, tracking=True)
    agrupador_prestaciones_id = fields.Many2one('hu_productividad.agrupador_prestaciones', string='Agrupador')
    es_receta = fields.Boolean(string='Es receta', help='Cuando está en true, al calcular productividad busca no solo por el código del turno sino también por especialidad RECETAS MEDICAS')

    def name_get(self):
        res = []
        for field in self:
            name = field.codigo + ' ' + str(field.name)
            res.append((field.id, name))
        return res

    # Cambia el método de busqueda para que también busque por codigo
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', 'ilike', name), ('codigo', 'ilike', name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class ProductividadAgrupadorPrestaciones(models.Model):
    _name = 'hu_productividad.agrupador_prestaciones'
    _description = 'Productividad - Agrupador de prestaciones'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True, tracking=True)
    prestacion_ids = fields.One2many('hu_productividad.prestacion', 'agrupador_prestaciones_id')


class ProductividadTipoPunto(models.Model):
    _name = 'hu_productividad.tipo_punto'
    _description = 'Productividad - Tipo de punto'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Descripción', required=True, tracking=True)
    valor = fields.Float(string='Valor $', required=True, tracking=True)
    active = fields.Boolean(string='Activo', default=True, tracking=True)

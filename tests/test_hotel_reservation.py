from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestHotelReservation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Chart guard: guarantee a sale journal + accounts on any DB
        company = cls.env.company
        if not cls.env['account.journal'].search(
                [('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1):
            cls.env['account.chart.template'].try_loading(
                'generic_coa', company, install_demo=False)

        cls.property = cls.env['hotel.property'].create({'name': 'Test Property'})
        cls.env.user.property_id = cls.property
        cls.room = cls.env['hotel.room'].create({
            'room_number': 'T101', 'room_type': 'double', 'price': 100.0,
            'property_id': cls.property.id, 'employee_name': cls.env.user.id,
        })
        cls.guest = cls.env['hotel.guest'].create({
            'name': 'Test Guest', 'id_number': 'IDTEST01',
        })
        cls.today = fields.Date.today()

    def _make_reservation(self, **kw):
        vals = {
            'guest_id': self.guest.id, 'room_id': self.room.id,
            'check_in': self.today, 'check_out': self.today + timedelta(days=2),
            'adults': 1,
        }
        vals.update(kw)
        return self.env['hotel.reservation'].create(vals)

    def test_workflow(self):
        r = self._make_reservation()
        self.assertEqual(r.state, 'draft')
        self.assertEqual(r.room_total, 200.0)
        r.action_confirm()
        self.assertEqual(r.state, 'confirmed')
        r.action_check_in()
        self.assertEqual(r.state, 'checked_in')
        self.assertEqual(self.room.status, 'occupied')

    def test_folio_payment_checkout(self):
        r = self._make_reservation()
        r.action_confirm(); r.action_check_in()
        self.env['hotel.folio.line'].create({
            'reservation_id': r.id, 'name': 'Minibar', 'quantity': 2, 'unit_price': 5.0})
        self.env['hotel.payment'].create({
            'reservation_id': r.id, 'amount': 210.0, 'method': 'cash'}).action_confirm()
        self.assertEqual(r.balance, 0.0)
        r.action_check_out()
        self.assertEqual(r.state, 'checked_out')
        self.assertEqual(self.room.status, 'needs_cleaning')
        self.assertTrue(r.invoice_id)
        self.assertTrue(all(r.folio_line_ids.mapped('is_paid')))

    def test_report_render(self):
        r = self._make_reservation()
        report = self.env.ref('hotel_management.action_report_hotel_folio')
        pdf, _ = report._render_qweb_pdf('hotel_management.report_hotel_folio', res_ids=[r.id])
        self.assertTrue(pdf)

    def test_double_booking(self):
        self._make_reservation()
        with self.assertRaises(ValidationError):
            self._make_reservation()

    def test_capacity(self):
        with self.assertRaises(ValidationError):
            self._make_reservation(adults=3)

    def test_blacklist(self):
        self.guest.blacklisted = True
        with self.assertRaises(ValidationError):
            self._make_reservation()

    def test_checkout_blocked_when_balance(self):
        r = self._make_reservation()
        r.action_confirm(); r.action_check_in()
        with self.assertRaises(UserError):
            r.action_check_out()

    def test_cron_no_show(self):
        r = self._make_reservation(
            check_in=self.today - timedelta(days=2),
            check_out=self.today - timedelta(days=1))
        r.action_confirm()
        self.env['hotel.reservation']._cron_check_no_show()
        self.assertEqual(r.state, 'no_show')
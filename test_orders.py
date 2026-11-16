from django.contrib.auth import get_user_model
from procurement.models import Supplier, MaterialRequest, ProcurementOrder, ProcurementOrderItem
from warehouse.models import Material, Warehouse

User = get_user_model()

def m(code):
    return Material.objects.get(code=code)

supply_user = User.objects.filter(username__startswith='supply').first()
if supply_user is None:
    supply_user = User.objects.filter(is_superuser=True).first()

supplier1 = Supplier.objects.get(name="СеверНефтеСнаб")
supplier2 = Supplier.objects.get(name="ПриозёрскТехСервис")
central = Warehouse.objects.get(name="Центральный склад МТО")

req2 = MaterialRequest.objects.get(pk=2)

order1 = ProcurementOrder.objects.create(
    supplier=supplier1,
    warehouse=central,
    status='ordered',
    expected_delivery_date='2026-02-18',
    comment='Закупка под дефицит по заявке №2.',
    created_by=supply_user,
)

brg_item = req2.items.filter(material=m('BRG-6205')).first()
rmn_item = req2.items.filter(material=m('RMN-A45')).first()

ProcurementOrderItem.objects.create(
    order=order1,
    material=m('BRG-6205'),
    quantity=6,
    unit_price=850.00,
    request_item=brg_item,
)
ProcurementOrderItem.objects.create(
    order=order1,
    material=m('RMN-A45'),
    quantity=4,
    unit_price=1200.00,
    request_item=rmn_item,
)

order2 = ProcurementOrder.objects.create(
    supplier=supplier2,
    warehouse=central,
    status='draft',
    comment='Пополнение запаса фильтров.',
    created_by=supply_user,
)

ProcurementOrderItem.objects.create(
    order=order2,
    material=m('FLT-001'),
    quantity=20,
    unit_price=450.00,
)

print(f"Заказов: {ProcurementOrder.objects.count()}")
for o in ProcurementOrder.objects.all():
    print(f"  {o.order_number} | {o.supplier.name} | {o.status} | строк: {o.items.count()}")
print(f"Строк заказов всего: {ProcurementOrderItem.objects.count()}")
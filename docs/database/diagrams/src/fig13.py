from er import *

W, GAP = 430, 190
LX = 150; CX = LX + W + GAP; RX = CX + W + GAP

role = Table("Роль", "ROLE", [("PK", "role_id"), ("UK", "name")], CX, 0)
user = Table("Пользователь", "APP_USER", [
    ("PK", "user_id"), ("FK", "role_id"), ("UK", "login"), ("UK", "email"), ("", "password_hash"),
    ("", "full_name"), ("", "phone"), ("", "language"), ("", "status"), ("", "failed_login_count"),
    ("", "locked_until"), ("", "consent_accepted_at"), ("", "created_at"), ("", "updated_at")], CX, 0)
device = Table("Устройство", "USER_DEVICE", [
    ("PK", "device_id"), ("FK", "user_id"), ("", "platform"), ("UK", "push_token"),
    ("", "created_at"), ("", "last_seen_at")], RX, 0)
wallet = Table("Кошелёк", "WALLET", [
    ("PK", "wallet_id"), ("FK", "user_id"), ("FK", "asset_id"), ("UK", "address"),
    ("", "encrypted_private_key"), ("", "balance"), ("", "balance_updated_at"), ("", "created_at")], LX, 0)
asset = Table("Актив", "ASSET", [
    ("PK", "asset_id"), ("UK", "code"), ("", "name"), ("", "network"), ("", "contract_address"),
    ("", "decimals"), ("", "is_active")], LX, 0)
txn = Table("Транзакция", "WALLET_TRANSACTION", [
    ("PK", "transaction_id"), ("FK", "wallet_id"), ("UK", "idempotency_key"), ("", "direction"),
    ("", "counterparty_address"), ("", "amount"), ("", "fee"), ("", "tx_hash"), ("", "status"),
    ("", "attempt_count"), ("", "error_message"), ("", "created_at"), ("", "confirmed_at")], LX, 0)
notif = Table("Уведомление", "NOTIFICATION", [
    ("PK", "notification_id"), ("FK", "user_id"), ("FK", "deal_id"), ("FK", "transaction_id"),
    ("", "type"), ("", "message"), ("", "is_read"), ("", "created_at")], RX, 0)
audit = Table("Событие журнала", "AUDIT_LOG", [
    ("PK", "log_id"), ("FK", "user_id"), ("", "event_type"), ("", "details"),
    ("", "ip_address"), ("", "occurred_at")], RX, 0)
deal = Table("Сделка", "DEAL", [("PK", "deal_id")], RX, 0, stub=True, note="подробно на рисунке 14")

TOP, VG = 30, 64
wallet.y = device.y = TOP
user.y = TOP + ROW                       # user_id на одном уровне с wallet.user_id и device.user_id
asset.y = wallet.bottom + VG
txn.y = asset.bottom + VG
role.y = user.bottom + VG
notif.y = txn.y - 3 * ROW                # transaction_id напротив transaction_id
audit.y = (device.bottom + notif.y - audit.h) / 2
deal.y = notif.bottom + 70
assert role.bottom < txn.ry("transaction_id") - 30

uid = user.ry("user_id")
xb = user.right + 62          # шина от user_id вправо
x1 = CX - 72                  # канал ROLE → APP_USER
x0, x0i = LX - 125, LX - 72   # каналы слева от кошелька
xr = RX + W + 72              # канал справа от уведомления

links = [
    Link([(role.left, role.ry("role_id")), (x1, role.ry("role_id")), (x1, user.ry("role_id")), (user.left, user.ry("role_id"))]),
    Link([(user.left, uid), (wallet.right, wallet.ry("user_id"))]),
    Link([(xb, uid), (device.left, device.ry("user_id"))]),
    Link([(xb, audit.ry("user_id")), (audit.left, audit.ry("user_id"))], parent="zero_one"),
    Link([(xb, notif.ry("user_id")), (notif.left, notif.ry("user_id"))]),
    Link([(asset.left, asset.ry("asset_id")), (x0i, asset.ry("asset_id")), (x0i, wallet.ry("asset_id")), (wallet.left, wallet.ry("asset_id"))]),
    Link([(wallet.left, wallet.ry("wallet_id")), (x0, wallet.ry("wallet_id")), (x0, txn.ry("wallet_id")), (txn.left, txn.ry("wallet_id"))]),
    Link([(txn.right, txn.ry("transaction_id")), (notif.left, notif.ry("transaction_id"))], parent="zero_one"),
    Link([(deal.right, deal.ry("deal_id")), (xr, deal.ry("deal_id")), (xr, notif.ry("deal_id")), (notif.right, notif.ry("deal_id"))], parent="zero_one"),
]
bus = (f'<g stroke="{LINE}" stroke-width="{SW}" fill="none" stroke-linecap="square">'
       f'<polyline points="{user.right},{uid} {xb},{uid} {xb},{notif.ry("user_id")}"/></g>'
       + junction(xb, uid) + junction(xb, audit.ry("user_id")))

width = xr + 50
top = max(t.bottom for t in (txn, deal)) + 60
leg, lh = legend(30, top, width - 60, junction=True)
open("fig13.svg", "w").write(document(width, top + lh + 30, [role, user, device, wallet, asset, txn, notif, audit, deal], links, bus + leg))
print(width, top + lh + 30)

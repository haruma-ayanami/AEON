from er import *

WL, WC, WR, GAP = 400, 470, 430, 190
LX = 150; CX = LX + WL + GAP; RX = CX + WC + GAP

offer = Table("Объявление", "OFFER", [
    ("PK", "offer_id"), ("FK", "seller_id"), ("FK", "asset_id"), ("", "price"), ("", "fiat_currency"),
    ("", "min_amount"), ("", "max_amount"), ("", "available_amount"), ("", "status"),
    ("", "created_at"), ("", "updated_at")], CX, 0, WC)
user = Table("Пользователь", "APP_USER", [("PK", "user_id")], LX, 0, WL, stub=True, note="подробно на рисунке 13")
asset = Table("Актив", "ASSET", [("PK", "asset_id")], LX, 0, WL, stub=True, note="подробно на рисунке 13")
opm = Table("Способ оплаты объявления", "OFFER_PAYMENT_METHOD", [
    ("PK, FK", "offer_id"), ("PK, FK", "payment_method_id")], CX, 0, WC)
pm = Table("Способ оплаты", "PAYMENT_METHOD", [
    ("PK", "payment_method_id"), ("UK", "name"), ("", "is_active")], RX, 0, WR)
deal = Table("Сделка", "DEAL", [
    ("PK", "deal_id"), ("FK", "offer_id"), ("FK", "payment_method_id"), ("FK", "buyer_id"),
    ("", "amount"), ("", "price"), ("", "status"), ("", "created_at"), ("", "updated_at"),
    ("", "completed_at")], CX, 0, WC)

TOP, VG = 30, 80
offer.y = TOP
user.y = TOP + ROW                       # user_id напротив seller_id
asset.y = user.bottom + 60
opm.y = offer.bottom + VG
pm.y = opm.y + ROW                       # payment_method_id напротив payment_method_id
deal.y = opm.bottom + VG

x2 = CX - 72          # ASSET → OFFER
x5 = CX - 72          # OPM → DEAL (ниже, не пересекается с x2)
x6 = LX - 90          # APP_USER → DEAL (обход слева)
x3 = offer.right + 72 # OFFER → OPM
assert asset.ry("asset_id") < opm.y

opm_k = opm.y + HEAD + ROW               # граница строк составного ключа
deal_k = deal.y + HEAD + 2 * ROW
links = [
    Link([(user.right, user.ry("user_id")), (offer.left, offer.ry("seller_id"))]),
    Link([(asset.right, asset.ry("asset_id")), (x2, asset.ry("asset_id")), (x2, offer.ry("asset_id")), (offer.left, offer.ry("asset_id"))]),
    Link([(offer.right, offer.ry("offer_id")), (x3, offer.ry("offer_id")), (x3, opm.ry("offer_id")), (opm.right, opm.ry("offer_id"))], child="many"),
    Link([(pm.left, pm.ry("payment_method_id")), (opm.right, opm.ry("payment_method_id"))]),
    Link([(opm.left, opm_k), (x5, opm_k), (x5, deal_k), (deal.left, deal_k)],
         bracket_start=(opm.y + HEAD + 7, opm.y + HEAD + 2 * ROW - 7),
         bracket_end=(deal.y + HEAD + ROW + 7, deal.y + HEAD + 3 * ROW - 7)),
    Link([(user.left, user.ry("user_id")), (x6, user.ry("user_id")), (x6, deal.ry("buyer_id")), (deal.left, deal.ry("buyer_id"))]),
]

width = RX + WR + 40
top = deal.bottom + 60
leg, lh = legend(30, top, width - 60, composite=True)
open("fig14.svg", "w").write(document(width, top + lh + 30, [offer, user, asset, opm, pm, deal], links, leg))
print(width, top + lh + 30)

def get_fee_status(dues, credit_balance):
    if dues > 0:
        return "Due"
    if credit_balance > 0:
        return "Advance Credit"
    return "Fully Paid"

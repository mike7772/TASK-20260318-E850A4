def mask_phone(phone: str) -> str:
    if len(phone) < 5:
        return "*" * len(phone)
    return phone[:3] + "****" + phone[-2:]

def mask_phone_partial(phone: str) -> str:
    if len(phone) < 5:
        return "*" * len(phone)
    return phone[:2] + "****" + phone[-2:]


def mask_id_number(id_number: str) -> str:
    if len(id_number) < 6:
        return "*" * len(id_number)
    return id_number[:2] + "****" + id_number[-2:]


def mask_email(email: str) -> str:
    if "@" not in email:
        return "*" * len(email)
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        return "*" * len(name) + "@" + domain
    return name[:1] + "****" + name[-1:] + "@" + domain


def mask_email_partial(email: str) -> str:
    if "@" not in email:
        return "*" * len(email)
    name, domain = email.split("@", 1)
    if len(name) <= 4:
        return mask_email(email)
    return name[:2] + "****" + name[-2:] + "@" + domain

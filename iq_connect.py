from iqoptionapi.stable_api import IQ_Option
import time

def conectar_iq(email, senha, tipo_conta="PRACTICE"):
    Iq = IQ_Option(email, senha)
    Iq.connect()
    time.sleep(1)

    if Iq.check_connect():
        Iq.change_balance(tipo_conta)
        return Iq
    else:
        return None
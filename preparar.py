import csv
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet

BASE = Path(__file__).resolve().parent
CAMPOS = [
    'pedido_id', 'cliente_id', 'nombre_cliente',
    'correo', 'ciudad', 'importe', 'estado',
]
# Todos los clientes y pedidos son ficticios.
# Numero de cliente, ciudad, importe y estado por pedido.
PEDIDOS = [
    (1, 'Villahermosa', '1850.00', 'Confirmado'),
    (2, 'Merida', '950.50', 'Confirmado'),
    (3, 'Puebla', '1200.00', 'Cancelado'),
    (1, 'Villahermosa', '650.00', 'Confirmado'),
    (4, 'Merida', '1499.50', 'Confirmado'),
    (5, 'Puebla', '2100.00', 'Confirmado'),
    (6, 'Villahermosa', '800.00', 'Cancelado'),
    (7, 'Puebla', '400.00', 'Confirmado'),
    (8, 'Merida', '300.00', 'Confirmado'),
    (9, 'Villahermosa', '1750.00', 'Confirmado'),
    (10, 'Puebla', '550.00', 'Cancelado'),
    (11, 'Merida', '1250.00', 'Confirmado'),
]


def main():
    datos = BASE / 'datos'
    secretos = BASE / '.secrets'
    datos.mkdir(exist_ok=True)
    secretos.mkdir(exist_ok=True)
    entrada = datos / 'pedidos.csv'
    referencia = BASE / 'referencia.sha256'
    clave = secretos / 'fernet.key'
    # No reemplazar datos, clave o referencia en una repeticion.
    if any(p.exists() for p in (entrada, referencia, clave)):
        raise FileExistsError('Entorno existente; revisar antes de recrear')
    with entrada.open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for n, (cliente, ciudad, importe, estado) in enumerate(
                PEDIDOS, start=1001):
            escritor.writerow({
                'pedido_id': f'PED-{n}',
                'cliente_id': f'CLI-{cliente:03d}',
                'nombre_cliente': f'Cliente Prueba {cliente:03d}',
                'correo': f'cliente{cliente:03d}@example.com',
                'ciudad': ciudad,
                'importe': importe,
                'estado': estado,
            })
    # Alta de referencia sobre datos conocidos del instructor.
    referencia.write_text(
        hashlib.sha256(entrada.read_bytes()).hexdigest(),
        encoding='ascii')
    with clave.open('xb') as f:
        f.write(Fernet.generate_key())
    try:
        clave.chmod(0o600)
    except OSError:
        pass  # En Windows se requiere gestionar ACL aparte.
    print('Dataset, referencia y clave creados sin mostrarlos')


if __name__ == '__main__':
    main()

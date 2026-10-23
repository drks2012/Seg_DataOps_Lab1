import argparse
import csv
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from cryptography.fernet import Fernet

BASE = Path(__file__).resolve().parent
DATOS = BASE / 'datos'
SALIDAS = BASE / 'salidas'
PERMISOS = {
    'operador': {'ejecutar', 'recuperar'},
    'analista': {'resumen'},
    'auditor': {'evidencias'},
}
CAMPOS = [
    'pedido_id', 'cliente_id', 'nombre_cliente',
    'correo', 'ciudad', 'importe', 'estado',
]


def calcular_hash(ruta):
    # TODO 1: devolver el SHA-256 hexadecimal del archivo.

    raise NotImplementedError('TODO 1: calcular_hash')


def autorizar(rol, operacion):
    # TODO 2: usar PERMISOS; denegar roles desconocidos.
    # Sin permiso: lanzar PermissionError, sin datos personales.
    raise NotImplementedError('TODO 2: autorizar')


def cifrar(valor, fernet):
    # TODO 3: str -> UTF-8 -> encrypt -> texto ASCII.

    
    raise NotImplementedError('TODO 3: cifrar')


def descifrar(token, fernet):
    # TODO 4: texto ASCII -> decrypt -> texto UTF-8.
    raise NotImplementedError('TODO 4: descifrar')


def cargar_cifrador():
    clave = os.environ.get('DATAOPS_KEY')
    if not clave:
        raise ValueError('Falta DATAOPS_KEY en el entorno')
    return Fernet(clave.encode('ascii'))


def leer_pedidos(ruta):
    with Path(ruta).open(encoding='utf-8', newline='') as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != CAMPOS:
            raise ValueError('Columnas distintas del contrato')
        filas = list(lector)
    if not filas:
        raise ValueError('Dataset vacio')
    ids = [fila['pedido_id'] for fila in filas]
    if len(ids) != len(set(ids)):
        raise ValueError('Identificadores duplicados')
    for fila in filas:
        monto = Decimal(fila['importe'])
        if not monto.is_finite() or monto < 0:
            raise ValueError('Importe invalido')
        if fila['estado'] not in {'Confirmado', 'Cancelado'}:
            raise ValueError('Estado invalido')
    return filas


def verificar_integridad(entrada, referencia):
    esperado = Path(referencia).read_text().strip()
    actual = calcular_hash(entrada)
    if actual != esperado:
        raise ValueError('Integridad de entrada no valida')
    return actual


def escribir_csv(ruta, campos, filas):
    with Path(ruta).open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)


def ejecutar(rol, entrada, referencia, destino):
    autorizar(rol, 'ejecutar')
    hash_entrada = verificar_integridad(entrada, referencia)
    filas = leer_pedidos(entrada)
    fernet = cargar_cifrador()
    protegidas, totales = [], {}
    for fila in filas:
        copia = dict(fila)
        for campo in ('nombre_cliente', 'correo'):
            copia[campo] = cifrar(fila[campo], fernet)
        protegidas.append(copia)
        if fila['estado'] == 'Confirmado':
            ciudad = fila['ciudad']
            totales[ciudad] = (
                totales.get(ciudad, Decimal('0'))
                + Decimal(fila['importe'])
            )
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=False)
    detalle = destino / 'detalle_protegido.csv'
    resumen = destino / 'resumen.csv'
    escribir_csv(detalle, CAMPOS, protegidas)
    escribir_csv(resumen, ['ciudad', 'total_ventas'], [
        {'ciudad': ciudad, 'total_ventas': f'{total:.2f}'}
        for ciudad, total in sorted(totales.items())
    ])
    return {
        'hash_entrada': hash_entrada,
        'filas': len(filas),
        'detalle': detalle,
        'resumen': resumen,
    }


def consultar_resumen(rol, destino):
    autorizar(rol, 'resumen')
    ruta = Path(destino) / 'resumen.csv'
    return ruta.read_text(encoding='utf-8')


def recuperar_muestra(rol, destino):
    autorizar(rol, 'recuperar')
    ruta = Path(destino) / 'detalle_protegido.csv'
    fila = leer_pedidos(ruta)[0]
    fernet = cargar_cifrador()
    return {
        campo: descifrar(fila[campo], fernet)
        for campo in ('nombre_cliente', 'correo')
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('accion', choices=[
        'inspeccionar', 'ejecutar', 'resumen', 'recuperar',
    ])
    parser.add_argument('--rol', default='operador')
    parser.add_argument('--entrada', type=Path,
                        default=DATOS / 'pedidos.csv')
    parser.add_argument('--referencia', type=Path,
                        default=BASE / 'referencia.sha256')
    parser.add_argument('--destino', type=Path,
                        default=SALIDAS / 'lab1')
    args = parser.parse_args()
    try:
        if args.accion == 'inspeccionar':
            # Diagnostico previo con datos ficticios.
            print(json.dumps(leer_pedidos(args.entrada)[0],
                             ensure_ascii=False, indent=2))
        elif args.accion == 'ejecutar':
            r = ejecutar(args.rol, args.entrada,
                         args.referencia, args.destino)
            print(f"Proceso terminado: {r['filas']} filas")
        elif args.accion == 'resumen':
            print(consultar_resumen(args.rol, args.destino))
        else:
            print(json.dumps(recuperar_muestra(
                args.rol, args.destino), ensure_ascii=False))
    except NotImplementedError as exc:
        parser.exit(2, f'PENDIENTE: {exc}\n')
    except (PermissionError, ValueError, OSError) as exc:
        parser.exit(1, f'BLOQUEADO: {exc}\n')


if __name__ == '__main__':
    main()

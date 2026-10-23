"""Comprobaciones de 1A; no contiene la solucion de los TODO."""
import sys
import lab1


def main():
    fernet = lab1.cargar_cifrador()
    correo = "cliente001@example.com"
    token = lab1.cifrar(correo, fernet)
    recuperado = lab1.descifrar(token, fernet) == correo
    print(f"Recuperacion coincidente: {recuperado}")
    assert recuperado, "El dato recuperado no coincide"

    entrada = lab1.DATOS / "pedidos.csv"
    referencia = (lab1.BASE / "referencia.sha256").read_text().strip()
    original = lab1.calcular_hash(entrada) == referencia
    print(f"Original coincide con referencia: {original}")
    assert original, "Revisar el original; no recalcular la referencia"

    copia = lab1.DATOS / "pedidos_prueba_parte1.csv"
    contenido = entrada.read_bytes()
    alterado = contenido.replace(b"1850.00", b"1851.00", 1)
    assert alterado != contenido, "No se encontro el importe de prueba"
    copia.write_bytes(alterado)
    coincide = lab1.calcular_hash(copia) == referencia
    print(f"Copia alterada coincide con referencia: {coincide}")
    assert not coincide, "La alteracion no fue detectada"
    print("Laboratorio 1A verificado")


if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as exc:
        sys.exit(f"PENDIENTE: {exc}")
    except (AssertionError, ValueError, OSError) as exc:
        sys.exit(f"REVISAR: {exc}")

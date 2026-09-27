"""Funciones de estadística del Módulo 1, ahora como módulo reutilizable."""

from decimal import Decimal


def promedio(*valores: Decimal) -> Decimal:
    if not valores:
        raise ValueError("Se necesita al menos un valor.")
    return sum(valores, Decimal("0")) / len(valores)


def mediana(*valores: Decimal) -> Decimal:
    if not valores:
        raise ValueError("Se necesita al menos un valor.")
    ordenados = sorted(valores)
    mitad = len(ordenados) // 2
    if len(ordenados) % 2 == 0:
        return (ordenados[mitad - 1] + ordenados[mitad]) / 2
    return ordenados[mitad]


def estadisticas(*valores: Decimal) -> dict[str, Decimal]:
    return {
        "Mínimo": min(valores),
        "Máximo": max(valores),
        "Promedio": promedio(*valores),
        "Mediana": mediana(*valores),
    }

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que la información de pago se carga correctamente
"""

import json
from data_manager import load_data

def test_payment_info():
    """Prueba la carga de información de pago"""
    print("=== PRUEBA DE INFORMACIÓN DE PAGO ===")
    
    # Cargar datos usando data_manager
    print("\n1. Cargando datos con data_manager.load_data()...")
    data = load_data()
    
    # Verificar si existe payment_info
    if "payment_info" in data:
        print("✅ payment_info encontrado en los datos")
        print(f"📊 Número de métodos de pago: {len(data['payment_info'])}")
        
        print("\n💳 Métodos de pago disponibles:")
        for method, info in data["payment_info"].items():
            print(f"  • {method}: {info}")
    else:
        print("❌ payment_info NO encontrado en los datos")
    
    # Cargar directamente desde el archivo JSON
    print("\n2. Cargando datos directamente desde data.json...")
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            direct_data = json.load(f)
        
        if "payment_info" in direct_data:
            print("✅ payment_info encontrado en el archivo directo")
            print(f"📊 Número de métodos de pago: {len(direct_data['payment_info'])}")
            
            print("\n💳 Métodos de pago desde archivo directo:")
            for method, info in direct_data["payment_info"].items():
                print(f"  • {method}: {info}")
        else:
            print("❌ payment_info NO encontrado en el archivo directo")
            
    except Exception as e:
        print(f"❌ Error al cargar archivo directo: {e}")
    
    # Comparar ambos resultados
    print("\n3. Comparación de resultados...")
    if "payment_info" in data and "payment_info" in direct_data:
        if data["payment_info"] == direct_data["payment_info"]:
            print("✅ Los datos coinciden perfectamente")
        else:
            print("⚠️ Los datos NO coinciden")
            print("Diferencias encontradas:")
            for method in set(list(data["payment_info"].keys()) + list(direct_data["payment_info"].keys())):
                data_value = data["payment_info"].get(method, "[NO EXISTE]")
                direct_value = direct_data["payment_info"].get(method, "[NO EXISTE]")
                if data_value != direct_value:
                    print(f"  • {method}:")
                    print(f"    - data_manager: {data_value}")
                    print(f"    - archivo directo: {direct_value}")

if __name__ == "__main__":
    test_payment_info()
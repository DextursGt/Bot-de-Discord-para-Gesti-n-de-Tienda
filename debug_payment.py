import json
from data_manager import load_data

# Script para debuggear el problema del comando /pago
print("=== DEBUG: Información de Pago ===")

# Cargar datos usando data_manager
print("\n1. Cargando datos con data_manager.load_data():")
data = load_data()
payment_info = data.get("payment_info", {})

print(f"Número total de métodos de pago: {len(payment_info)}")
print("\nMétodos encontrados:")
for i, (method, info) in enumerate(payment_info.items(), 1):
    print(f"{i}. {method}: {info}")

# Cargar datos directamente del JSON
print("\n\n2. Cargando datos directamente del archivo JSON:")
try:
    with open("data.json", "r", encoding="utf-8") as f:
        direct_data = json.load(f)
    
    direct_payment_info = direct_data.get("payment_info", {})
    print(f"Número total de métodos de pago (directo): {len(direct_payment_info)}")
    print("\nMétodos encontrados (directo):")
    for i, (method, info) in enumerate(direct_payment_info.items(), 1):
        print(f"{i}. {method}: {info}")
        
except Exception as e:
    print(f"Error al cargar directamente: {e}")

# Verificar si hay diferencias
print("\n\n3. Comparación:")
if payment_info == direct_payment_info:
    print("✅ Los datos son idénticos")
else:
    print("❌ Los datos son diferentes")
    print("Diferencias:")
    for key in set(payment_info.keys()) | set(direct_payment_info.keys()):
        if key not in payment_info:
            print(f"  - Falta en data_manager: {key}")
        elif key not in direct_payment_info:
            print(f"  - Falta en JSON directo: {key}")
        elif payment_info[key] != direct_payment_info[key]:
            print(f"  - Diferente valor para {key}:")
            print(f"    data_manager: {payment_info[key]}")
            print(f"    JSON directo: {direct_payment_info[key]}")

print("\n=== FIN DEBUG ===")